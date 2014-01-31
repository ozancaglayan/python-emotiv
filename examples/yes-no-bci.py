#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:set et ts=4 sw=4:
#
## Copyright (C) 2013 Ozan Çağlayan <ocaglayan@gsu.edu.tr>
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
import socket
import subprocess

from espeak import espeak

import numpy as np
from scipy.io import savemat

DSPD_SOCK = "/tmp/bbb-bci-dspd.sock"
DATA_DIR = os.path.expanduser("~/BCIData")

from emotiv import epoc, utils


def get_subject_information():
    initials = raw_input("Initials: ")
    age = raw_input("Age: ")
    sex = raw_input("Sex (M)ale / (F)emale: ")
    comment = raw_input("Experiment description: ")
    return {
            "age"       :  age,
            "sex"       :  sex,
            "initials"  :  initials,
            "comment"   :  comment,
           }

def save_as_dataset(rest_eegs, ssvep_eegs, experiment):
    """Save whole recording as a single dataset."""
    matlab_data = {}

    # len(rest_eegs) == len(ssvep_eegs) == experiment['n_trials']
    n_trials = experiment['n_trials']
    channel_mask = experiment['channel_mask']

    trial = np.zeros((n_trials,), dtype=np.object)
    rest = np.zeros((n_trials,), dtype=np.object)
    trial_time = np.zeros((n_trials,), dtype=np.object)

    for t in range(n_trials):
        trial[t] = ssvep_eegs[t][:, :].T
        trial_time[t] = np.array(range(ssvep_eegs[t][:, 0].size)) / 128.0
        if rest_eegs:
            rest[t] = rest_eegs[t][:, :].T

    # This structure can be read by fieldtrip functions directly
    fieldtrip_data = {"fsample"     : 128.0,
                      "label"       : np.array(channel_mask, dtype=np.object).reshape((len(channel_mask), 1)),
                      "trial"       : trial,
                      "rest"        : rest,
                      "time"        : trial_time,
                     }

    matlab_data["data"] = fieldtrip_data

    # Inject metadata if any
    for key, value in experiment.items():
        matlab_data[key] = value

    # Put time of recording
    date_info = time.strftime("%d-%m-%Y_%H-%M")
    day_info = time.strftime("%d-%m-%Y")
    matlab_data["date"] = date_info

    output = "%s-%d-trials-of-%dsecs-%s-%sHz-%sHz-%s" % (experiment['initials'],
                                                         n_trials, experiment['trial_duration'],
                                                         experiment['comment'],
                                                         experiment['freq_left'], experiment['freq_right'],
                                                         date_info)

    output_folder = os.path.join(DATA_DIR, day_info, output)
    try:
        os.makedirs(output_folder)
    except:
        pass
    savemat(os.path.join(output_folder, "dataset.mat"), matlab_data, oned_as='row')

def stop_callback(pid):
    os.kill(pid, signal.SIGUSR1)

def main(argv):
    local_time = time.localtime()

    # Set TTS parameters
    espeak.set_parameter(espeak.Parameter.Pitch, 60)
    espeak.set_parameter(espeak.Parameter.Rate, 150)
    espeak.set_parameter(espeak.Parameter.Range, 600)

    # Set niceness of this process
    os.nice(-3)

    # Create DATA_DIR if not available
    try:
        os.makedirs(DATA_DIR)
    except:
        pass

    duration = None
    freq_left = freq_right = None

    # Parse cmdline args
    try:
        freq_left = argv[1]
        freq_right = argv[2]
        duration = int(argv[3])
        n_trials = int(argv[4])
    except:
        print "Usage: %s <frequency left> <frequency right> <trial_duration> <n_trials>" % argv[0]
        sys.exit(1)

    # Spawn SSVEP and DSPD process
    ssvepd = None
    dspd = None
    try:
        ssvepd = subprocess.Popen(["./bbb-bci-ssvepd.py", freq_left, freq_right])
        #dspd = subprocess.Popen(["./bbb-bci-dspd.py"])
    except OSError, e:
        print "Error: Can't launch SSVEP/DSP subprocesses: %s" % e
        sys.exit(2)

    # Open socket to DSP process if any
    if dspd:
        sock = socket.socket(socket.AF_UNIX)
        sock_connected = False
        for i in range(10):
            try:
                sock.connect(DSPD_SOCK)
                sock_connected = True
            except:
                time.sleep(0.5)

    # Setup headset
    headset = epoc.EPOC(enable_gyro=False)
    headset.set_channel_mask(["O1", "O2", "P7", "P8"])

    # Collect experiment information
    experiment = get_subject_information()
    experiment['channel_mask'] = headset.channel_mask
    experiment['n_trials'] = n_trials
    experiment['trial_duration'] = duration

    # Equal amount of trials for each LED will be randomized
    cues = ["Left" for i in range(n_trials/2)] + ["Right" for i in range(n_trials/2)]
    random.shuffle(cues)
    random.shuffle(cues)
    experiment['cues'] = cues

    # Add flickering frequency informations
    experiment['freq_left'] = freq_left
    experiment['freq_right'] = freq_right

    # FIXME: Experiment data (7 bytes)
    # sock.send("%7s" % experiment)

    # Send 4 bytes of data for duration
    # sock.send("%4d" % duration)

    # Send comma separated list of enabled channels (49 bytes max.)
    # channel_conf = "CTR," + ",".join(headset.channel_mask)
    # sock.send("%49s" % channel_conf)

    rest_eegs = []
    ssvep_eegs = []

    # Repeat nb_trials time
    for i in range(experiment['n_trials']):
        # Acquire resting data (A random duration of 2,3 or 4 seconds to avoid adaptation)
        #idx, eeg = headset.acquire_data_fast(random.randint(2,4))
        #rest_eegs.append(eeg)
        #print utils.check_packet_drops(idx)

        # Give an auditory cue
        espeak.synth(cues[i])

        while espeak.is_playing():
            time.sleep(0.1)

        time.sleep(2)

        # Start flickering
        ssvepd.send_signal(signal.SIGUSR1)

        # Acquire EEG data for duration seconds and stop flickering
        idx, eeg = headset.acquire_data_fast(duration, stop_callback, ssvepd.pid)
        ssvep_eegs.append(eeg)
        #print utils.check_packet_drops(idx)

    # Save dataset
    experiment['battery'] = headset.battery
    save_as_dataset(rest_eegs, ssvep_eegs, experiment)

    # Cleanup
    try:
        print "Disconnecting headset..."
        headset.disconnect()
        print "Terminating ssvepd..."
        ssvepd.terminate()
        print "Waiting ssvepd termination..."
        ssvepd.wait()
        if dspd and sock_connected:
            sock.close()
            dspd.terminate()
            dspd.wait()
    except e:
        print e

if __name__ == "__main__":
    sys.exit(main(sys.argv))
