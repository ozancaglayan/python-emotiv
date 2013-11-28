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

import Adafruit_BBIO.GPIO as GPIO

PID_FILE = "/var/run/bbb-ssvepd.pid"

PIN_LEFT_ARM  = "P8_9"
PIN_RIGHT_ARM = "P8_10"
LED_LEFT = 0
LED_RIGHT = 0
ENABLED = False

def sigusr1_handler(signum, stack):
    print "Received: ", signum
    ENABLED = not ENABLED
    LED_LEFT = LED_RIGHT = 0
    GPIO.output(PIN_LEFT_ARM, 0)
    GPIO.output(PIN_RIGHT_ARM, 0)

def write_pid_file():
    if os.path.exists(PID_FILE):
        return False
    open(PID_FILE, "w").write(os.getpid())
    return True

def main(f1, f2):
    if not write_pid_file():
        return 1

    # Setup pins
    GPIO.setup(PIN_LEFT_ARM, GPIO.OUT)
    GPIO.setup(PIN_RIGHT_ARM, GPIO.OUT)

    # Compute periods
    p1 = 1 / (f1 * 2.0) # f1 Hz
    p2 = 1 / (f2 * 2.0) # f2 Hz

    # Initial led states are off
    GPIO.output(PIN_LEFT_ARM, 0)
    GPIO.output(PIN_RIGHT_ARM, 0)

    # Register SIGUSR1 handler
    signal.signal(signal.SIGUSR1, sigusr1_handler)

    while 1:
        if enabled:
            GPIO.output(PIN_LEFT_ARM, LED_LEFT)
            GPIO.output(PIN_RIGHT_ARM, LED_RIGHT)
        else:
            signal.pause()

    # Close devices
    try:
        GPIO.output(PIN_LEFT_ARM, 0)
        GPIO.output(PIN_RIGHT_ARM, 0)
        GPIO.cleanup()
    except e:
        print e
    finally:
        os.unlink(PID_FILE)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s <freq1> <freq2>" % sys.argv[0]

    sys.exit(main(sys.argv[1], sys.argv[2]))
