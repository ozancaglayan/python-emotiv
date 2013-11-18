#!/usr/bin/env python

import pylsl

try:
    from emotiv import epoc
except ImportError:
    sys.path.insert(0, "..")
    from emotiv import epoc

if __name__ == '__main__':

    headset = epoc.EPOC()
    print "Found headset: ", headset.serial_number

    info = pylsl.stream_info('EPOC', 'EEG', len(headset.channel_mask),
                             headset.sampling_rate,
                             pylsl.cf_int16,
                             str(headset.serial_number))

    info_desc = info.desc()
    info_desc.append_child_value("manufacturer", "Emotiv")
    channels = info_desc.append_child("channels")

    for ch in headset.channel_mask:
        channels.append_child("channel").append_child_value("label", ch).append_child_value("unit","microvolts").append_child_value("type","EEG")

    # Outgoing buffer size = 360 seconds, transmission chunk size = 32 samples
    outlet = pylsl.stream_outlet(info, 360, 32)

    while True:
        s = headset.get_sample()
        if s:
            outlet.push_sample(pylsl.vectori(s), pylsl.local_clock())

    headset.disconnect()
