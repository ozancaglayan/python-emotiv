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

# Multi-frequency SSVEP stimulator to use with Raspberry Pi GPIO
# Inspired by the code from:
#   http://playground.arduino.cc/Code/MultiBlink

import os
import sys
import time
import signal

from multiprocessing import Process

import RPi.GPIO as GPIO

isRunning = True

class LedStimulus(object):
    def __init__(self, _pin, _desc, _initial, _freq):
        self.pin = _pin
        self.desc = _desc
        self.current = _initial
        self.initial = _initial
        self.interval = 1.0 / (_freq * 2)
        self.lastTransition = 0.0

def ssvepThread():
    def sigusr1Handler(signum, frame):
        global isRunning
        isRunning = not isRunning

    def sigtermHandler(signum, frame):
        GPIO.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGUSR1, sigusr1Handler)
    signal.signal(signal.SIGTERM, sigtermHandler)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    stimuli = [
               LedStimulus(11, "Left Arm" , 0, 5),
               LedStimulus(12, "Right Arm", 0, 7),
              ]

    # Setup pins
    GPIO.setmode(GPIO.BOARD)
    for stimulus in stimuli:
        GPIO.setup(stimulus.pin, GPIO.OUT)

    while 1:
        if isRunning:
            for stimulus in stimuli:
                if time.time() >= stimulus.lastTransition + stimulus.interval:
                    # Event elapsed, change state
                    stimulus.current = (stimulus.current + 1) % 2
                    stimulus.lastTransition = time.time()
                    GPIO.output(stimulus.pin, stimulus.current)
        else:
            # Revert LEDs back to the initial OFF status
            for stimulus in stimuli:
                GPIO.output(stimulus.pin, GPIO.LOW)
                stimulus.lastTransition = 0.0
                stimulus.current = stimulus.initial

if __name__ == "__main__":
    ssvepProcess = Process(target=ssvepThread)
    ssvepProcess.daemon = True
    ssvepProcess.start()

    a = time.time()
    try:
        while 1:
            if time.time() - a > 4:
                a = time.time()
                os.kill(ssvepProcess.pid, signal.SIGUSR1)
    except KeyboardInterrupt, ke:
        ssvepProcess.terminate()
