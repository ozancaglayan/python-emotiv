#!/usr/bin/env python

import os
import sys

import numpy as np

from scipy import fftpack, signal
from scipy.io import loadmat
from matplotlib import pylab as plt

if __name__ == '__main__':
    try:
        folder = sys.argv[1]
        ch1 = sys.argv[2]
        ch2 = sys.argv[3]
        resting_sig = loadmat(os.path.join(folder, "eeg-resting"))
        ssvep_sig = loadmat(os.path.join(folder, "eeg-ssvep"))
    except IndexError, ie:
        print "Usage: %s <data-folder> <channel1> <channel2>" % sys.argv[0]

    else:
        fs = 128.0
        time_step = 1/fs
        cut = 1*fs
        # Always drop the 1st second
        sample_count = ssvep_sig['SEQ'].size - int(cut)
        sample_freq = fftpack.fftfreq(sample_count, d=time_step)
        pidxs = np.where(sample_freq > 0)
        freqs = sample_freq[pidxs]

        # 3 for matlab meta data arrays, and 1 for SEQ

        #rest = signal.detrend(resting_sig[channel][0,:])
        #ssvep = signal.detrend(ssvep_sig[channel][0,:])
        #rest = resting_sig[channel][0,:]
        ssvep_ch1 = ssvep_sig[ch1][0,int(cut):]
        ssvep_ch2 = ssvep_sig[ch2][0,int(cut):]
        diff_signal = ssvep_ch1 - ssvep_ch2

        diff_fft = fftpack.fft(diff_signal)

        # Find powers
        sig_diff_power = np.abs(diff_fft)[pidxs]

        # Normalize
        #sig_diff_power = (sig_diff_power / sig_diff_power.max()) * 100
        #freqs, sig_diff_power = signal.welch(diff_signal, fs=128)

        plt.plot(freqs, sig_diff_power)
        #fig.tight_layout()
        plt.show()
