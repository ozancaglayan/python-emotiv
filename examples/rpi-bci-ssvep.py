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
    # Setup pins
    GPIO.setmode(GPIO.BOARD)

    pool = []
    stimuli = {
                PIN_LEFT_ARM    :   7.5,
                PIN_RIGHT_ARM   :   10,
              }

    # Spawn processes
    for pin, frequency in stimuli.items():
        pool.append(Process(target=blinkLed, args=(pin, frequency)))

    for process in pool:
        process.daemon = True
        process.start()

    # Stop LED's
    for p in pool:
        os.kill(p.pid, signal.SIGSTOP)

    # Resume LED's
    for p in pool:
        os.kill(p.pid, signal.SIGSTOP)

    # Finish
    try:
        for process in pool:
            process.join()
    except KeyboardInterrupt, ke:
        GPIO.cleanup()

if __name__ == "__main__":
    sys.exit(main())
