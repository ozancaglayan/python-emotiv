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

import numpy as np

try:
    from emotiv import epoc, utils
except ImportError:
    sys.path.insert(0, "..")
    from emotiv import epoc, utils

def main():
    try:
        duration = int(sys.argv[1])
    except:
        print "Usage: %s <duration> [ch1,ch2,..,chN]" % sys.argv[0]
        return 1

    channels = None
    try:
        channels = sys.argv[2].split(",")
    except:
        pass

    # Setup headset
    headset = epoc.EPOC(enable_gyro=False)
    if channels:
        headset.set_channel_mask(channels)

    # Acquire
    idx, data = headset.acquire_data_fast(duration)

    print "Battery: %d %%" % headset.battery
    print "Contact qualities"
    print headset.quality

    utils.save_as_matlab(data, headset.channel_mask)

    try:
        headset.disconnect()
    except e:
        print e

if __name__ == "__main__":
    sys.exit(main())
