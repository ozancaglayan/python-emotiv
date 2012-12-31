Emotiv EPOC Python Interface
============================

This is a BCI project using the Emotiv EPOC neuro headset.
Although Emotiv recently provided 32-bit SDK for Linux, we have chosen
to use the reverse-engineered protocol as the code will be finally deployed
on a raspberry-pi ARM box.

Parts of the project are inspired from
[mushu](https://github.com/venthur/mushu) and
[emokit](https://github.com/openyou/emokit) which is the pioneer of the
reverse-engineered protocol.

Dependencies
============

* [pyusb](http://sourceforge.net/projects/pyusb) (Version >= 1.0)
* [pycrypto](https://www.dlitz.net/software/pycrypto)
* [python-bitstring](http://code.google.com/p/python-bitstring)
* numpy
* matplotlib
* scipy (in the future)

Installation
============

Copy the relevant udev rule under /etc/udev/rules.d before plugging the EPOC
dongle for being able to run this as a non-root user.

Usage
=====

You do not need to put the headset or mount the dry electrodes in order to
acquire gyroscope data.

Screenshot
==========

When you run Emotiv.py, it will update what it gets from your headset
and output the data once in a second on your terminal:

![Terminal screenshot](https://raw.github.com/ozancaglayan/EmotivBCI/master/doc/sc_console.png)

Authors
=======

Ozan Çağlayan
Galatasaray University, Computer Engineering Dept.
