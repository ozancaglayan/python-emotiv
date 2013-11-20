#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:set et ts=4 sw=4:
#
## Copyright (C) 2013 Ozan Çağlayan <ocaglayan@gsu.edu.tr>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.

## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import os
import sys
import time
import signal

import numpy as np

import Adafruit_BBIO.GPIO as GPIO

try:
    from emotiv import epoc
except ImportError:
    sys.path.insert(0, "..")
    from emotiv import epoc

def main():

    # Setup headset
    headset = epoc.EPOC()

    PIN_LEFT_ARM  = "P8_9"
    PIN_RIGHT_ARM = "P8_10"

    # Setup pins
    GPIO.setup(PIN_LEFT_ARM, GPIO.OUT)
    GPIO.setup(PIN_RIGHT_ARM, GPIO.OUT)

    p1 = 1 / (18 * 2.0) # 18Hz
    p2 = 1 / (10 * 2.0) # 10Hz

    led1 = 0
    led2 = 0

    # Experiment duration
    duration = 4
    try:
        duration = int(sys.argv[1])
    except:
        pass

    # Resting EEG
    # eeg_rest = headset.acquire_data(duration)

    total_samples = duration * headset.sampling_rate
    ctr = 0
    _buffer = np.ndarray((total_samples, len(headset.channel_mask) + 1))

    GPIO.output(PIN_LEFT_ARM, led1)
    prev1 = prev2 = time.time()
    GPIO.output(PIN_RIGHT_ARM, led2)

    while ctr < total_samples:
        tic = time.time()
        if prev1 + p1 <= tic:
            led1 ^= 1
            GPIO.output(PIN_LEFT_ARM, led1)
            prev1 = time.time()
        if prev2 + p2 <= tic:
            led2 ^= 1
            GPIO.output(PIN_RIGHT_ARM, led2)
            prev2 = time.time()
        # Fetch new data
        data = headset.get_sample()
        if data:
            # Prepend sequence numbers
            _buffer[ctr] = np.insert(np.array(data), 0, headset.counter)
            ctr += 1

    print _buffer.T[0]

    # SSVEP EEG
    #eeg_ssvep = headset.acquire_data(duration)

    # Close devices
    try:
        headset.disconnect()
        GPIO.cleanup()
    except e:
        print e

    # Finally, save the data as matlab files
    #headset.save_as_matlab(eeg_ssvep, "eeg-ssvep", experiment)
    #headset.save_as_matlab(eeg_rest, "eeg-resting", experiment)

if __name__ == "__main__":
    sys.exit(main())
