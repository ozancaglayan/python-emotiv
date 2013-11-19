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
import time

# Switching periods for led
t1 = 1 / (18 * 2.0)
t2 = 1 / (19 * 2.0)

led1 = 0
led2 = 0

prev1 = prev2 = 0

def blink():
    global prev1, prev2, led1, led2
    tic = time.time()
    if prev1 + t1 <= tic:
        led1 = led1 ^ 1
        # FIXME: Drive GPIO
        prev1 = time.time()
    if prev2 + t2 <= tic:
        led2 = led2 ^ 1
        # FIXME: Drive GPIO
        prev2 = time.time()


def main():

    global prev1, prev2
    prev1 = prev2 = time.time()
    # FIXME: Drive GPIO (initial)
    while 1:
        blink()

if __name__ == "__main__":
    sys.exit(main())
