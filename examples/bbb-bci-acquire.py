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

try:
    from emotiv import epoc, utils
except ImportError:
    sys.path.insert(0, "..")
    from emotiv import epoc, utils

def main():

    # Setup headset
    headset = epoc.EPOC()

    try:
        ssvepd_pid = int(open("/var/run/bbb-ssvepd.pid", "r").read())
    except:
        print "SSVEP service is not running."
        return 1

    # Experiment duration
    duration = 4
    try:
        duration = int(sys.argv[1])
    except:
        pass

    total_samples = duration * headset.sampling_rate
    ctr = 0
    _buffer = np.ndarray((total_samples, len(headset.channel_mask) + 1))

    os.kill(ssvepd_pid, signal.SIGUSR1)
    while ctr < total_samples:
        # Fetch new data
        data = headset.get_sample()
        if data:
            # Prepend sequence numbers
            _buffer[ctr] = np.insert(np.array(data), 0, headset.counter)
            ctr += 1

    os.kill(ssvepd_pid, signal.SIGUSR1)
    print utils.check_packet_drops(_buffer.T[0].tolist())

    # Close devices
    try:
        headset.disconnect()
    except e:
        print e

    # Finally, save the data as matlab files
    #headset.save_as_matlab(eeg_ssvep, "eeg-ssvep", experiment)
    #headset.save_as_matlab(eeg_rest, "eeg-resting", experiment)

if __name__ == "__main__":
    sys.exit(main())
