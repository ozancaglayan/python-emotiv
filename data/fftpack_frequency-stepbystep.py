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
        sig = sig[0, :1280]
        sig_fft = fftpack.fft(sig[:128])
        for i in xrange(1,10):
            n_sig = sig[128*i:128*(i+1)]
            sig_fft = (sig_fft + fftpack.fft(n_sig))

            #sig = sig[0, :128]
            #sig = sig - sig.mean()

            sample_freq = fftpack.fftfreq(128, d=time_step)
            pidxs = np.where(sample_freq > 0)
            freqs, power = sample_freq[pidxs], np.abs(sig_fft)[pidxs]
            freq = freqs[power.argmax()]

            pl.figure()
            pl.plot(freqs, power)
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


