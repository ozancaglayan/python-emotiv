#!/usr/bin/env python

import matplotlib
import numpy as np
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from Emotiv import EmotivEPOC, EmotivEPOCNotFoundException

class Scope:
    def __init__(self, ax, maxt=2, dt=0.02):
        self.ax = ax
        self.dt = dt
        self.maxt = maxt
        self.tdata = [0]
        self.ydata = [0]
        self.line = Line2D(self.tdata, self.ydata)
        self.ax.add_line(self.line)
        self.ax.set_ylim(-127, 128)
        self.ax.set_xlim(0, self.maxt)

    def update(self, y):
        lastt = self.tdata[-1]
        if lastt > self.tdata[0] + self.maxt: # reset the arrays
            self.tdata = [self.tdata[-1]]
            self.ydata = [self.ydata[-1]]
            self.ax.set_xlim(self.tdata[0], self.tdata[0] + self.maxt)
            self.ax.figure.canvas.draw()

        t = self.tdata[-1] + self.dt
        self.tdata.append(t)
        self.ydata.append(y)
        self.line.set_data(self.tdata, self.ydata)
        return self.line,

if __name__ == '__main__':
    emotiv = EmotivEPOC()
    try:
        emotiv.enumerate()
    except EmotivEPOCNotFoundException, e:
        if emotiv.permissionProblem:
            print("Please make sure that device permissions are handled.")
        else:
            print("Please make sure that device permissions are handled or"\
                    " at least 1 Emotiv EPOC dongle is plugged.")
        sys.exit(1)

    for k,v in emotiv.devices.iteritems():
        print("Found dongle with S/N: %s" % k)

    emotiv.setupEncryption()

    fig = plt.figure()
    ax = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    scope = Scope(ax)
    scope2 = Scope(ax2)
    # pass a generator in "emitter" to produce data for the update func
    ani = animation.FuncAnimation(fig, scope.update, emotiv.getGyroX, interval=10,
        blit=True)
    ani2 = animation.FuncAnimation(fig, scope2.update, emotiv.getGyroY, interval=10,
        blit=True)
    plt.show()
