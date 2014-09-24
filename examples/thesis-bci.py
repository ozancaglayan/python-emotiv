#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:set et ts=4 sw=4:
#
## Copyright (C) 2014 Ozan Çağlayan <ocaglayan@gsu.edu.tr>
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
import signal
import random
import subprocess

from multiprocessing import Process, Pipe

from espeak import espeak

import numpy as np
from scipy.signal import filtfilt, butter, detrend
from nitime.algorithms.spectral import multi_taper_psd

from emotiv import epoc, utils

# DATA_DIR to save Matlab datasets
DATA_DIR = os.path.expanduser("~/BCIData")

# Enable to give auditory cues
CUE_BASED = False

### Classifier delegate
def classifier(conn):
    # Setup filter coefficients
    Wn = 5 / 64.0
    b, a = butter(2, Wn, "highpass")

    # Get experiment details
    experiment = conn.recv()

    # Setup PSD parameters
    psd_step = 1.0 / experiment['block_size']
    psd_points = (64 / psd_step) + 1
    freqs = np.linspace(0, 64, psd_points)
    psd = np.zeros((psd_points,))
    avg_psd = np.empty((psd_points,))

    # Fetch flickering frequencies
    freq_left = int(experiment['freq_left'])
    freq_right= int(experiment['freq_right'])

    # List for scores
    LEFT, RIGHT = range(2)

    if psd_step == 1:
        # Scoring is at the fundamental frequencies
        left_score = [freq_left]
        right_score = [freq_right]
    else:
        # Scoring is the average of the 3 neighbours centered
        # at the fundamental frequency, e.g. 16.5, 17, 17.5 for 17Hz for psd_step = 0.5
        left_score  = range(int((freq_left  / psd_step)) - 1, int((freq_left  / psd_step)) + 2)
        right_score = range(int((freq_right / psd_step)) - 1, int((freq_right / psd_step)) + 2)

    print "Frequency points\nleft: %s:%s\nright: %s:%s" % (left_score, freqs[left_score], right_score, freqs[right_score])

    while 1:
        its = 0
        scores = [0, 0]

        # Clear the array
        psd.fill(0)

        while 1:
            # Wait for data
            data = conn.recv()

            # Filter it
            f_data = filtfilt(b, a, detrend(data[:,0]))

            # Computer PSD and average it with the previous blocks
            psd += multi_taper_psd(f_data, Fs=128.0)[1]
            avg_psd = psd / (its + 1)

            # Increment counter
            its += 1

            left = avg_psd[left_score].mean()
            right = avg_psd[right_score].mean()

            scores[LEFT if left > right else RIGHT] += 1

            # If one class won at least 3 times, we decide for it.
            if abs(scores[LEFT] - scores[RIGHT]) >= 3:
                winner = "Left" if scores[LEFT] > scores[RIGHT] else "Right"
                conn.send({"iterations": its, "winner": winner})
                break


def stop_callback(pid):
    os.kill(pid, signal.SIGUSR1)

def main(argv):
    # Is there any soundcard detected?
    sound_enabled = "no soundcards" not in open("/proc/asound/cards", "r").read().strip()
    # Is there any robot plugged?

    # Create a Pipe IPC
    p_conn, c_conn = Pipe()
    dspd = Process(target=classifier, args=(c_conn,))
    dspd.start()

    # Set niceness of this process
    os.nice(-3)

    # Create DATA_DIR if not available
    try:
        os.makedirs(DATA_DIR)
    except:
        pass

    freq_left = freq_right = None

    # Parse cmdline args
    try:
        freq_left = argv[1]
        freq_right = argv[2]
        n_runs = int(argv[3])
    except:
        print "Usage: %s <frequency left> <frequency right> <n_runs>" % argv[0]
        sys.exit(1)

    # Spawn SSVEP daemon
    ssvepd = None
    try:
        ssvepd = subprocess.Popen(["./bbb-bci-ssvepd.py", freq_left, freq_right])
    except OSError, e:
        print "Error: Can't launch SSVEP daemon: %s" % e
        sys.exit(2)

    # Setup headset
    headset = epoc.EPOC(enable_gyro=False)
    headset.set_channel_mask(["O1", "O2", "P7", "P8"])

    # Collect experiment information
    experiment = {}
    experiment['n_runs'] = n_runs
    experiment['freq_left'] = freq_left
    experiment['freq_right'] = freq_right
    experiment['channel_mask'] = headset.channel_mask
    experiment['block_size'] = 2

    if sound_enabled:
        # Set TTS parameters
        espeak.set_parameter(espeak.Parameter.Pitch, 60)
        espeak.set_parameter(espeak.Parameter.Rate, 150)
        espeak.set_parameter(espeak.Parameter.Range, 600)

        # Equal amount of trials for each LED will be randomized
        cues = ["Left" for i in range(n_runs/2)] + ["Right" for i in range(n_runs/2)]
        random.shuffle(cues)
        random.shuffle(cues)
        experiment['cues'] = cues

    # Let classifier compute a PSD average over 2 second blocks
    p_conn.send(experiment)

    # Repeat n_runs time
    for i in range(experiment['n_runs']):
        # Give an auditory cue
        if CUE_BASED:
            espeak.synth(cues[i])

            while espeak.is_playing():
                time.sleep(0.1)

            time.sleep(2)

        # Start flickering
        ssvepd.send_signal(signal.SIGUSR1)

        # Acquire EEG data until classified
        while 1:
            idx, eeg = headset.acquire_data_fast(experiment['block_size'])
            if not p_conn.poll():
                # Not classified yet
                p_conn.send(eeg)
            else:
                break

        # Stop flickering
        ssvepd.send_signal(signal.SIGUSR1)

        # There's something to receive from classifier
        result = p_conn.recv()
        if sound_enabled:
            espeak.synth(result["winner"])
            while espeak.is_playing():
                time.sleep(0.1)
        else:
            print result["winner"]

    # Cleanup
    try:
        headset.disconnect()
        ssvepd.terminate()
        ssvepd.wait()
        dspd.join(0)
        dspd.terminate()
    except e:
        print e

if __name__ == "__main__":
    sys.exit(main(sys.argv))
