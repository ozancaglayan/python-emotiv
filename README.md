Emotiv EPOC Python Interface
============================

python-emotiv is an open-source library to acquire data from Emotiv EPOC headset.
Although Emotiv recently provided 32-bit SDK for Linux, we have chosen
to use the reverse-engineered protocol as the code will be finally deployed
on a Raspberry Pi or BeagleBone Black ARM box.

The library uses libusb to detect and access the dongle instead of hidapi. The
udev rules create a /dev/emotiv\_epoc symlink in /dev tree, if you want to
directly read from that node, pass method="direct" when you create your EPOC
object.

Parts of the project are inspired from
[mushu](https://github.com/venthur/mushu) and
[emokit](https://github.com/openyou/emokit) which is the pioneer of the
reverse-engineered protocol.

Dependencies
============

* [pyusb](http://sourceforge.net/projects/pyusb) (Version >= 1.0)
* [pycrypto](https://www.dlitz.net/software/pycrypto)
* numpy
* scipy
* matplotlib (For data analysis scripts under utils/)
* RPi GPIO (For SSVEP BCI in examples/)

Installation
============

Just run ```python setup.py install``` to install the module on your system.

Data Logger
==========

When you run emotiv/epoc.py as a standalone application, it will dump sensor data
to the terminal:

![Terminal screenshot](https://raw.github.com/ozancaglayan/python-emotiv/master/doc/sc_console.png)

Authors
=======

Ozan Çağlayan, Galatasaray University, Computer Engineering Dept.
