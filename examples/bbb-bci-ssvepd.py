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
import atexit

import Adafruit_BBIO.GPIO as GPIO

PID_FILE = "/var/run/bbb-ssvepd.pid"

# LED informations
LEDS = {"left"   :  {"pin": "P8_9",   "value": 0, "timer": time.time()},
        "right"  :  {"pin": "P8_10",  "value": 0, "timer": time.time()},
       }

ENABLED = 0

def cleanup():
    try:
        os.unlink(PID_FILE)
    except:
        pass
    for led in LEDS.values():
        GPIO.output(led["pin"], 0)
    GPIO.cleanup()

def sigusr1_handler(signum, stack):
    global ENABLED
    ENABLED ^= 1
    for led, led_info in LEDS.items():
        led_info["value"] = 0
        GPIO.output(led_info["pin"], led_info["value"])

    # If stimulation is turned off, block until another SIGUSR1
    if not ENABLED:
        signal.pause()

def write_pid_file():
    if os.path.exists(PID_FILE):
        return False
    with open(PID_FILE, "w") as fp:
        fp.write("%s" % os.getpid())
    return True

def toggle_led(which):
    led = LEDS[which]
    led["value"] ^= 1
    GPIO.output(led["pin"], led["value"])
    led["timer"] = time.time()

def main(freqs):
    if not write_pid_file():
        print "Failed writing PID file."
        return 1

    # Setup pins
    for i, led in enumerate(LEDS.values()):
        GPIO.setup(led["pin"], GPIO.OUT)
        GPIO.output(led["pin"], led["value"])
        led["period"] = 1 / (int(freqs[i]) * 2.0)

    # 80% of the minimum waiting period between steps
    min_period = min([led["period"] for led in LEDS.values()]) * 0.8

    # Register signal handlers
    signal.signal(signal.SIGUSR1, sigusr1_handler)

    try:
        while 1:
            if ENABLED:
                for led, led_info in LEDS.items():
                    if (time.time() - led_info["timer"]) >= led_info["period"]:
                        toggle_led(led)
                # Sleep for min_period for not hogging the CPU
                time.sleep(min_period)
    except KeyboardInterrupt, ke:
        return 2

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s [--start] <freq1> <freq2> ... <freqN>" % sys.argv[0]
        sys.exit(1)

    # Start stimulation immediately
    if sys.argv[1] == "--start":
        ENABLED = 1
        sys.argv.remove("--start")

    # Register cleanup handler
    atexit.register(cleanup)

    sys.exit(main(sys.argv[1:]))
