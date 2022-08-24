#
# Copyright (C) 2018 Pico Technology Ltd. See LICENSE file for terms.
#
# PS4824 BLOCK MODE EXAMPLE
# This example opens a 4000a driver device, sets up two channels and a trigger then collects a block of data.
# This data is then plotted as mV against time in ns.

import sys
import ctypes
import numpy as np
from picosdk.ps4000a import ps4000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok
import picosdk.discover as dut
import csv

if len(sys.argv) != 2:
    print("Wrong number of arguments!")
    exit(1)

file_name = str(sys.argv[1])



# Create chandle and status ready for use
chandle = ctypes.c_int16()
status = {}



# Open 4000 series PicoScope
# Returns handle to chandle for use in future API functions
status["openunit"] = ps.ps4000aOpenUnit(ctypes.byref(chandle), None)

try:
    assert_pico_ok(status["openunit"])
except: # PicoNotOkError:
    powerStatus = status["openunit"]

    if powerStatus == 286:
        status["changePowerSource"] = ps.ps4000aChangePowerSource(chandle, powerStatus)
    elif powerStatus == 282:
        status["changePowerSource"] = ps.ps4000aChangePowerSource(chandle, powerStatus)
    else:
        raise

    assert_pico_ok(status["changePowerSource"])


#### Ranges
#  pico_d9_bnc_10mv = 0
#  pico_d9_bnc_20mv = 1
#  pico_d9_bnc_50mv = 2
#  pico_d9_bnc_100mv = 3
#  pico_d9_bnc_200mv = 4
#  pico_d9_bnc_500mv = 5
#  pico_d9_bnc_1v = 6
#  pico_d9_bnc_2v = 7
#  pico_d9_bnc_5v = 8
#  pico_d9_bnc_10v = 9
#  pico_d9_bnc_20v = 10
#  pico_d9_bnc_50v = 11
#  pico_d9_bnc_100v = 12
#  pico_d9_bnc_200v = 13

######  Set up channel A: Cluster #############
# handle = chandle
# channel = PS4000a_CHANNEL_A = 0
# enabled = 1
# coupling type = PS4000a_DC = 1
# range = PS4000a_2V = 7
# analogOffset = 0 V
chARange = 3
status["setChA"] = ps.ps4000aSetChannel(chandle, 0, 1, 1, chARange, 0)
assert_pico_ok(status["setChA"])

######  Set up channel B: Soc #############
# Set up channel B
# handle = chandle
# channel = PS4000a_CHANNEL_B = 1
# enabled = 1
# coupling type = PS4000a_DC = 1
# range = PS4000a_2V = 7
# analogOffset = 0 V
chBRange = 3
status["setChB"] = ps.ps4000aSetChannel(chandle, 1, 1, 1, chBRange, 0)
assert_pico_ok(status["setChB"])

######  Set up channel C: Trigger #############
# handle = chandle
# channel = PS4000a_CHANNEL_C = 2
# enabled = 1
# coupling type = PS4000a_DC = 1
# range = PS4000a_2V = 7
# analogOffset = 0 V
chCRange = 8 #5V 
status["setChC"] = ps.ps4000aSetChannel(chandle, 2, 1, 1, chCRange, 0)
assert_pico_ok(status["setChC"])

######  Set up channel D: Memory #############
# handle = chandle
# channel = PS4000a_CHANNEL_D = 3
# enabled = 1
# coupling type = PS4000a_DC = 1
# range = PS4000a_2V = 7
# analogOffset = 0 V
chDRange = 3
status["setChD"] = ps.ps4000aSetChannel(chandle, 3, 1, 1, chDRange, 0)
assert_pico_ok(status["setChD"])

# Set up single trigger
# handle = chandle
# enabled = 1
# source = PS4000a_CHANNEL_D = 3
# threshold = 1024 ADC counts
# direction = PS4000a_RISING = 2
# delay = 0 s
# auto Trigger = 1000 ms
status["trigger"] = ps.ps4000aSetSimpleTrigger(chandle, 1, 2, 1024, 2, 0, 0)
assert_pico_ok(status["trigger"])

# Set number of pre and post trigger samples to be collected
preTriggerSamples = 0
postTriggerSamples = 2000000
maxSamples = preTriggerSamples + postTriggerSamples

# Get timebase information
# handle = chandle
# timebase = 8 = timebase
# noSamples = maxSamples
# pointer to timeIntervalNanoseconds = ctypes.byref(timeIntervalns)
# pointer to maxSamples = ctypes.byref(returnedMaxSamples)
# segment index = 0
timebase = 52
timeIntervalns = ctypes.c_float()
returnedMaxSamples = ctypes.c_int32()
oversample = ctypes.c_int16(1)
status["getTimebase2"] = ps.ps4000aGetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
assert_pico_ok(status["getTimebase2"])

# Run block capture
# handle = chandle
# number of pre-trigger samples = preTriggerSamples
# number of post-trigger samples = PostTriggerSamples
# timebase = 3 = 80 ns = timebase (see Programmer's guide for mre information on timebases)
# time indisposed ms = None (not needed in the example)
# segment index = 0
# lpReady = None (using ps4000aIsReady rather than ps4000aBlockReady)
# pParameter = None
status["runBlock"] = ps.ps4000aRunBlock(chandle, preTriggerSamples, postTriggerSamples, timebase, None, 0, None, None)
assert_pico_ok(status["runBlock"])

# Check for data collection to finish using ps4000aIsReady
ready = ctypes.c_int16(0)
check = ctypes.c_int16(0)
while ready.value == check.value:
    status["isReady"] = ps.ps4000aIsReady(chandle, ctypes.byref(ready))

# Create buffers ready for assigning pointers for data collection
bufferAMax = (ctypes.c_int16 * maxSamples)()
bufferAMin = (ctypes.c_int16 * maxSamples)() # used for downsampling which isn't in the scope of this example
bufferBMax = (ctypes.c_int16 * maxSamples)()
bufferBMin = (ctypes.c_int16 * maxSamples)() # used for downsampling which isn't in the scope of this example
bufferCMax = (ctypes.c_int16 * maxSamples)()
bufferCMin = (ctypes.c_int16 * maxSamples)() # used for downsampling which isn't in the scope of this example
bufferDMax = (ctypes.c_int16 * maxSamples)()
bufferDMin = (ctypes.c_int16 * maxSamples)() # used for downsampling which isn't in the scope of this example

# Set data buffer location for data collection from channel A
# handle = chandle
# source = PS4000a_CHANNEL_A = 0
# pointer to buffer max = ctypes.byref(bufferAMax)
# pointer to buffer min = ctypes.byref(bufferAMin)
# buffer length = maxSamples
# segementIndex = 0
# mode = PS4000A_RATIO_MODE_NONE = 0
status["setDataBuffersA"] = ps.ps4000aSetDataBuffers(chandle, 0, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), maxSamples, 0 , 0)
assert_pico_ok(status["setDataBuffersA"])

# Set data buffer location for data collection from channel B
# handle = chandle
# source = PS4000a_CHANNEL_B = 1
# pointer to buffer max = ctypes.byref(bufferBMax)
# pointer to buffer min = ctypes.byref(bufferBMin)
# buffer length = maxSamples
# segementIndex = 0
# mode = PS4000A_RATIO_MODE_NONE = 0
status["setDataBuffersB"] = ps.ps4000aSetDataBuffers(chandle, 1, ctypes.byref(bufferBMax), ctypes.byref(bufferBMin), maxSamples, 0 , 0)
assert_pico_ok(status["setDataBuffersB"])

# Set data buffer location for data collection from channel C
# handle = chandle
# source = PS4000a_CHANNEL_C = 1
# pointer to buffer max = ctypes.byref(bufferCMax)
# pointer to buffer min = ctypes.byref(bufferCMin)
# buffer length = maxSamples
# segementIndex = 0
# mode = PS4000A_RATIO_MODE_NONE = 0
status["setDataBuffersC"] = ps.ps4000aSetDataBuffers(chandle, 2, ctypes.byref(bufferCMax), ctypes.byref(bufferCMin), maxSamples, 0 , 0)
assert_pico_ok(status["setDataBuffersC"])

# Set data buffer location for data collection from channel D
# handle = chandle
# source = PS4000a_CHANNEL_D = 3
# pointer to buffer max = ctypes.byref(bufferDMax)
# pointer to buffer min = ctypes.byref(bufferDMin)
# buffer length = maxSamples
# segementIndex = 0
# mode = PS4000A_RATIO_MODE_NONE = 0
status["setDataBuffersD"] = ps.ps4000aSetDataBuffers(chandle, 3, ctypes.byref(bufferDMax), ctypes.byref(bufferDMin), maxSamples, 0 , 0)
assert_pico_ok(status["setDataBuffersD"])


# create overflow loaction
overflow = ctypes.c_int16()
# create converted type maxSamples
cmaxSamples = ctypes.c_int32(maxSamples)

# Retried data from scope to buffers assigned above
# handle = chandle
# start index = 0
# pointer to number of samples = ctypes.byref(cmaxSamples)
# downsample ratio = 0
# downsample ratio mode = PS4000a_RATIO_MODE_NONE
# pointer to overflow = ctypes.byref(overflow))
status["getValues"] = ps.ps4000aGetValues(chandle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, ctypes.byref(overflow))
assert_pico_ok(status["getValues"])


# find maximum ADC count value
# handle = chandle
# pointer to value = ctypes.byref(maxADC)
maxADC = ctypes.c_int16(32767)


# convert ADC counts data to mV
adc2mVChAMax =  adc2mV(bufferAMax, chARange, maxADC)
adc2mVChBMax =  adc2mV(bufferBMax, chBRange, maxADC)
adc2mVChCMax =  adc2mV(bufferCMax, chCRange, maxADC)
adc2mVChDMax =  adc2mV(bufferDMax, chDRange, maxADC)

## detect the last point
last_point = postTriggerSamples
for i,item in enumerate(adc2mVChCMax[10:]):
    if item < 1000:
        last_point = i+10
        break
print("Last point is ", last_point, "\nTime duration is = ", (last_point*timeIntervalns.value)/(1000*1000) ,' msec')


# Compute Average
CH_A_Avg = np.average(adc2mVChAMax[:last_point])
CH_B_Avg = np.average(adc2mVChBMax[:last_point])
CH_D_Avg = np.average(adc2mVChDMax[:last_point])
n_Points = last_point
print("Avg values {} {} {} over {} points!".format(CH_A_Avg,CH_B_Avg,CH_D_Avg,n_Points))

with open(file_name+".csv", "w", newline='') as file:
    writer = csv.writer(file, delimiter=',')
#    writer.writerow(adc2mVChAMax[:last_point])
#    writer.writerow(adc2mVChBMax[:last_point])
#    writer.writerow(adc2mVChCMax[:last_point])
    writer.writerow(['CH_A_Avg',CH_A_Avg])
    writer.writerow(['CH_B_Avg',CH_B_Avg])
    writer.writerow(['CH_D_Avg',CH_D_Avg])
    writer.writerow(['n_Points',n_Points])

## Create time data
# time = np.linspace(0, (cmaxSamples.value) * timeIntervalns.value, cmaxSamples.value)
# # plot data from channel A and B
# plt.plot(time[:last_point], adc2mVChAMax[:last_point], label="Ch A")
# plt.plot(time[:last_point], adc2mVChBMax[:last_point], label="Ch B")
# plt.plot(time[:last_point], adc2mVChCMax[:last_point], label="Ch C")
# plt.plot(time[:last_point], adc2mVChDMax[:last_point], label="Ch D")
# plt.legend()
# plt.xlabel('Time (ns)')
# plt.ylabel('Voltage (mV)')
# plt.show()

# Stop the scope
# handle = chandle
status["stop"] = ps.ps4000aStop(chandle)
assert_pico_ok(status["stop"])


# Close unitDisconnect the scope
# handle = chandle
#status["close"] = ps.ps4000aCloseUnit(chandle)
#assert_pico_ok(status["close"])

#print("Closed")

# display status returns
print(status)
