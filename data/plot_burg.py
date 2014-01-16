# -*- coding: utf-8 -*-

from scipy import signal
from scipy.io import loadmat
import spectrum

from matplotlib import pylab as pl
import numpy as np

import sys

if __name__ == "__main__":
    d = loadmat(sys.argv[1])
    o1 = signal.detrend(d['raw'][0])
    o2 = signal.detrend(d['raw'][1])

    diff = o1 - o2
    avg = (o1 + o2) / 2.0

    data_labels = ["O1", "O2", "O1-O2", "(O1+O2)/2"]
    datas = [o1, o2, diff, avg]

    fig, axs = pl.subplots(nrows=1, ncols=4, sharey=True)
    time = d['data']['time'][0][0][0][0]

    for i in range(4):
        psd = spectrum.pburg(datas[i], order=8, NFFT=256, sampling=128.0)
        psd.run()
        p = 10 * np.log10(psd.get_converted_psd('onesided'))
        axs[i].set_title(data_labels[i])
        axs[i].plot(psd.frequencies(), p)

    pl.show()
