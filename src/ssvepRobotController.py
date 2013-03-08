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

import os
import sys
import time

import numpy as np

from scipy import fftpack

# Enumerations for EEG channels (14 channels)
CH_F3, CH_FC5, CH_AF3, CH_F7, CH_T7,  CH_P7, CH_O1,\
CH_O2, CH_P8,  CH_T8,  CH_F8, CH_AF4, CH_FC6,CH_F4 = range(14)

from Emotiv import *

if __name__ == "__main__":

    emotiv = EmotivEPOC()

    print("Enumerating devices...")
    try:
        emotiv.enumerate()
    except EmotivEPOCNotFoundException, e:
        if emotiv.permissionProblem:
            print("Please make sure that device permissions are handled.")
        else:
            print("Please make sure that device permissions are handled or"\
                    " at least 1 Emotiv EPOC dongle is plugged.")
        sys.exit(1)

    for k,v in emotiv.devices.iteritems():
        print("Found dongle with S/N: %s" % k)

    emotiv.setupEncryption()

    try:
        while True:
            emotiv.acquireData(duration=duration)
    except KeyboardInterrupt, ke:
        emotiv.disconnect()
        sys.exit(1)
