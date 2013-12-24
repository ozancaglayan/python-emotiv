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
import signal
import socket
import subprocess

DSPD_SOCK = "/tmp/bbb-bci-dspd.sock"
DATA_DIR = os.path.expanduser("~/BCIData")

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

def main(argv):
    # Create DATA_DIR if not available
    try:
        os.makedirs(DATA_DIR)
    except:
        pass

    # Experiment duration (default: 4)
    duration = None
    freq1 = freq2 = None

    # Parse cmdline args
    try:
        freq1 = argv[1]
        freq2 = argv[2]
        duration = int(argv[3])
    except:
        print "Usage: %s <frequency 1> <frequency 2> <duration>" % argv[0]
        sys.exit(1)

    # Spawn SSVEP process
    ssvepd = None
    dspd = None
    try:
        ssvepd = subprocess.Popen(["./bbb-bci-ssvepd.py", freq1, freq2])
        dspd = subprocess.Popen(["./bbb-bci-dspd.py"])
    except OSError, e:
        print "Error: Can't launch SSVEP/DSP subprocesses."
        sys.exit(2)

    # Open socket to DSP process
    try:
        sock = socket.socket(socket.AF_UNIX)
        sock.connect(DSPD_SOCK)
    except:
        print "Can't connect to DSP block."
        ssvepd.terminate()
        ssvepd.wait()
        dspd.terminate()
        dspd.wait()
        sys.exit(4)

    # Setup headset
    headset = epoc.EPOC(enable_gyro=False)
    headset.set_channel_mask(["O1", "O2", "P7", "P8"])

    # Experiment data (7 bytes)
    nb_trials = 10
    experiment = get_subject_information()
    sock.send("%7s" % experiment)

    # Send 4 bytes of data for duration
    sock.send("%4d" % duration)

    # Send comma separated list of enabled channels (49 bytes max.)
    channel_conf = "CTR," + ",".join(headset.channel_mask)
    sock.send("%49s" % channel_conf)

    # Repeat nb_trials time
    for i in range(nb_trials):
        # Acquire resting data
        rest_eeg = headset.acquire_data(4)

        # TODO: Ask a question maybe?

        # Start flickering
        ssvepd.send_signal(signal.SIGUSR1)

        # Acquire EEG data for duration seconds
        ssvep_eeg = headset.acquire_data(duration)

        # Stop flickering
        ssvepd.send_signal(signal.SIGUSR1)

        # Send the data to DSP block
        sock.sendall(ssvep_eeg.tostring())

    # Cleanup
    try:
        headset.disconnect()
        sock.close()
        ssvepd.terminate()
        ssvepd.wait()
        dspd.terminate()
        dspd.wait()
    except e:
        print e

if __name__ == "__main__":
    sys.exit(main(sys.argv))
