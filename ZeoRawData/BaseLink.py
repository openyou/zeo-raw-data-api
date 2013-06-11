"""
BaseLink
--------

Listens to the data coming from the serial port connected to Zeo.

The serial port is set at baud 38400, no parity, one stop bit.
Data is sent Least Significant Byte first.

The serial protocol is: 
    * AncllLLTttsid
    
        * A  is a character starting the message
        * n  is the protocol "version", ie "4"
        * c  is a one byte checksum formed by summing the identifier byte and all the data bytes
        * ll is a two byte message length sent LSB first. This length includes the size of the data block plus the identifier.
        * LL is the inverse of ll sent for redundancy. If ll does not match ~LL, we can start looking for the start of the next block immediately, instead of reading some arbitrary number of bytes, based on a bad length.
        * T  is the lower 8 bits of Zeo's unix time.
        * tt is the 16-bit sub-second (runs through 0xFFFF in 1second), LSB first.
        * s  is an 8-bit sequence number.
        * i  is the datatype
        * d  is the array of binary data

The incoming data is cleaned up into packets containing a timestamp,
the raw data output version, and the associated data.

External code can be sent new data as it arrives by adding 
themselves to the callback list using the addCallBack function.
It is suggested, however, that external code use the ZeoParser to
organize the data into events and slices of data.

"""

#System Libraries
import threading
from serial import Serial

#Zeo Libraries
from Utility import *

class BaseLink(threading.Thread):
    """
    Runs on a seperate thread and handles the raw serial communications
    and parsing required to communicate with Zeo. Each time data is
    successfully received, it is sent out to all of the callbacks.
    """
    
    def __init__(self, port):
        """
        Create a new class with default serial port settings.
        Parameters:
        port - the name of the serialport to open
                i.e. COM1 or /dev/ttyUSB0
        """
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.terminateEvent = threading.Event()

        self.callbacks = []

        self.ser = Serial(port, 38400, timeout = 5)
        self.ser.flushInput()

    def addCallback(self, callback):
        """Add a callback that will be passed valid data."""
        self.callbacks.append(callback)

    def error(self, msg):
        """Function for error printing."""
        print('Capture error: %s' % msg)   

    def run(self):
        """Begins thread execution and raw serial parsing."""
        zeoTime = None
        version = None
        ring = '  '
        fatal_error_ring = '            '
        while not self.terminateEvent.isSet():
            if ring != 'A4':
                c = self.ser.read(1)
                if len(c) == 1:
                    ring = ring[1:] + c
                    fatal_error_ring = fatal_error_ring[1:] + c
                    if fatal_error_ring == 'FATAL_ERROR_':
                        print 'A fatal error has occured.'
                        self.terminateEvent.set()
                else:
                    self.error('Read timeout in sync.')
                    ring = '  '
                    self.ser.flushInput()
            else:

                ring = '  '

                raw = self.ser.read(1)
                if len(raw) != 1:
                    self.error('Failed to read checksum.')
                    continue

                cksum = ord(raw)

                raw = self.ser.read(2)
                if len(raw) != 2:
                    self.error('Failed to read length.')
                    continue

                datalen = getUInt16(raw)

                raw = self.ser.read(2)
                if len(raw) != 2:
                    self.error('Failed to read second length.')
                    continue

                datalen2 = getUInt16(raw) ^ 0xffff

                if datalen != datalen2:
                    self.error('Mismatched lengths.')
                    continue

                raw = self.ser.read(3)
                if len(raw) != 3:
                    self.error('Failed to read timestamp.')
                    continue
                timestamp_lowbyte = ord(raw[0])
                timestamp_subsec = getUInt16(raw[1:3])/65535.0
                timestamp = 0

                raw = self.ser.read(1)
                if len(raw) != 1:
                    self.error('Failed to read sequence number.')
                    continue

                seqnum = ord(raw)
                
                raw = self.ser.read(datalen)
                if len(raw) != datalen:
                    self.error('Failed to read data.')
                    continue

                data = raw

                if sum(map(ord, data)) % 256 != cksum:
                    self.error('bad checksum')
                    continue

                
                # Check the datatype is supported
                if dataTypes.keys().count(ord(data[0])) == 0:
                    self.error('Bad datatype 0x%02X.' % ord(data[0]))
                    continue
                    
                datatype = dataTypes[ord(data[0])]
                
                # Check if this packet is an RTC time or version number
                if datatype == 'ZeoTimestamp':
                    zeoTime = getUInt32(data[1:])
                    continue
                elif datatype == 'Version':
                    version = getUInt32(data[1:])
                    continue

                # Don't pass the timestamp or version data since we send that
                # information along with the other data
                if zeoTime == None or version == None:
                    continue

                # Construct the full timestamp from the most recently received RTC
                # value in seconds, and the lower 8 bits of the RTC value as of
                # when this object was sent.
                if (zeoTime & 0xff == timestamp_lowbyte):
                    timestamp = zeoTime
                elif ((zeoTime - 1) & 0xff == timestamp_lowbyte):
                    timestamp = zeoTime - 1
                elif ((zeoTime + 1) & 0xff == timestamp_lowbyte):
                    timestamp = zeoTime + 1
                else:
                    # Something doesn't line up. Maybe unit was reset.
                    timestamp = zeoTime
                
                for callback in self.callbacks:
                    callback(timestamp, timestamp_subsec, version, data)
        self.ser.close()

