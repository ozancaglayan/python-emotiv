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

from multiprocessing import Queue

from bitstring import BitArray
from Crypto.Cipher import AES

def decryptionProcess(aes_key, input_queue, output_queue):
    # Setup decryption cipher
    cipher = AES.new(aes_key)
    cold_start = True
    while 1:
        encrypted_packet = input_queue.get()
        decrypted_packet = cipher.decrypt(encrypted_packet)
        bits = BitArray(bytes=decrypted_packet)
        # Skip until packet with seq number 0
        if cold_start and bits[0:8].uint != 0:
            pass
        # Discard battery packets for now
        elif not bits[0]:
            cold_start = False
            output_queue.put(bits)
        input_queue.task_done()
