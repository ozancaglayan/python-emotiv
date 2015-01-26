Emotiv EPOC Python Interface
============================

Unmaintained as of January 2015
-------------

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
* BeagleBone Black GPIO (For SSVEP BCI in examples/)

[labstreaminglayer](https://code.google.com/p/labstreaminglayer)
================================================================

"labstreaminglayer is a system for the unified collection of measurement time series
in research experiments and handles both the networking, time-synchronization,
(near-) real-time access as well as optionally the centralized collection,
viewing and disk recording of the data."

python-emotiv has preliminary support in lsl/ folder to stream Emotiv EEG signals to
labstreaminglayer nodes.

Saving your data
================

utils.py contains a save_as_matlab() function to export the acquired signals
as a MATLAB file. This function saves the EEG data according to the
[FieldTrip](http://fieldtrip.fcdonders.nl)
specification to ease the process of analysing signals with FieldTrip.

Installation
============

Just run ```python setup.py install``` to install the module on your system.

Testing
=======

When you run emotiv/epoc.py as a standalone application, it will dump sensor data
to the terminal:

![Terminal screenshot](https://raw.github.com/ozancaglayan/python-emotiv/master/doc/sc_console.png)

Authors
=======

Ozan Çağlayan, Galatasaray University, Computer Engineering Dept.
