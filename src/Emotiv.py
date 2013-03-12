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

from __future__ import print_function

import os
import sys
import time

from multiprocessing import Pool, Queue, Process, JoinableQueue
from multiprocessing.managers import BaseManager

import usb.core
import usb.util

import numpy as np

from scipy import fftpack
from scipy.io import savemat

from decryptionProcess import decryptionProcess as decryptionThread

class EmotivEPOCNotFoundException(Exception):
    pass

class EmotivEPOCTurnedOffException(Exception):
    pass

class EmotivEPOCException(Exception):
    pass

class EmotivEPOC(object):
    def __init__(self, serialNumber=None):
        # These seem to be the same for every device
        self.__INTERFACE_DESC = "Emotiv RAW DATA"
        self.__MANUFACTURER_DESC = "Emotiv Systems Pty Ltd"

        # Define a contact quality ordering
        # See:
        #   github.com/openyou/emokit/blob/master/doc/emotiv_protocol.asciidoc
        # For counter values between 0-15
        self.cqOrder = ["F3", "FC5", "AF3", "F7", "T7",  "P7",  "O1",
                        "O2", "P8",  "T8",  "F8", "AF4", "FC6", "F4",
                        "F8", "AF4"]
        # 16-63 is currently unknown
        self.cqOrder.extend([None,] * 48)
        # Now the first 16 values repeat once more and ends with 'FC6'
        self.cqOrder.extend(self.cqOrder[:16])
        self.cqOrder.append("FC6")
        # Finally pattern 77-80 repeats until 127
        self.cqOrder.extend(self.cqOrder[-4:] * 12)

        # Channel names
        self.channels = ["F3", "FC5", "AF3", "F7", "T7", "P7", "O1",
                         "O2", "P8",  "T8",  "F8", "AF4","FC6","F4"]

        # Update __dict__ with convenience attributes for channels
        self.__dict__.update(dict((v, k) for k,v in enumerate(self.channels)))

        # Store slices for bit manipulation for convenience
        # This way we can get EEG data for a channel from a bitarray
        # using bits[self.__slices["O3"]].
        self.slices = dict((k, v) for k,v in
                                zip(self.channels, (slice(8,22),
                                                    slice(22,36),
                                                    slice(36,50),
                                                    slice(50,64),
                                                    slice(64,78),
                                                    slice(78,92),
                                                    slice(92,106),
                                                    slice(134,148),
                                                    slice(148,162),
                                                    slice(162,176),
                                                    slice(176,190),
                                                    slice(190,204),
                                                    slice(204,218),
                                                    slice(218,232))))

        # Gyroscope and sequence number slices
        self.slices["GYROX"] = slice(233,240)
        self.slices["GYROX"] = slice(240,248)
        self.slices["SEQ#"] = slice(0,8)

        ##################
        # ADC parameters #
        # ################

        # Sampling rate: 128Hz (Internal: 2048Hz)
        self.sampling_rate = 128

        # Vertical resolution (0.51 microVolt)
        self.resolution = 0.51

        # Each channel has 14 bits of data
        self.ch_bits = 14

        self.ch_buffer = np.ndarray([len(self.channels), self.sampling_rate],
                buffer=np.zeros([len(self.channels), self.sampling_rate]), dtype=int)

        # Battery levels
        # github.com/openyou/emokit/blob/master/doc/emotiv_protocol.asciidoc
        self.battery_levels = {247:99, 246:97, 245:93, 244:89, 243:85,
                               242:82, 241:77, 240:72, 239:66, 238:62,
                               237:55, 236:46, 235:32, 234:20, 233:12,
                               232: 6, 231: 4, 230: 3, 229: 2, 228: 1,
                               227: 1, 226: 1,
                               }
        # 100% for bit values between 248-255
        self.battery_levels.update(dict([(k,100) for k in range(248, 256)]))
        # 0% for bit values between 128-225
        self.battery_levels.update(dict([(k,0)   for k in range(128, 226)]))

        # One can want to specify the dongle with its serial
        self.serialNumber = serialNumber

        # Serial number indexed device map
        self.devices = {}
        self.endpoints = {}

        # Acquired data
        self.packetLoss = 0
        self.counter = 0
        self.battery = 0
        self.gyroX   = 0
        self.gyroY   = 0
        self.quality = {
                            "F3" : 0, "FC5" : 0, "AF3" : 0, "F7" : 0,
                            "T7" : 0, "P7"  : 0, "O1"  : 0, "O2" : 0,
                            "P8" : 0, "T8"  : 0, "F8"  : 0, "AF4": 0,
                            "FC6": 0, "F4"  : 0,
                       }

        self.input_queue = JoinableQueue()
        self.output_queue = Queue()

    def _is_emotiv_epoc(self, device):
        """Custom match function for libusb."""
        try:
            manu = usb.util.get_string(device, len(self.__MANUFACTURER_DESC),
                                       device.iManufacturer)
        except usb.core.USBError, ue:
            # Skip failing devices as it happens on Raspberry Pi
            if ue.errno == 32:
                return False
            elif ue.errno == 13:
                self.permissionProblem = True
                pass
        else:
            if manu == self.__MANUFACTURER_DESC:
                # Found a dongle, check for interface class 3
                for interf in device.get_active_configuration():
                    ifStr = usb.util.get_string(device, len(self.__INTERFACE_DESC),
                                                interf.iInterface)
                    if ifStr == self.__INTERFACE_DESC:
                        return True

    def enumerate(self):
        devs = usb.core.find(find_all=True, custom_match=self._is_emotiv_epoc)

        if not devs:
            raise EmotivEPOCNotFoundException("No plugged Emotiv EPOC")

        for dev in devs:
            sn = usb.util.get_string(dev, 32, dev.iSerialNumber)
            cfg = dev.get_active_configuration()

            for interf in dev.get_active_configuration():
                if dev.is_kernel_driver_active(interf.bInterfaceNumber):
                    # Detach kernel drivers and claim through libusb
                    dev.detach_kernel_driver(interf.bInterfaceNumber)
                    usb.util.claim_interface(dev, interf.bInterfaceNumber)

            # 2nd interface is the one we need
            self.endpoints[sn] = usb.util.find_descriptor(interf,
                                 bEndpointAddress=usb.ENDPOINT_IN|2)

            self.devices[sn] = dev
            self.serialNumber = sn

            # FIXME: Default to the first device for now
            break

    def setupEncryption(self, research=True):
        """Generate the encryption key and setup Crypto module.
        The key is based on the serial number of the device and the
        information whether it is a research or consumer device.
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

        self.decryptionProcess = Process(target=decryptionThread,
                                         args=[self.key, self.input_queue,
                                               self.output_queue])
        self.decryptionProcess.daemon = True
        self.decryptionProcess.start()

    def acquireData(self, duration, channelMask, savePrefix=None):
        totalSamples = duration * self.sampling_rate
        while self.output_queue.qsize() != totalSamples:
            # Fetch new data
            try:
                raw = self.endpoints[self.serialNumber].read(32, timeout=1000)
                self.input_queue.put(raw)
            except usb.USBError as e:
                if e.errno == 110:
                    raise EmotivEPOCTurnedOffException("Make sure that headset is turned on")
                else:
                    raise EmotivEPOCException(e)

        # Process and return the final data

        # +1 for sequence numbers
        eeg_data = np.zeros((len(channelMask)+1, self.output_queue.qsize()))
        for spl in xrange(self.output_queue.qsize()):
            bits = self.output_queue.get_nowait()
            eeg_data[0, spl] = bits[self.slices["SEQ#"]].uint
            for i,chName in enumerate(channelMask):
                # chName's are strings like "O1", "O2", etc.
                eeg_data[i+1, spl] = bits[self.slices[chName]].uint

        if savePrefix:
            # Save as matlab data with channel annotations
            matlabData = {"SEQ" : eeg_data[0]}
            for i,chName in enumerate(channelMask):
                matlabData[chName] = eeg_data[i+1]
            savemat("%s-%s.mat" % (savePrefix, "-".join(channelMask)),
                    matlabData, oned_as='row')

        return eeg_data

    def getData(self, what):
        self.acquireData()
        return self.ch_buffer[self.channels.index(what), :]

    def dumpData(self):
        # Clear screen
        print("\x1b[2J\x1b[H")
        header = "Emotiv Data Packet [%3d/128] [Loss: %3d] [Battery: %2d(%%)]" % (
            self.counter, self.packetLoss, self.battery)
        print("%s\n%s" % (header, '-'*len(header)))

        print("%10s: %5d" % ("Gyro(x)", self.gyroX))
        print("%10s: %5d" % ("Gyro(y)", self.gyroY))

        for i,channel in enumerate(self.channels):
            print("%10s: %5d %20s: %5d (%.2f)" % (channel,
                                           self.ch_buffer[i, self.counter],
                                           "Quality", self.quality[channel],
                                           self.quality[channel]/540.))

    def calibrateGyro(self):
        """Gyroscope has a baseline value. We can subtract that
        from the acquired values to maintain the baseline at (0,0)"""
        pass

    def getGyroX(self):
        self.acquireData()
        yield self.gyroX

    def getGyroY(self):
        self.acquireData()
        yield self.gyroY

    def getContactQuality(self, electrode):
        "Return contact quality for the specified electrode."""
        try:
            return self.quality[electrode]
        except KeyError, ke:
            print("Electrode name %s is wrong." % electrode)

    def getBatteryLevel(self):
        """Returns the battery level."""
        return self.battery

    def disconnect(self):
        """Release the claimed interfaces."""

        for dev in self.devices.values():
            cfg = dev.get_active_configuration()

            for interf in dev.get_active_configuration():
                usb.util.release_interface(dev, interf.bInterfaceNumber)
