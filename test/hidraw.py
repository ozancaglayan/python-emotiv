import os
import sys
import time

from bitstring import BitArray
from Crypto.Cipher import AES

if __name__ == "__main__":
    fd = open(sys.argv[1])
    aes_key = '9\x005T4\x100B9\x005H4\x000P'
    cipher = AES.new(aes_key)
    duration = int(sys.argv[2]) * 128
    c = -1
    t = []
    while len(t) != duration:
        st = time.time()
        data = fd.read(32)
        t.append(time.time() - st)
        if data:
            raw = cipher.decrypt(data)
            bits = BitArray(bytes=cipher.decrypt(data))
            if not bits[0]:
                if c == -1:
                    c = bits[0:8].uint
                else:
                    nc = bits[0:8].uint
                    print "[%d] took %.2f" % (nc, t[-1]*1000)
                    d = nc - c
                    if d != 1 and d != -127:
                        print "Loss! prev: %d, next: %d" % (c, nc)
                    c = nc
            else:
                print "battery: %.2f" % (1000*t.pop())
        else:
            print "no data!"
    fd.close()
    print "Total: %.4f\nMean: %.4f\nMin: %.4f\nMax: %.4f" % (len(t)/128.0,
                                                             sum(t)/len(t),
                                                             min(t)*1000,
                                                             max(t)*1000)


