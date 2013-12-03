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
from scipy import signal, fftpack

SOCKET = "/tmp/bbb-bci-dspd.sock"
RECVSIZE = 4096 * 8

CTR, F3, FC5, AF3, F7, T7, P7, O1, O2, P8, T8, F8, AF4, FC6, F4 = range(15)

def process_eeg(data):
    ch = signal.detrend(data[:, O2].T)
    time_step = 1/128.0
    sample_freq = fftpack.fftfreq(ch.size, d=time_step)
    pidxs = np.where(sample_freq > 0)
    freqs = sample_freq[pidxs]

    fft = fftpack.fft(ch)
    power = np.abs(fft)[pidxs]

def main():
    server = socket.socket(socket.AF_UNIX)
    server.bind(SOCKET)
    server.listen(0)

    # Blocks to wait a new connection
    client, client_addr = server.accept()

    # Get experiment max duration
    duration = int(client.recv(1))

    data = np.empty((duration * 128, 15), dtype=np.float64)

    try:
        for i in range(duration):
            # Blocks
            raw_bytes = client.recv(RECVSIZE)

            # We should receive 1 second of EEG data 128x15 matrix
            data[i*128:(i+1)*128, :] = np.fromstring(raw_bytes,
                    dtype=np.uint16).reshape((128, 15)).astype(np.float64)

            # Process data
            process_eeg(data[:(i+1)*128, :])

    except Exception, e:
        print e
        pass
    finally:
        # Pass the result back to acquisition daemon
        # TODO: client.send(...)
        server.close()
        os.unlink(SOCKET)

if __name__ == "__main__":
    sys.exit(main())
