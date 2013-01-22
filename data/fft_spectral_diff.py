#!/usr/bin/env python

import sys

import numpy as np

from scipy import fftpack
from matplotlib import pylab as pl

def main():
    try:
        sig_idle = np.load(sys.argv[1])
        sig_busy = np.load(sys.argv[2])
    except IndexError, ie:
        print "Usage: %s <numpy data file>" % sys.argv[0]

    else:
        time_step = 1/128.0

        # 1second
        fft_idle = fftpack.fft(sig_idle[0, :128*2])
        fft_busy = fftpack.fft(sig_busy[0, :128*2])

        final_fft = fft_busy - fft_idle

        sample_freq = fftpack.fftfreq(256, d=time_step)
        pidxs = np.where(sample_freq > 0)
        freqs = sample_freq[pidxs]
        final_power = np.abs(final_fft)[pidxs]
        busy_power = np.abs(fft_busy)[pidxs]

        pl.figure()
        pl.plot(freqs, final_power)
        pl.plot(freqs, busy_power, 'r')
        pl.xlabel('Frequency [Hz]')
        pl.ylabel('plower')
        pl.axes().set_ylim(0, 2)
        #axes = pl.axes([0.3, 0.3, 0.5, 0.5])
        #pl.title('Peak frequency')
        #pl.plot(freqs[30:300], power[30:300])
        #pl.setp(axes, yticks=[])
        pl.show()

if __name__ == '__main__':
    main()


