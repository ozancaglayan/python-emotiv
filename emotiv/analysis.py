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

import numpy as np
from scipy import fftpack
from scipy import signal

def fft(data):
    # Those can be precomputed for several data lengths
    time_step = 1/128.0

    sampling_freqs = fftpack.fftfreq(data.size, d=time_step)
    positive_freqs = np.where(sampling_freqs > 0)
    freqs = sampling_freqs[positive_freqs]

    # Here's the computation part
    power = np.abs(fftpack.fft(signal.detrend(data)))[positive_freqs]
    return freqs, power

