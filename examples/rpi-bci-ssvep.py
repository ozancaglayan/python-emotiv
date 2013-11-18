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

from multiprocessing import Process

import RPi.GPIO as GPIO

try:
    from emotiv import epoc
except ImportError:
    sys.path.insert(0, "..")
    from emotiv import epoc

PIN_LEFT_ARM  = 11
PIN_RIGHT_ARM = 12

def blinkLed(pin, frequency):
    def sigHandler(signum, frame):
        GPIO.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, sigHandler)
    signal.signal(signal.SIGTERM, sigHandler)

    interval = 1.0 / (2 * frequency)
    GPIO.setup(pin, GPIO.OUT)

    while 1:
        GPIO.output(pin, 0)
        time.sleep(interval)
        GPIO.output(pin, 1)
        time.sleep(interval)

def main():

    # Setup headset
    headset = epoc.EPOC(method="direct")
    headset.set_channel_mask(["O1", "O2"])

    # Setup pins
    GPIO.setmode(GPIO.BOARD)

    # Experiment duration
    duration = 4
    try:
        duration = int(sys.argv[1])
    except:
        pass

    # Process pool
    pool = []

    # Stimuli and experiment information
    stimuli = {
                PIN_LEFT_ARM    :   10.8,
                PIN_RIGHT_ARM   :   15,
              }

    experiment = {"SSVEP":      stimuli.values(),
                  "Duration":   duration,
                  "LED":        "Green",
                  "Subject":    "OC",
                  "Age":        28,
                  "Date":       time.strftime("%d-%h-%Y %H:%M"),
                 }

    # Spawn processes
    for pin, frequency in stimuli.items():
        if frequency > 0:
            process = Process(target=blinkLed, args=(pin, frequency))
            process.daemon = True
            pool.append(process)

    # Resting EEG
    eeg_rest = headset.acquire_data(duration)

    # Start flickering
    for process in pool:
        process.start()

    # SSVEP EEG
    eeg_ssvep = headset.acquire_data(duration)

    # Stop LED's
    for p in pool:
        p.terminate()

    # Close devices
    try:
        headset.disconnect()
        GPIO.cleanup()
    except e:
        print e

    # Finally, save the data as matlab files
    headset.save_as_matlab(eeg_ssvep, "eeg-ssvep", experiment)
    headset.save_as_matlab(eeg_rest, "eeg-resting", experiment)

if __name__ == "__main__":
    sys.exit(main())
