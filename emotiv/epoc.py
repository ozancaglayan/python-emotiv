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

"""\
This module provides the EPOC class for accessing Emotiv EPOC
EEG headsets.
"""

import os

from multiprocessing import Process, JoinableQueue

import usb.core
import usb.util

import numpy as np

from scipy.io import savemat

import decryptor, utils


class EPOCError(Exception):
    """Base class for exceptions in this module."""
    pass


class EPOCTurnedOffError(EPOCError):
    """Exception raised when Emotiv EPOC is not turned on."""
    pass


class EPOCDeviceNodeNotFoundError(EPOCError):
    """Exception raised when /dev/emotiv_epoc is missing."""
    pass


class EPOCUSBError(EPOCError):
    """Exception raised when error occurs during I/O operations."""
    pass


class EPOCNotPluggedError(EPOCError):
    """Exception raised when EPOC dongle cannot be detected."""
    pass


class EPOCPermissionError(EPOCError):
    """Exception raised when EPOC dongle cannot be opened for I/O."""
    pass


class EPOC(object):
    """Class for accessing Emotiv EPOC headset devices."""

    # Device descriptions for USB
    INTERFACE_DESC = "Emotiv RAW DATA"
    MANUFACTURER_DESC = "Emotiv Systems Pty Ltd"

    # Channel names
    channels = ["F3", "FC5", "AF3", "F7", "T7", "P7", "O1",
                "O2", "P8",  "T8",  "F8", "AF4", "FC6", "F4"]

    # Sampling rate: 128Hz (Internal: 2048Hz)
    sampling_rate = 128

    # Battery levels
    # github.com/openyou/emokit/blob/master/doc/emotiv_protocol.asciidoc
    battery_levels = {247: 99, 246: 97, 245: 93, 244: 89, 243: 85,
                      242: 82, 241: 77, 240: 72, 239: 66, 238: 62,
                      237: 55, 236: 46, 235: 32, 234: 20, 233: 12,
                      232: 6, 231: 4, 230: 3, 229: 2, 228: 1,
                      227: 1, 226: 1,
                      }
    # 100% for bit values between 248-255
    battery_levels.update(dict([(k, 100) for k in range(248, 256)]))
    # 0% for bit values between 128-225
    battery_levels.update(dict([(k, 0) for k in range(128, 226)]))

    # Define a contact quality ordering
    #   github.com/openyou/emokit/blob/master/doc/emotiv_protocol.asciidoc

    # For counter values between 0-15
    cq_order = ["F3", "FC5", "AF3", "F7", "T7",  "P7",  "O1",
                "O2", "P8",  "T8",  "F8", "AF4", "FC6", "F4",
                "F8", "AF4"]

    # 16-63 is currently unknown
    cq_order.extend([None, ] * 48)

    # Now the first 16 values repeat once more and ends with 'FC6'
    cq_order.extend(cq_order[:16])
    cq_order.append("FC6")

    # Finally pattern 77-80 repeats until 127
    cq_order.extend(cq_order[-4:] * 12)

    # Store slices for bit manipulation for convenience
    # This way we can get EEG data for a channel from a bitarray
    # using bits[self.__slices["O3"]].
    slices = dict((k, v) for k, v in
                  zip(channels, (slice(8, 22),
                                 slice(22, 36),
                                 slice(36, 50),
                                 slice(50, 64),
                                 slice(64, 78),
                                 slice(78, 92),
                                 slice(92, 106),
                                 slice(134, 148),
                                 slice(148, 162),
                                 slice(162, 176),
                                 slice(176, 190),
                                 slice(190, 204),
                                 slice(204, 218),
                                 slice(218, 232))))

    # Gyroscope and sequence number slices
    slices["GYROX"] = slice(233, 240)
    slices["GYROY"] = slice(240, 248)
    slices["SEQ#"] = slice(0, 8)

    def __init__(self, method, serial_number=None):
        self.vendor_id = None
        self.product_id = None
        self.decryptor = None
        self.decryption_key = None

        self.buffer = None

        # Access method can be 'hidraw' or 'libusb'
        self.method = method

        # One may like to specify the dongle with its serial
        self.serial_number = serial_number

        # libusb device and endpoint
        self.device = None
        self.endpoint = None

        # By default acquire from all channels
        self.channel_mask = self.channels

        # Dict for storing contact qualities
        self.quality = {
            "F3": 0, "FC5": 0, "AF3": 0, "F7": 0,
            "T7": 0, "P7": 0, "O1": 0, "O2": 0,
            "P8": 0, "T8": 0, "F8": 0, "AF4": 0,
            "FC6": 0, "F4": 0,
        }

        # Update __dict__ with convenience attributes for channels
        self.__dict__.update(dict((v, k) for k, v in enumerate(self.channels)))

        # Queues
        self.input_queue = JoinableQueue()
        self.output_queue = JoinableQueue()

        # Enumerate the bus to find EPOC devices
        self.enumerate()

    def _is_epoc(self, device):
        """Custom match function for libusb."""
        try:
            manu = usb.util.get_string(device, len(self.MANUFACTURER_DESC),
                                       device.iManufacturer)
        except usb.core.USBError, usb_exception:
            # Skip failing devices as it happens on Raspberry Pi
            if usb_exception.errno == 32:
                return False
            elif usb_exception.errno == 13:
                print usb_exception
                raise EPOCPermissionError("Problem with device permissions.")
        else:
            if manu == self.MANUFACTURER_DESC:
                # Found a dongle, check for interface class 3
                for interf in device.get_active_configuration():
                    if_str = usb.util.get_string(
                        device, len(self.INTERFACE_DESC),
                        interf.iInterface)
                    if if_str == self.INTERFACE_DESC:
                        return True

    def set_channel_mask(self, channel_mask):
        """Set channels from which to acquire."""
        self.channel_mask = channel_mask

    def enumerate(self):
        """Traverse through USB bus and enumerate EPOC devices."""
        devices = usb.core.find(find_all=True, custom_match=self._is_epoc)

        if not devices:
            raise EPOCNotPluggedError("Emotiv EPOC not found.")

        for dev in devices:
            serial = usb.util.get_string(dev, 32, dev.iSerialNumber)
            if self.serial_number and self.serial_number != serial:
                # If a special S/N is given, look for it.
                continue

            # Record some attributes
            self.serial_number = serial
            self.vendor_id = "%X" % dev.idVendor
            self.product_id = "%X" % dev.idProduct

            if self.method == "libusb":
                # 2nd interface is the one we need
                interface = dev.get_active_configuration()[1]
                if dev.is_kernel_driver_active(interface.bInterfaceNumber):
                    # Detach kernel drivers and claim through libusb
                    dev.detach_kernel_driver(interface.bInterfaceNumber)
                    usb.util.claim_interface(dev, interface.bInterfaceNumber)

                self.device = dev
                self.endpoint = usb.util.find_descriptor(
                    interface, bEndpointAddress=usb.ENDPOINT_IN | 2)
            elif self.method == "hidraw":
                if os.path.exists("/dev/emotiv_epoc"):
                    self.endpoint = open("/dev/emotiv_epoc")
                else:
                    raise EPOCDeviceNodeNotFoundError(
                        "/dev/emotiv_epoc doesn't exist.")

            # Return the first Emotiv headset by default
            break

        self.setup_encryption()
        self.endpoint.read(32)

    def setup_encryption(self, research=True):
        """Generate the encryption key and setup Crypto module.
        The key is based on the serial number of the device and the
        information whether it is a research or consumer device.
        """
        if research:
            self.decryption_key = ''.join([self.serial_number[15], '\x00',
                                           self.serial_number[14], '\x54',
                                           self.serial_number[13], '\x10',
                                           self.serial_number[12], '\x42',
                                           self.serial_number[15], '\x00',
                                           self.serial_number[14], '\x48',
                                           self.serial_number[13], '\x00',
                                           self.serial_number[12], '\x50'])
        else:
            self.decryption_key = ''.join([self.serial_number[15], '\x00',
                                           self.serial_number[14], '\x48',
                                           self.serial_number[13], '\x00',
                                           self.serial_number[12], '\x54',
                                           self.serial_number[15], '\x10',
                                           self.serial_number[14], '\x42',
                                           self.serial_number[13], '\x00',
                                           self.serial_number[12], '\x50'])

        self.decryptor = Process(target=decryptor,
                                 args=[self.decryption_key,
                                       self.input_queue,
                                       self.output_queue, False])
        self.decryptor.daemon = True
        self.decryptor.start()

    def acquire_data(self, duration):
        """Acquire data from the EPOC headset."""

        # Delete previous buffer
        del self.buffer

        total_samples = duration * self.sampling_rate
        while self.output_queue.qsize() != total_samples:
            # Fetch new data
            try:
                self.input_queue.put(self.endpoint.read(32))
            except usb.USBError as usb_exception:
                if usb_exception.errno == 110:
                    raise EPOCTurnedOffError(
                        "Make sure that headset is turned on")
                else:
                    raise EPOCUSBError("USB I/O error with errno = %d" %
                                       usb_exception.errno)

        # Process and return the final data
        self.output_queue.join()

        # +1 for sequence numbers
        self.buffer = np.zeros((len(self.channel_mask)+1, self.output_queue.qsize()))
        for spl in xrange(self.output_queue.qsize()):
            bits = self.output_queue.get()
            self.buffer[0, spl] = bits[self.slices["SEQ#"]].uint
            for index, ch_name in enumerate(self.channel_mask):
                # ch_name's are strings like "O1", "O2", etc.
                self.buffer[index + 1, spl] = bits[self.slices[ch_name]].uint

        return self.buffer

    def save_as_matlab(self, filename):
        """Save acquired data as matlab file."""
        if self.buffer:
            # Save as matlab data with channel annotations
            matlab_data = {"SEQ": self.buffer[0]}
            for index, ch_name in enumerate(self.channel_mask):
                matlab_data[ch_name] = self.buffer[index + 1]
                savemat("%s.mat" % filename, matlab_data, oned_as='row')

    def get_quality(self, electrode):
        "Return contact quality for the specified electrode."""
        return self.quality.get(electrode, None)

    def disconnect(self):
        """Release the claimed interface."""
        if self.method == "libusb":
            for interf in self.device.get_active_configuration():
                usb.util.release_interface(
                    self.device, interf.bInterfaceNumber)
        elif self.method == "hidraw":
            os.close(self.endpoint)


def main():
    """Test function for EPOC class."""
    epoc = EPOC(method="hidraw")

    epoc.set_channel_mask(["O1", "O2"])

    eeg_rest = epoc.acquire_data(4)
    epoc.save_as_matlab("eeg-resting")

    # FIXME: Start flickering

    eeg_ssvep = epoc.acquire_data(4)
    epoc.save_as_matlab("eeg-ssvep")

    print "Packets dropped: %d" % utils.check_packet_drops(eeg_rest[0, :])
    print "Packets dropped: %d" % utils.check_packet_drops(eeg_ssvep[0, :])

if __name__ == "__main__":
    import sys
    sys.exit(main())
