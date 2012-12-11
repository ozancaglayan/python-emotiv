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

import os
import sys

import usb.core
import usb.util

import numpy as np

from matplotlib import pyplot as plt

class EmotivEPOCNotFoundException(Exception):
    pass


class EmotivEPOC(object):
    def __init__(self, serialNumber=None):
        # Apparently these can change from dongle to dongle
        # so leave this just for reference
        # self.EPOC_VID = 0x1234
        # self.EPOC_PID = 0xED02

        # These seem to be the same for every device
        self.INTERFACE_DESC = "Emotiv RAW DATA"
        self.MANUFACTURER_DESC = "Emotiv Systems Pty Ltd"
        self.ENDPOINT_IN = usb.util.ENDPOINT_IN | 2

        # Channel names
        self.channels = ['Counter', 'Battery',
                        'F3', 'FC5', 'AF3', 'F7', 'T7', 'P7', 'O1',
                        'O2', 'P8', 'T8', 'F8', 'AF4', 'FC6', 'F4',
                        'GyroX', 'GyroY',
                        'Quality F3', 'Quality FC5', 'Quality AF3',
                        'Quality F7', 'Quality T7', 'Quality P7',
                        'Quality 01', 'Quality O2', 'Quality P8',
                        'Quality T8', 'Quality F8', 'Quality AF4',
                        'Quality FC6', 'Quality F4']

        # One can want to specify the dongle with its serial
        self.serialNumber = serialNumber

        # Serial number indexed device map
        self.devices = {}

    def _is_emotiv_epoc(self, device):
        """Custom match function for libusb."""
        try:
            manu = usb.util.get_string(device, len(self.MANUFACTURER_DESC),
                                       device.iManufacturer)
        except usb.core.USBError, ue:
            # Skip failing devices as it happens on Raspberry Pi
            if ue.errno == 32
                return False

        if manu == self.MANUFACTURER_DESC:
            # Found a dongle, check for interface class 3
            for interf in device.get_active_configuration():
                ifStr = usb.util.get_string(device, len(self.INTERFACE_DESC),
                                            interf.iInterface)
                if ifStr == self.INTERFACE_DESC:
                    return True

    def enumerate(self):
        devs = usb.core.find(find_all=True, custom_match=self._is_emotiv_epoc)

        if not devs:
            raise EmotivEPOCNotFoundException("No plugged Emotiv EPOC")

        for dev in devs:
            sn = usb.util.get_string(dev, 32, dev.iSerialNumber)
            self.devices[sn] = dev
            self.serialNumber = sn

            # Detach possible kernel drivers
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
            if dev.is_kernel_driver_active(1):
                dev.detach_kernel_driver(1)

            # Claim interfaces before using
            usb.util.claim_interface(dev, 0)
            usb.util.claim_interface(dev, 1)

            # FIXME: Default to the first device for now
            break

    def setupEncryption(self, research=True):
        """Generate the encryption key and setup Crypto module.
        The key is based on the serial number of the device and the information
        whether it is a research or consumer device.
        """
        if research:
            self.key = ''.join([self.serialNumber[15], '\x00',
                                self.serialNumber[14], '\x54',
                                self.serialNumber[13], '\x10',
                                self.serialNumber[12], '\x42',
                                self.serialNumber[15], '\x00',
                                self.serialNumber[14], '\x48',
                                self.serialNumber[13], '\x00',
                                self.serialNumber[12], '\x50'])
        else:
            self.key = ''.join([self.serialNumber[15], '\x00',
                                self.serialNumber[14], '\x48',
                                self.serialNumber[13], '\x00',
                                self.serialNumber[12], '\x54',
                                self.serialNumber[15], '\x10',
                                self.serialNumber[14], '\x42',
                                self.serialNumber[13], '\x00',
                                self.serialNumber[12], '\x50'])

        from Crypto.Cipher import AES
        self.cipher = AES.new(self.key)

    def decryptData(self, rawData):
        """Decrypts a raw data packet."""
        unencryptedData = self.cipher.decrypt(rawData[:16]) +\
                          self.cipher.decrypt(rawData[16:])

        # FIXME: What's this?
        tmp = 0
        for i in range(32):
            tmp = tmp << 8
            tmp += ord(unencryptedData[i])

        return tmp

    def acquireData(self):
        try:
            raw = self.devices[self.serialNumber].read(self.ENDPOINT_IN, 32,
                               1, timeout=1000)
            print self.decryptData(raw)
        except Exception as e:
            print e

    def connect(self):
        pass

    def waitForContact(self):
        pass

    def getContactQuality(self):
        pass

    def getBatteryLevel(self):
        pass

    def disconnect(self):
        pass

if __name__ == "__main__":

    if len(sys.argv) > 2:
        # Pass a specific S/N
        emotiv = EmotivEPOC(sys.argv[1])
    else:
        emotiv = EmotivEPOC()

    print "Enumerating devices..."
    emotiv.enumerate()
    for k,v in emotiv.devices.iteritems():
        print "Found dongle with S/N: %s" % k

    emotiv.setupEncryption()

    try:
        while True:
            emotiv.acquireData()
    except KeyboardInterrupt, ke:
        sys.exit(1)
