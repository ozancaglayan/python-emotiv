# -*- coding: utf-8 -*-
# vim:set et ts=4 sw=4:
#
## Copyright (C) 2012 Ozan Çağlayan <ocaglayan@gsu.edu.tr>
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

from scipy.io import savemat
import numpy as np

import time

def check_packet_drops(seq_numbers):
    lost = []
    for seq in xrange(len(seq_numbers) - 1):
        cur = int(seq_numbers[seq])
        _next = int(seq_numbers[seq + 1])
        if ((cur + 1) % 128) != _next:
            lost.append((cur + 1) % 128)
    return lost

def get_level(raw_data, bits):
    """Returns signal level from raw_data frame."""
    level = 0
    for i in range(13, -1, -1):
        level <<= 1
        b, o = (bits[i] / 8) + 1, bits[i] % 8
        level |= (ord(raw_data[b]) >> o) & 1
    return level

def save_as_matlab(_buffer, channel_mask, filename=None, metadata=None):
    """Save as matlab data with optional metadata."""
    matlab_data = {"CTR": _buffer[:, 0]}

    nr_samples = _buffer[:, 0].size
    trial = np.zeros((1,), dtype=np.object)
    trial[0] = _buffer[:, 1:].astype(np.float64).T
    trial_time = np.zeros((1,), dtype=np.object)
    trial_time[0] = np.array(range(nr_samples)) / 128.0

    # save raw data as well
    matlab_data["raw"] = trial[0]

    # This structure can be read by fieldtrip functions directly
    fieldtrip_data = {"fsample"     : 128,
                      "label"       : np.array(channel_mask, dtype=np.object).reshape((len(channel_mask), 1)),
                      "trial"       : trial,
                      "time"        : trial_time,
                      "sampleinfo"  : np.array([1, nr_samples])}

    matlab_data["data"] = fieldtrip_data

    # Inject metadata if any
    if metadata:
        for key, value in metadata.items():
            matlab_data[key] = value

    # Put time of recording
    date_info = time.strftime("%d-%m-%Y_%H-%M-%S")
    matlab_data["date"] = date_info

    if not filename:
        if metadata and metadata.has_key("Initials"):
            filename = "emotiv-%s-%s.mat" % (metadata["Initials"], date_info)
        else:
            filename = "emotiv-%s.mat" % date_info

    savemat(filename, matlab_data, oned_as='row')
