#!/usr/bin/python

import os
import glob
import sys

if __name__ == "__main__":
    epoc = None

    for dev in glob.glob("/sys/bus/usb/devices/*"):
        try:
            manu = open(os.path.join(dev, "manufacturer")).read().strip()
            if manu == "Emotiv Systems Pty Ltd":
                epoc = os.path.basename(dev)
        except:
            pass

    with open("/sys/bus/usb/drivers/usb/unbind", "w") as unbind:
        unbind.write(epoc)
    with open("/sys/bus/usb/drivers/usb/bind", "w") as bind:
        bind.write(epoc)


