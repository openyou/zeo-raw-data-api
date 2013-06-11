"""
Parser
------

This module parses data from the BaseCapture module and assembles them
into slices that encompass a range of data representative of
Zeo's current status.

There are two different callbacks. One for slice callbacks and one that
the module will pass events to.

"""

#System Libraries
from math import sqrt
import time

#Zeo Libraries
from Utility import *
    
class Parser:
    """
    Interprets the incoming Zeo data and encapsulates it into an easy to use dictionary.
    """
    def clearSlice(self):
        """Resets the current Slice"""
        self.Slice = {'ZeoTimestamp'  : None, # String %m/%d/%Y %H:%M:%S
                      'Version'       : None, # Integer value
                      'SQI'           : None, # Integer value (0-30)
                      'Impedance'     : None, # Integer value as read by the ADC
                                              # Unfortunately left raw/unitless due to
                                              # nonlinearity in the readings.
                      'Waveform'      : [],   # Array of signed ints
                      'FrequencyBins' : {},   # Dictionary of frequency bins which are relative to the 2-30hz power
                      'BadSignal'     : None, # Boolean
                      'SleepStage'    : None  # String
                     }
                     
    def __init__(self):
        """Creates a new parser object."""
        self.EventCallbacks = []
        self.SliceCallbacks = []
        self.WaveBuffer = [0]*128
        
        self.clearSlice()

    def addEventCallback(self, callback):
        """Add a function to call when an Event has occured."""
        self.EventCallbacks.append(callback)
        
    def addSliceCallback(self, callback):
        """Add a function to call when a Slice of data is completed."""
        self.SliceCallbacks.append(callback)

    def update(self, timestamp, timestamp_subsec, version, data):
        """
        Update the current Slice with new data from Zeo.
        This function is setup to be easily added to the 
        BaseLink's callbacks.
        """
        
        if version != 3:
            print 'Unsupport raw data output version: %i' % version
            return
            
        datatype = dataTypes[ord(data[0])]
        
        if datatype == 'Event':
            for callback in self.EventCallbacks:
                callback(time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(timestamp)), 
                            version, eventTypes[getUInt32(data[1:5])])#for some reason 5 long when did 1:
            
        elif datatype == 'SliceEnd':
            self.Slice['ZeoTimestamp'] = time.strftime('%m/%d/%Y %H:%M:%S', time.gmtime(timestamp))
            self.Slice['Version'] = version
            for callback in self.SliceCallbacks:
                callback(self.Slice)
            self.clearSlice()
            
        elif datatype == 'Waveform':
            wave = []
            for i in range(1,256,2):
                value = getInt16(data[i:i+2])# Raw value
                value = float(value*315)/0x8000    # convert to uV value FIX
                wave.append(value)
            
            filtered = filter60hz(self.WaveBuffer + wave)

            self.Slice[datatype] = filtered[90:218] # grab the valid middle as the current second
            self.WaveBuffer = wave # store this second for processing the next second
            
            # NOTE: it is possible to mess this up easily for the first second.
            # A second could be stored, headband docked, then undocked and it would 
            # use the old data as the previous second. This is considered ok since it 
            # will only be bad for the first portion of the first second of data.
            
        elif datatype == 'FrequencyBins':
            for bin in range(7):
                value = float(getUInt16(data[(bin*2+1):(bin*2+3)]))/0x8000
                self.Slice[datatype][frequencyBins[bin]] = value
                
        elif datatype == 'BadSignal':
            self.Slice[datatype] = (getUInt32(data[1:])>0)
            
        elif datatype == 'SleepStage':
            self.Slice[datatype] = sleepStages[getUInt32(data[1:])]
            
        elif datatype == 'Impedance':
            impedance = getUInt32(data[1:])
            impi = (impedance & 0x0000FFFF) - 0x8000 # In Phase Component
            impq = ((impedance & 0xFFFF0000) >> 16) - 0x8000 # Quadrature Component
            if not impi == 0x7FFF: # 32767 indicates the impedance is bad
                impSquared = (impi * impi) + (impq * impq)
                self.Slice[datatype] = sqrt(impSquared)
                
        elif datatype == 'SQI':
            self.Slice[datatype] = getUInt32(data[1:])

