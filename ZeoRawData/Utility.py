"""
Utility
-------

A collection of general purpose functions and datatypes.

"""

from struct import unpack

def getInt32(A):
    """Creates a signed 32bit integer from a 4 item array"""
    return unpack('<i', A)[0]

def getUInt32(A):
    """Creates an unsigned 32bit integer from a 4 item array"""
    return unpack('<I', A)[0]
    
def getInt16(A):
    """Creates a signed 16bit integer from a 2 item array"""
    return unpack('<h', A)[0]

def getUInt16(A):
    """Creates an unsigned 16bit integer from a 2 item array"""
    return unpack('<H', A)[0]
    
def filter60hz(A):
    """
    Filters out 60hz noise from a signal.
    In practice it is a sinc low pass filter with cutoff frequency of 50hz.
    """
    # Filter designed in matlab
    # Convolution math from http://www.phys.uu.nl/~haque/computing/WPark_recipes_in_python.html
    filter=[0.0056, 0.0190, 0.0113, -0.0106, 0.0029, 0.0041, 
    -0.0082, 0.0089, -0.0062, 0.0006, 0.0066, -0.0129,
    0.0157, -0.0127, 0.0035, 0.0102, -0.0244, 0.0336,
    -0.0323, 0.0168, 0.0136, -0.0555, 0.1020, -0.1446,
    0.1743, 0.8150, 0.1743, -0.1446, 0.1020, -0.0555,
    0.0136, 0.0168, -0.0323, 0.0336, -0.0244, 0.0102,
    0.0035, -0.0127, 0.0157, -0.0129, 0.0066, 0.0006,
    -0.0062, 0.0089, -0.0082, 0.0041, 0.0029, -0.0106,
    0.0113, 0.0190, 0.0056]
    #convolution
    P = len(A)
    Q = len(filter)
    N = P + Q - 1
    c = []
    for k in range(N):
        t = 0
        lower = max(0, k-(Q-1))
        upper = min(P-1, k)
        for i in range(lower, upper+1):
            t = t + A[i] * filter[k-i]
        c.append(t)
    return c

dataTypes = {0x00 : 'Event', 0x02 : 'SliceEnd', 0x03 : 'Version', 0x80 : 'Waveform',
                0x83 : 'FrequencyBins', 0x84 : 'SQI', 0x8A : 'ZeoTimestamp', 
                0x97 : 'Impedance', 0x9C : 'BadSignal', 0x9D : 'SleepStage'}
"""
A dictionary containing all types of data the base may send.

0x00 : 'Event'
    An event has occured

0x02 : 'SliceEnd'
    Marks the end of a slice of data

0x03 : 'Version'
    Version of the raw data output

0x80 : 'Waveform'
    Raw time domain brainwave

0x83 : 'FrequencyBins'
    Frequency bins derived from waveform

0x84 : 'SQI'
    Signal Quality Index of waveform (0-30)

0x8A : 'ZeoTimestamp'
    Timestamp from Zeo's RTC

0x97 : 'Impedance'
    Impedance across the headband

0x9C : 'BadSignal'
    Signal contains artifacts

0x9D : 'SleepStage'
    Current 30sec sleep stage
"""
       
eventTypes = {0x05 : 'NightStart', 0x07 : 'SleepOnset', 0x0E : 'HeadbandDocked',
                0x0F : 'HeadbandUnDocked', 0x10 : 'AlarmOff', 0x11 : 'AlarmSnooze', 
                0x13 : 'AlarmPlay', 0x15 : 'NightEnd', 0x24 : 'NewHeadband'}
"""
A dictionary containing all the types of event that may be fired.

0x05 : 'NightStart'
    User's night has begun

0x07 : 'SleepOnset'
    User is asleep

0x0E : 'HeadbandDocked'
    Headband returned to dock

0x0F : 'HeadbandUnDocked'
    Headband removed from dock

0x10 : 'AlarmOff'
    User turned off the alarm
    
0x11 : 'AlarmSnooze'
    User hit snooze

0x13 : 'AlarmPlay'
    Alarm is firing
    
0x15 : 'NightEnd'
    User's night has ended

0x24 : 'NewHeadband'
    A new headband ID has been read
"""

frequencyBins = {0x00 : '2-4', 0x01 : '4-8', 0x02 : '8-13', 0x03 : '13-18',
                 0x04 : '18-21', 0x05 : '11-14', 0x06 : '30-50'}
"""
A dictionary containing all of the frequency bins.

0x00 : '2-4'
    Delta

0x01 : '4-8'
    Theta

0x02 : '8-13'
    Alpha

0x03 : '13-18'
    Beta

0x04 : '18-21'
    Beta

0x05 : '11-14'
    Beta (sleep spindles)

0x06 : '30-50'
    Gamma
"""
                
sleepStages = {0x00 : 'Undefined', 0x01 : 'Awake', 0x02 : 'REM',
               0x03 : 'Light', 0x04 : 'Deep'}
"""
A dictionary containing the sleepstages output by the base.

0x00 : 'Undefined'
    Sleepstage unsure

0x01 : 'Awake'
    Awake

0x02 : 'REM'
    Rapid eye movement(possibly dreaming)

0x03 : 'Light'
    Light sleep

0x04 : 'Deep'
    Deep sleep
"""
             
