#!/usr/bin/env python
# encoding: utf-8

from distutils.core import setup

VERSION = "0.1"

setup(
        name="python-emotiv",
        version=VERSION,
        author="Ozan Çağlayan",
        author_email="ozancag@gmail.com",
        packages=["emotiv"],
        data_files=[('/etc/udev/rules.d', ['udev/99-emotiv-epoc.rules'])],
        #scripts
        url="http://github.com/ozancaglayan/python-emotiv",
        license="COPYING",
        description="Python library to access Emotiv EPOC EEG headset data",
     )
