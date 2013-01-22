#!/usr/bin/env python

import sys

import numpy as np

from scipy import fftpack
from matplotlib import pylab as pl

def main():
    #sig = np.genfromtxt("ssvep-10Hz-7.5Hz.txt")
    try:
        sig = np.load(sys.argv[1])
    except IndexError, ie:
        print "Usage: %s <numpy data file>" % sys.argv[0]

    else:
        time_step = 1/128.0

        # 1second
        sig = sig[0, :sig.size]

        sample_freq = fftpack.fftfreq(sig.size, d=time_step)
        sig_fft = fftpack.fft(sig)
        pidxs = np.where(sample_freq > 0)
        freqs, power = sample_freq[pidxs], np.abs(sig_fft)[pidxs]
        freq = freqs[power.argmax()]

        step = sig.size/128
        pl.figure()
        pl.plot(freqs, power)
        pl.xlabel('Frequency [Hz]')
        pl.ylabel('plower')
        axes = pl.axes([0.3, 0.3, 0.5, 0.5])
        pl.title('Peak frequency')
        pl.plot(freqs[9*step:22*step], power[9*step:22*step])
        pl.setp(axes, yticks=[])
        pl.show()

if __name__ == '__main__':
    main()


