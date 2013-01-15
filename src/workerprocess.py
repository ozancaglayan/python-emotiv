#!/usr/bin/env python

import os
import sys
import time
from multiprocessing import Pool, Queue, Process, JoinableQueue
from multiprocessing.managers import BaseManager

from Crypto.Cipher import AES
from bitstring import BitArray


key = bytes("1234567998654321")
cipher = AES.new(key)


def worker(input_queue, output_queue):
    while 1:
        item = input_queue.get()
        dec = cipher.decrypt(item)
        bit = BitArray(bytes=dec)
        output_queue.put(bit)

        input_queue.task_done()

def main():
    input_queue = JoinableQueue()
    output_queue = Queue()

    proc = Process(target=worker, args=[input_queue, output_queue])
    proc.daemon = True
    proc.start()

    i = 0

    while i < 128:
        raw = os.urandom(32)
        input_queue.put(raw)

        time.sleep(1/128.)
        i += 1

    for i in range(output_queue.qsize()):
        ba = output_queue.get()
        print ba[0:8].uint


if __name__ == '__main__':
    sys.exit(main())
