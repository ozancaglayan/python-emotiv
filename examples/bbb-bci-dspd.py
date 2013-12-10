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
import socket

from emotiv import utils

import numpy as np
from scipy import signal, fftpack

SOCKET = "/tmp/bbb-bci-dspd.sock"
RECVSIZE = 4096 * 8

def process_eeg(data):
    print "Lost packets: ", utils.check_packet_drops(data[:, CTR])

    ch = signal.detrend(data[:, O2].T)
    time_step = 1/128.0
    sample_freq = fftpack.fftfreq(ch.size, d=time_step)
    pidxs = np.where(sample_freq > 0)
    freqs = sample_freq[pidxs]

    fft = fftpack.fft(ch)
    power = np.abs(fft)[pidxs]
    max_power_ind = power.argmax()
    max_args = power.argsort()[::-1][:5]
    print freqs[max_args], power[max_args]
    #print "Power\n-----------------------------\n"
    #print power
    #print "\n".join("%10s: \t%2.f" % (z[0],z[1]) for z in zip(freqs, power))

def main():
    try:
        os.unlink(SOCKET)
    except:
        pass

    server = socket.socket(socket.AF_UNIX)
    server.bind(SOCKET)
    server.listen(0)

    # Blocks to wait a new connection
    client, client_addr = server.accept()

    # Get experiment metadata (7 bytes)
    experiment = client.recv(7)
    metadata = dict((k,v) for k,v in zip(["Initials", "Age", "Sex"], experiment.split(",")))

    # Get experiment max duration (4 digits)
    duration = int(client.recv(4))

    # Get comma separated channel configuration (49 bytes max)
    # Expose them as global variables to use them as int indices
    channel_conf = client.recv(49)
    for i, ch in enumerate(channel_conf.strip().split(",")):
        globals()[ch] = i
    n_channels = i + 1

    globals()["channel_mask"] = channel_conf.strip().split(",")[1:]

    # Preliminary buffer to accumulate data
    data = np.empty((duration * 128, n_channels), dtype=np.uint16)

    try:
        for i in range(duration):
            # Blocks
            raw_bytes = client.recv(RECVSIZE)

            # We should receive 1 second of EEG data 128x15 matrix
            d = np.fromstring(raw_bytes, dtype=np.uint16).reshape((128, n_channels))

            # This is for accumulating
            data[i * 128:(i+1) * 128, :] = d

            # Process data
            #process_eeg(data[:(i+1)*128, :])
            process_eeg(d)

    except Exception, e:
        print e
        pass
    finally:
        # Pass the result back to acquisition daemon
        # TODO: client.send(...)
        server.close()
        os.unlink(SOCKET)
        utils.save_as_matlab(data, channel_mask, metadata=metadata)
        print "Total packet lost: %d/%d" % (len(utils.check_packet_drops(data[:, CTR])), data[:, CTR].size)

if __name__ == "__main__":
    sys.exit(main())
