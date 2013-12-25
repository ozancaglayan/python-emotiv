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
import socket

import numpy as np

SSVEPD_PID = "/var/run/bbb-bci-ssvepd.pid"
DSPD_SOCK = "/tmp/bbb-bci-dspd.sock"

try:
    from emotiv import epoc, utils
except ImportError:
    sys.path.insert(0, "..")
    from emotiv import epoc, utils

def get_subject_information():
    initials = raw_input("Initials: ")
    age = raw_input("Age: ")
    sex = raw_input("Sex (M)ale / (F)emale: ")
    return ",".join([initials[:2], age[:2], sex[0]])

def main():

    try:
        ssvepd_pid = int(open(SSVEPD_PID, "r").read())
    except:
        print "SSVEP service is not running."
        return 1

    try:
        sock = socket.socket(socket.AF_UNIX)
        sock.connect(DSPD_SOCK)
    except:
        print "Can't connect to DSP block."
        return 1

    # Setup headset
    headset = epoc.EPOC(enable_gyro=False)
    headset.set_channel_mask(["O1", "O2", "P7", "P8"])

    # Experiment duration
    duration = 4
    try:
        duration = int(sys.argv[1])
    except:
        pass

    # Experiment data (7 bytes)
    experiment = get_subject_information()
    sock.send("%7s" % experiment)

    # Send 4 bytes of data for duration
    sock.send("%4d" % duration)

    # Send comma separated list of enabled channels (49 bytes max.)
    channel_conf = "CTR," + ",".join(headset.channel_mask)
    sock.send("%49s" % channel_conf)

    os.kill(ssvepd_pid, signal.SIGUSR1)
    for i in range(duration):
        # Fetch 1 second of data each time
        data = headset.acquire_data(1)

        # Send the data to DSP block
        sock.sendall(data.tostring())

    os.kill(ssvepd_pid, signal.SIGUSR1)

    # Close devices
    try:
        headset.disconnect()
        sock.close()
    except e:
        print e

if __name__ == "__main__":
    sys.exit(main())
