#!/usr/bin/env python

import os
import sys

import numpy as np

from scipy import fftpack, signal
from scipy.io import loadmat
from matplotlib import pylab as plt

from emotiv import utils

if __name__ == '__main__':
    if len(sys.argv) > 2:
        ch = list(sys.argv[2:])
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

        resting_drops = utils.check_packet_drops(resting_sig['SEQ'][0,:])
        ssvep_drops = utils.check_packet_drops(ssvep_sig['SEQ'][0,:])
        if ssvep_drops:
            print "SSVEP drops: %s" % ssvep_drops
        if resting_drops:
            print "Resting drops: %s" % resting_drops

        if ch:
            fig, axarr = plt.subplots(5, len(ch), sharex=False)
            axarr = np.array(axarr).reshape((-1, len(ch)))
            channels = ch
        else:
            # 3 for matlab meta data arrays, and 1 for SEQ
            fig, axarr = plt.subplots(5, len(ssvep_sig) - 4, sharex=False)
            channels = [c for c in ssvep_sig.keys() if not c.startswith(("__", "SEQ"))]

        for index, channel in enumerate(channels):
            rest = signal.detrend(resting_sig[channel][0,:], type='constant')
            ssvep = signal.detrend(ssvep_sig[channel][0,:], type='constant')
            #rest = resting_sig[channel][0,:]
            #ssvep = ssvep_sig[channel][0,:]
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
            """
            freqs, rest_power = signal.welch(rest, fs=128, scaling='spectrum')
            freqs, ssvep_power = signal.welch(ssvep, fs=128)
            freqs, sig_diff_power = signal.welch(diff_signal, fs=128)
            """

            axarr[0, index].plot(ssvep)
            axarr[0, index].plot(rest, color='r')
            axarr[0, index].set_title("EEG(%s)" % channel)
            axarr[1, index].plot(freqs, rest_power)
            axarr[1, index].set_title("Resting(%s)" % channel)
            axarr[2, index].plot(freqs, ssvep_power)
            axarr[2, index].set_title("SSVEP(%s)" % channel)
            axarr[3, index].plot(freqs, ssvep_power - rest_power)
            axarr[3, index].set_title("Difference(%s)" % channel)
            axarr[4, index].plot(freqs, sig_diff_power)
            axarr[4, index].set_title("Signal Difference(%s)" % channel)

        fig.tight_layout()
        plt.show()
