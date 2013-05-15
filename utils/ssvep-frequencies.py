#!/usr/bin/env python

import os
import sys

import numpy as np

from scipy import fftpack
from scipy.io import loadmat
from matplotlib import pylab as plt

if __name__ == '__main__':
    if len(sys.argv) > 2:
        ch = sys.argv[2]
    else:
        ch = None

    try:
        folder = sys.argv[1]
        resting_sig = loadmat(os.path.join(folder, "eeg-resting"))
        ssvep_sig = loadmat(os.path.join(folder, "eeg-ssvep"))
    except IndexError, ie:
        print "Usage: %s <data-folder> [channel]" % sys.argv[0]

    else:
        time_step = 1/128.0
        sample_count = ssvep_sig['SEQ'].size
        sample_freq = fftpack.fftfreq(sample_count, d=time_step)
        pidxs = np.where(sample_freq > 0)
        freqs = sample_freq[pidxs]

        if ch:
            fig, axarr = plt.subplots(4, 1, sharex=False)
            axarr = np.array(axarr).reshape((-1, 1))
            channels = [ch]
        else:
            # 3 for matlab meta data arrays, and 1 for SEQ
            fig, axarr = plt.subplots(4, len(ssvep_sig) - 4, sharex="col",
                    sharey="row")
            print axarr
            channels = [c for c in ssvep_sig.keys() if not c.startswith(("__",
                "SEQ"))]

        for index, channel in enumerate(channels):
            rest = resting_sig[channel][0,:]
            ssvep = ssvep_sig[channel][0,:]
            diff_signal = ssvep - rest

            rest_fft = fftpack.fft(rest)
            ssvep_fft = fftpack.fft(ssvep)
            diff_fft = fftpack.fft(diff_signal)

            # Find powers
            rest_power = np.abs(rest_fft)[pidxs]
            ssvep_power = np.abs(ssvep_fft)[pidxs]
            sig_diff_power = np.abs(diff_fft)[pidxs]

            # Normalize
            rest_power = (rest_power / rest_power.max()) * 100
            ssvep_power = (ssvep_power / ssvep_power.max()) * 100
            sig_diff_power = (sig_diff_power / sig_diff_power.max()) * 100

            axarr[0, index].plot(freqs, rest_power)
            axarr[0, index].set_title("Resting(%s)" % channel)
            axarr[1, index].plot(freqs, ssvep_power)
            axarr[1, index].set_title("SSVEP(%s)" % channel)
            axarr[2, index].plot(freqs, ssvep_power - rest_power)
            axarr[2, index].set_title("Difference(%s)" % channel)
            axarr[3, index].plot(freqs, sig_diff_power)
            axarr[3, index].set_title("Signal Difference(%s)" % channel)

        plt.show()
