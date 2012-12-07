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

import usb.core
import usb.util


class EmotivEPOC(object):
    def __init__(self, serialNumber=None):
        # Apparently these can change from dongle to dongle
        # so leave this just for reference
        # self.EPOC_VID = 0x1234
        # self.EPOC_PID = 0xED02

        # These seem to be the same for every device
        self.INTERFACE_DESC = "Emotiv RAW DATA"
        self.MANUFACTURER_DESC = "Emotiv Systems Pty Ltd"
        
        # One can want to specify the dongle with its serial
        self.serial = serialNumber

    def _is_emotiv_epoc(self, device):
        """Custom match function for libusb."""
        manu = usb.util.get_string(device, len(self.MANUFACTURER_DESC),
                                   device.iManufacturer)
        if manu == self.MANUFACTURER_DESC:
            # Found a dongle, check for interface class 3
            for interf in device.get_active_configuration():
                ifStr = usb.util.get_string(device, len(self.INTERFACE_DESC),
                                            interf.iInterface)
                if ifStr == self.INTERFACE_DESC:
                    return True

    def enumerate(self):
        self.devices = usb.core.find(find_all=True,
                custom_match=self._is_emotiv_epoc)

    def connect(self):
        pass

    def waitForContact(self):
        pass

    def getContactQuality(self):
        pass

    def getBatteryLevel(self):
        pass

    def getData(self):
        pass

    def disconnect(self):
        pass
