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

import sys
import time

import RPi.GPIO as GPIO

ON, OFF = range(2)

class LedStimulus(object):
    def __init__(self, _pin, _desc, _initial, _freq):
        self.pin = _pin
        self.desc = _desc
        self.current = _initial
        self.interval = 1.0 / (_freq * 2)
        self.lastTransition = 0.0

def main():
    stimuli = [
               LedStimulus(11, "Left Arm" , OFF, 5),
               LedStimulus(12, "Right Arm", OFF, 7),
              ]

    # Setup pins
    GPIO.setmode(GPIO.BOARD)
    for stimulus in stimuli:
        GPIO.setup(stimulus.pin, GPIO.OUT)

    try:
        while 1:
            for stimulus in stimuli:
                if time.time() >= stimulus.lastTransition + stimulus.interval:
                    # Event elapsed, change state
                    stimulus.current = (stimulus.current + 1) % 2
                    stimulus.lastTransition = time.time()
                    GPIO.output(stimulus.pin, stimulus.current)
    except KeyboardInterrupt, ke:
        GPIO.cleanup()

if __name__ == "__main__":
    sys.exit(main())
