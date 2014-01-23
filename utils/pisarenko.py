import pylab
import numpy
PI = numpy.pi


def covariance(x, k):
    N = len(x) - k
    return (x[:-k] * x[k:]).sum() / N


def phd1(x):
    """
    Estimate frequency using Pisarenko Harmonic Decomposition.
    It returns frequency `omega` in the unit radian/steps.
    If `x[n] = cos(omega*n+phi)` then it returns an estimat of `omega`.
    Note that mean of `x` must be 0.
    See equation (6) from [Kenneth W. K. Lui and H. C. So]_.

    .. [Kenneth W. K. Lui and H. C. So] An Unbiased Pisarenko Harmonic
       Decomposition Estimator For Single-Tone Frequency,
       http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.75.4859
    """
    r1 = covariance(x, 1)
    r2 = covariance(x, 2)
    a = (r2 + numpy.sqrt(r2 ** 2 + 8 * r1 ** 2)) / 4 / r1
    if a > 1:  # error should be raised?
        a = 1
    elif a < -1:
        a = -1
    return numpy.arccos(a)


def freq(x, sample_step=1, dt=1.0):
    """Estimate frequency using `phd1`"""
    omega = phd1(x[::sample_step])
    return omega / 2.0 / PI / sample_step / dt


def plot_x_and_psd_with_estimated_omega(x, sample_step=1, dt=1.0):
    y = x[::sample_step]
    F = freq(x, sample_step, dt)
    T = 1.0 / F

    pylab.clf()

    # plot PSD
    pylab.subplot(211)
    pylab.psd(y, Fs=1.0 / sample_step / dt)
    ylim = pylab.ylim()
    pylab.vlines(F, *ylim)
    pylab.ylim(ylim)

    # plot time series
    pylab.subplot(223)
    pylab.plot(x)

    # plot time series (three cycles)
    n = int(T / dt) * 3
    m = n // sample_step
    pylab.subplot(224)
    pylab.plot(x[:n])
    pylab.plot(numpy.arange(0, n, sample_step)[:m], y[:m], 'o')

    pylab.suptitle('F = %s' % F)


if __name__ == '__main__':
    F = 0.01
    num = int(1.0 / F) * 50
    n = numpy.arange(num)
    x = numpy.sin(2 * PI * F * n)
    x += numpy.random.randn(len(x)) * 0.1
    # NB: here, theoretically x.mean() == 0
    sample_step = 20

    plot_x_and_psd_with_estimated_omega(x, sample_step)
    pylab.show()
