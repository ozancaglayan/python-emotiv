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

import sys

try:
    from emotiv import epoc
except ImportError:
    sys.path.insert(0, "..")
    from emotiv import epoc

def main():
    # Setup headset
    headset = epoc.EPOC()

    try:
        d = headset.get_sample()
        prev_ctr = headset.counter
        while 1:
            d = headset.get_sample()
            ctr = headset.counter
            if (prev_ctr + 1) % 129 != ctr:
                print "Dropped packets between %d and %d" % (prev_ctr, ctr)
            prev_ctr = ctr
    except:
        headset.disconnect()
        return 0

if __name__ == "__main__":
    sys.exit(main())
