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

from Crypto.Cipher import AES

import usb.core
import usb.util

import numpy as np

import utils


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
    # Used by the old BitArray logic.
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

    # emokit-style bit indexes to use with utils.get_level()
    bit_indexes = {
        'F3': [10, 11, 12, 13, 14, 15, 0, 1, 2, 3, 4, 5, 6, 7],
        'FC5': [28, 29, 30, 31, 16, 17, 18, 19, 20, 21, 22, 23, 8, 9],
        'AF3': [46, 47, 32, 33, 34, 35, 36, 37, 38, 39, 24, 25, 26, 27],
        'F7': [48, 49, 50, 51, 52, 53, 54, 55, 40, 41, 42, 43, 44, 45],
        'T7': [66, 67, 68, 69, 70, 71, 56, 57, 58, 59, 60, 61, 62, 63],
        'P7': [84, 85, 86, 87, 72, 73, 74, 75, 76, 77, 78, 79, 64, 65],
        'O1': [102, 103, 88, 89, 90, 91, 92, 93, 94, 95, 80, 81, 82, 83],
        'O2': [140, 141, 142, 143, 128, 129, 130, 131, 132, 133, 134, 135, 120, 121],
        'P8': [158, 159, 144, 145, 146, 147, 148, 149, 150, 151, 136, 137, 138, 139],
        'T8': [160, 161, 162, 163, 164, 165, 166, 167, 152, 153, 154, 155, 156, 157],
        'F8': [178, 179, 180, 181, 182, 183, 168, 169, 170, 171, 172, 173, 174, 175],
        'AF4': [196, 197, 198, 199, 184, 185, 186, 187, 188, 189, 190, 191, 176, 177],
        'FC6': [214, 215, 200, 201, 202, 203, 204, 205, 206, 207, 192, 193, 194, 195],
        'F4': [216, 217, 218, 219, 220, 221, 222, 223, 208, 209, 210, 211, 212, 213],
        'QU': [99,100,101,102,103,104,105,106,107,108,109,110,111,112],
    }

    def __init__(self, method="libusb", serial_number=None, enable_gyro=True):
        self.vendor_id = None
        self.product_id = None
        self.decryption = None
        self.decryption_key = None
        self.headset_on = False
        self.enable_gyro = enable_gyro
        self.battery = 0
        self.counter = 0
        self.gyroX = 0
        self.gyroY = 0

        # Access method can be direct/libusb/dummy (Default: libusb)
        # If dummy is given the class behaves as a random signal generator
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

        # Enumerate the bus to find EPOC devices
        self.enumerate()

    def _is_epoc(self, device):
        """Custom match function for libusb."""
        try:
            manu = usb.util.get_string(device, len(self.MANUFACTURER_DESC),
                                       device.iManufacturer)
        except usb.core.USBError, usb_exception:
            # If the udev rule is installed, we shouldn't get an exception
            # for Emotiv device.
            return False
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
        if self.method == "dummy":
            self.endpoint = open("/dev/urandom")
            self.get_sample = self.__get_sample_dummy
            return

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
                # Last interface is the one we need
                for interface in dev.get_active_configuration():
                    if dev.is_kernel_driver_active(interface.bInterfaceNumber):
                        # Detach kernel drivers and claim through libusb
                        dev.detach_kernel_driver(interface.bInterfaceNumber)
                        usb.util.claim_interface(dev, interface.bInterfaceNumber)

                self.device = dev
                self.endpoint = usb.util.find_descriptor(
                    interface, bEndpointAddress=usb.ENDPOINT_IN | 2)
            elif self.method == "direct":
                if os.path.exists("/dev/emotiv_epoc"):
                    self.endpoint = open("/dev/emotiv_epoc")
                else:
                    raise EPOCDeviceNodeNotFoundError(
                        "/dev/emotiv_epoc doesn't exist.")

            # Return the first Emotiv headset by default
            break

        self.setup_encryption()
        # Attempt to see whether the headset is turned on
        try:
            self.endpoint.read(32, 100)
        except usb.USBError as ue:
            if ue.errno == 110:
                self.headset_on = False
                print "Setup is OK but make sure that headset is turned on."
        else:
            self.headset_on = True

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

        self._cipher = AES.new(self.decryption_key)

    def set_external_decryption(self):
        """Use another process for concurrent decryption."""
        self.decryption = Process(target=decryptionProcess,
                                  args=[self._cipher,
                                        self.input_queue,
                                        self.output_queue, False])
        self.decryption.daemon = True
        self.decryption.start()

    def __get_sample_dummy(self):
        """Read random dummy samples."""
        raw_data = self.endpoint.read(32)
        return [utils.get_level(raw_data, self.bit_indexes[n]) for n in self.channel_mask]

    def get_sample(self):
        """Returns an array of EEG samples."""
        try:
            raw_data = self._cipher.decrypt(self.endpoint.read(32))
            # Parse counter
            ctr = ord(raw_data[0])
            # Update gyro's if requested
            if self.enable_gyro:
                self.gyroX = ((ord(raw_data[29]) << 4) | (ord(raw_data[31]) >> 4))
                self.gyroY = ((ord(raw_data[30]) << 4) | (ord(raw_data[31]) & 0x0F))
            if ctr < 128:
                self.counter = ctr
                # Contact qualities
                self.quality[self.cq_order[ctr]] = utils.get_level(raw_data, self.bit_indexes["QU"]) / 540.0
                # Finally EEG data
                return [utils.get_level(raw_data, self.bit_indexes[n]) for n in self.channel_mask]
            else:
                # Set a synthetic counter for this special packet: 128
                self.counter = 128
                # Parse battery level
                self.battery = self.battery_levels[ctr]
                return []
        except usb.USBError as usb_exception:
            if usb_exception.errno == 110:
                self.headset_on = False
                raise EPOCTurnedOffError(
                        "Make sure that headset is turned on")
            else:
                raise EPOCUSBError("USB I/O error with errno = %d" %
                        usb_exception.errno)

    def acquire_data(self, duration):
        """Acquire data from the EPOC headset."""

        total_samples = duration * self.sampling_rate
        _buffer = np.ndarray((total_samples, len(self.channel_mask) + 1),
                dtype=np.uint16)
        ctr = 0
        while ctr < total_samples:
            # Fetch new data
            data = self.get_sample()
            if data:
                # Prepend sequence numbers
                _buffer[ctr] = np.insert(np.array(data), 0, self.counter)
                ctr += 1

        return _buffer

    def get_quality(self, electrode):
        "Return contact quality for the specified electrode."""
        return self.quality.get(electrode, None)

    def disconnect(self):
        """Release the claimed interface."""
        if self.method == "libusb":
            for interf in self.device.get_active_configuration():
                usb.util.release_interface(
                    self.device, interf.bInterfaceNumber)
        else:
            self.endpoint.close()


def main():
    """Test function for EPOC class."""
    e = EPOC()

    while 1:
        try:
            data = e.get_sample()
            # data is [] for each battery packet, e.g. ctr > 127
            if data:
                # Clear screen
                print("\x1b[2J\x1b[H")
                header = "Emotiv Data Packet [%3d/128] [Loss: N/A] [Battery: %2d(%%)]" % (
                    e.counter, e.battery)
                print "%s\n%s" % (header, '-'*len(header))

                print "%10s: %5d" % ("Gyro(x)", e.gyroX)
                print "%10s: %5d" % ("Gyro(y)", e.gyroY)

                for i,channel in enumerate(e.channel_mask):
                    print "%10s: %5d %20s: %.2f" % (channel, data[i], "Quality", e.quality[channel])
        except EPOCTurnedOffError, ete:
            print ete
        except KeyboardInterrupt, ki:
            e.disconnect()
            return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
