import numpy as np
from scipy import fftpack
import pylab as pl

#time_step = 0.02
#time_vec = np.arange(0, 20, time_step)
#np.random.seed(1234)
#period = 5.
#sig = np.sin(2 * np.pi / period * time_vec) + \
#      0.5 * np.random.randn(time_vec.size)
#

sig = np.genfromtxt("ssvep-10Hz-7.5Hz.txt")
time_step = 1/200.0

sample_freq = fftpack.fftfreq(sig.size, d=time_step)
sig_fft = fftpack.fft(sig)
pidxs = np.where(sample_freq > 0)
freqs, power = sample_freq[pidxs], np.abs(sig_fft)[pidxs]
freq = freqs[power.argmax()]

pl.figure()
pl.plot(freqs, power)
pl.xlabel('Frequency [Hz]')
pl.ylabel('plower')
axes = pl.axes([0.3, 0.3, 0.5, 0.5])
pl.title('Peak frequency')
pl.plot(freqs[:8], power[:8])
pl.setp(axes, yticks=[])
pl.show()
