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

from scipy import fftpack, signal
from scipy.io import loadmat

import spectrum
import time
import nitime

from matplotlib import pylab as pl

def fft(data):
    # Those can be precomputed for several data lengths
    time_step = 1/128.0

    sampling_freqs = fftpack.fftfreq(data.size, d=time_step)
    positive_freqs = np.where(sampling_freqs > 0)
    freqs = sampling_freqs[positive_freqs]

    # Here's the computation part
    power = np.abs(fftpack.fft(signal.detrend(data)))[positive_freqs]
    return freqs, power

def psd_classifier(eeg_data, experiment, block_size, time_range=None):

    labels = ['o1', 'o2', 'o1-o2', 'o1-p7', 'o1-p8', 'o2-p7', 'o2-p8', 'o1-avg', 'o2-avg']

    # Steps between frequency points after PSD estimation (1, 0.5, 0.25, etc)
    psd_step = 128.0/block_size
    psd_res = (64 / psd_step) + 1

    n_trials = experiment['n_trials']
    channel_mask = experiment['channel_mask']
    cues = experiment['cues']

    left_freq = float(experiment['freq_left'])
    right_freq = float(experiment['freq_right'])

    plot_left_bounds = min(left_freq, right_freq) - 2
    plot_right_bounds = max(left_freq, right_freq)*2 + 2

    if left_freq < 20:
        left_scores = [left_freq, left_freq*2-psd_step, left_freq*2, left_freq*2 + psd_step]
    else:
        left_scores = [left_freq - psd_step, left_freq, left_freq + psd_step]

    if right_freq < 20:
        right_scores = [right_freq, right_freq*2-psd_step, right_freq*2, right_freq*2 + psd_step]
    else:
        right_scores = [right_freq - psd_step, right_freq, right_freq + psd_step]

    print "Left freq powers @ ", left_scores
    print "Right freq powers @ ", right_scores

    # Classification results
    results = np.zeros([n_trials + 1, len(labels)])

    # Final averaged burg psd's
    final_pxx = np.zeros([n_trials, psd_res, len(labels)])

    # High-pass filter
    Wn = 5 / 64.0
    b, a = signal.butter(9, Wn, "highpass")

    for t in range(n_trials):
        # FIXME: Use time_range

        # Apply filter
        o1 = signal.filtfilt(b, a, eeg_data[t][channel_mask.index("O1"), :].T)
        o2 = signal.filtfilt(b, a, eeg_data[t][channel_mask.index("O2"), :].T)
        p7 = signal.filtfilt(b, a, eeg_data[t][channel_mask.index("P7"), :].T)
        p8 = signal.filtfilt(b, a, eeg_data[t][channel_mask.index("P8"), :].T)

        # Find common average
        avg = (o1 + o2 + p7 + p8) / 4.0

        # Create an array of interesting channel combinations
        chans = np.array([eval(c) for c in labels])

        # Trial cue
        cue = cues[t].strip().lower()

        # Process each channel
        for i in range(len(chans)):
            pxx = np.zeros(psd_res)
            avg_psd = np.zeros(psd_res)
            hits = {"left" : 0, "right" : 0}

            d = signal.detrend(chans[i])
            iterations = d.size / block_size

            print "Channel is %s, variance is %.2f" % (labels[i], np.var(d, ddof=1))

            for it in range(iterations):
                block = d[it * block_size: ((it+1) * block_size)]
                #p = spectrum.pburg(block, 64, NFFT=128, sampling=128.0)
                #p.run()
                #avg_burg += 10*np.log10(p.psd)
                freqs, n_pxx, l = nitime.algorithms.spectral.multi_taper_psd(block, Fs=128.0)
                #freqs, n_pxx = nitime.algorithms.spectral.periodogram(block, Fs=128.0, N=128)
                pxx += n_pxx
                avg_psd = pxx / (it + 1)

                fl_mean = avg_psd[[int(s/psd_step) for s in left_scores]].mean()
                fr_mean = avg_psd[[int(s/psd_step) for s in right_scores]].mean()

                if fl_mean > fr_mean:
                    hits["left"] += 1
                else:
                    hits["right"] += 1

                print "Trial %d (Cue: %s (%sHz)): [%d/%d] Left: %.2f (%d) Right: %.2f (%d)" % ((t + 1), cue, eval("%s_freq" % cue),
                        (it + 1), iterations, fl_mean, hits["left"], fr_mean, hits["right"])
                #pl.plot(freqs,10*np.log10(avg_psd))
                #pl.show()


            print "Left %d, Right %d for cue %s" % (hits["left"], hits["right"], cue)

            # Record averaged PSD's
            final_pxx[t, :, i] = avg_psd
            #pl.plot(freqs,10*np.log10(avg_psd))
            #pl.show()

            if (hits["left"] > hits["right"] and cue == "left") or (hits["right"] > hits["left"] and cue == "right"):
                results[t, i] = 1

    # Calculate total scores
    results[-1] = np.mean(results[:-1], axis=0)
    for i in range(len(labels)):
        if results[-1, i] > 0.5:
            print "Channel: %s, Classification Rate: %.2f%%" % (labels[i], results[-1, i]*100)

    #max_idx = np.where(results[-1] > 0.5)[0]
    #print labels[c]

    #return [(labels[c], results[:, c]) for c in max_idx]
    return results

if __name__ == "__main__":
    # Test code for classifier function above
    import sys

    m = loadmat(sys.argv[1])
    eeg = m['data']['trial'][0][0][0]

    exp = {
            "n_trials"      : int(m["n_trials"]),
            "channel_mask"  : [d.strip() for d in m['channel_mask'].tolist()],
            "cues"          : [d.strip() for d in m['cues'].tolist()],
            "freq_right"    : m['freq_right'][0].strip(),
            "freq_left"     : m['freq_left'][0].strip(),
          }

    results = psd_classifier(eeg, exp, 256)
