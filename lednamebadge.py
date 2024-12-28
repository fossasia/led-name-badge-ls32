#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
#
# (C) 2019 juergen@fabmail.org
#
# This is an upload tool for e.g.
# https://www.sertronics-shop.de/computer/pc-peripheriegeraete/usb-gadgets/led-name-tag-11x44-pixel-usb
# The font_11x44[] data was downloaded from such a device.
#
# Ubuntu install:
# ---------------
#  sudo apt-get install python3-usb
#
# Optional for image support:
#  sudo apt-get install python3-pil
#
# Windows install:
# ----------------
# For Windows, we need to set up the libusb API for the LED badge device.
# The way described here, uses [libusb-win32](https://github.com/mcuee/libusb-win32/wiki)
# in a quite low level way and in a quite old version:
#
# - Please use version 1.2.6.0 of 'libusb-win32`. It's still available on the
#   [old project repo on SourceForge](https://sourceforge.net/projects/libusb-win32/files/libusb-win32-releases/1.2.6.0/)
# - Then
#     - Extract the downloaded zip file and go to the directory `libusb-win32-bin-1.2.6.0\bin`
#     - Right click on `inf-wizard.exe` and `Run as Administrator`
#     - `Next` -> Select `0x0416 0x5020 LS32 Custm HID` (or similar with the same IDs)
#     - `Next` -> `Next` -> Save as dialog `LS32_Sustm_HID.inf` -> `Save` (just to proceed, we don't need that file)
#     - `Install Now...` -> Driver Install Complete -> `OK`
#
# There are other - meanwhile recommended, but untested here - ways to install and setup
# newer versions of `libusb-win32`: use
# [Zadig](https://zadig.akeo.ie/) (it is also available from the old libusb-win32 repo on
# [GitHub repo](https://github.com/mcuee/libusb-win32/releases) of newer releases)
# or [libusbK](https://libusbk.sourceforge.net/UsbK3/index.html)
#
# Of course, Python is needed:
#
# - Download latest python from [python.org](https://www.python.org/downloads/),
# or specific versions from [here](https://www.python.org/downloads/windows/)
#     - Checkmark the following options
#         - `[x]` install Launcher for all Users
#         - `[x]` Add Python X.Y to PATH
#     - Click the `Install Now ...` text message.
#     - Optionally click on the 'Disable path length limit' text message. This is always a good thing to do.
#
# Install needed the Python packages. On some systems (esp. those with Python 2
# *and* 3 installed), you have to address Python 3 explicitly by using the
# command `pip3` instead of `pip`.
#
# - Run cmd.exe as Administrator, enter:
#
#         pip install pyusb
#         pip install pillow

#
# v0.1, 2019-03-05, jw  initial draught. HID code is much simpler than expected.
# v0.2, 2019-03-07, jw  support for loading bitmaps added.
# v0.3              jw  option -p to preload graphics for inline use in text.
# v0.4, 2019-03-08, jw  Warning about unused images added. Examples added to the README.
# v0.5,             jw  Deprecated -p and CTRL-characters. We now use embedding within colons(:)
#                       Added builtin icons and -l to list them.
# v0.6, 2019-03-14, jw  Added --mode-help with hints and example for making animations.
#                       Options -b --blink, -a --ants added. Removed -p from usage.
# v0.7, 2019-05-20, jw  Support pyhidapi, fallback to usb.core. Added python2 compatibility.
# v0.8, 2019-05-23, jw  Support usb.core on windows via libusb-win32
# v0.9, 2019-07-17, jw  Support 48x12 configuration too.
# v0.10, 2019-09-09, jw Support for loading monochrome images. Typos fixed.
# v0.11, 2019-09-29, jw New option --brightness added.
# v0.12, 2019-12-27, jw hint at pip3 -- as discussed in https://github.com/jnweiger/led-name-badge-ls32/issues/19
# v0.13, 2023-11-14, bs modularization.
#     Some comments about this big change:
#     * I wanted to keep this one-python-file-for-complete-command-line-usage, but also needed to introduce importable
#       classes for writing own content to the device (my upcoming GUI editor). Therefore, the file was renamed to an
#       importable python file, and forwarding python files are introduced with the old file names for full
#       compatibility.
#     * A bit of code rearranging and cleanup was necessary for that goal, but I hope the original parts are still
#       recognizable, as I tried to keep all this refactoring as less, as possible and sense-making, but did not do
#       the full clean-codish refactoring. Keeping the classes in one file is part of that refactoring-omittance.
#     * There is some initialization code executed in the classes not needed, if not imported. This is nagging me
#       somehow, but it is acceptable, as we do not need to save every processor cycle, here :)
#     * Have fun!
# v0.14, 2024-06-02, bs extending write methods.
#     * Preparation for further or updated write methods, like bluetooth.
#     * Automatic or manual write method and device selection, See -M and -D (substituting -H) resp.
#       get_available_methods() and get_available_device_ids().


import argparse
import os
import re
import sys
import time
from array import array
from datetime import datetime


__version = "0.14"


class SimpleTextAndIcons:
    font_11x44 = (
        # 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        0x00, 0x38, 0x6c, 0xc6, 0xc6, 0xfe, 0xc6, 0xc6, 0xc6, 0xc6, 0x00,
        0x00, 0xfc, 0x66, 0x66, 0x66, 0x7c, 0x66, 0x66, 0x66, 0xfc, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0xc0, 0xc0, 0xc0, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0xfc, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0xfc, 0x00,
        0x00, 0xfe, 0x66, 0x62, 0x68, 0x78, 0x68, 0x62, 0x66, 0xfe, 0x00,
        0x00, 0xfe, 0x66, 0x62, 0x68, 0x78, 0x68, 0x60, 0x60, 0xf0, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0xc0, 0xc0, 0xce, 0xc6, 0xc6, 0x7e, 0x00,
        0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xfe, 0xc6, 0xc6, 0xc6, 0xc6, 0x00,
        0x00, 0x3c, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x00,
        0x00, 0x1e, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0xcc, 0xcc, 0x78, 0x00,
        0x00, 0xe6, 0x66, 0x6c, 0x6c, 0x78, 0x6c, 0x6c, 0x66, 0xe6, 0x00,
        0x00, 0xf0, 0x60, 0x60, 0x60, 0x60, 0x60, 0x62, 0x66, 0xfe, 0x00,
        0x00, 0x82, 0xc6, 0xee, 0xfe, 0xd6, 0xc6, 0xc6, 0xc6, 0xc6, 0x00,
        0x00, 0x86, 0xc6, 0xe6, 0xf6, 0xde, 0xce, 0xc6, 0xc6, 0xc6, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0xfc, 0x66, 0x66, 0x66, 0x7c, 0x60, 0x60, 0x60, 0xf0, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xd6, 0xde, 0x7c, 0x06,
        0x00, 0xfc, 0x66, 0x66, 0x66, 0x7c, 0x6c, 0x66, 0x66, 0xe6, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0x60, 0x38, 0x0c, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x7e, 0x7e, 0x5a, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x00,
        0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x6c, 0x38, 0x10, 0x00,
        0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xd6, 0xfe, 0xee, 0xc6, 0x82, 0x00,
        0x00, 0xc6, 0xc6, 0x6c, 0x7c, 0x38, 0x7c, 0x6c, 0xc6, 0xc6, 0x00,
        0x00, 0x66, 0x66, 0x66, 0x66, 0x3c, 0x18, 0x18, 0x18, 0x3c, 0x00,
        0x00, 0xfe, 0xc6, 0x86, 0x0c, 0x18, 0x30, 0x62, 0xc6, 0xfe, 0x00,

        # 'abcdefghijklmnopqrstuvwxyz'
        0x00, 0x00, 0x00, 0x00, 0x78, 0x0c, 0x7c, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0xe0, 0x60, 0x60, 0x7c, 0x66, 0x66, 0x66, 0x66, 0x7c, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x7c, 0xc6, 0xc0, 0xc0, 0xc6, 0x7c, 0x00,
        0x00, 0x1c, 0x0c, 0x0c, 0x7c, 0xcc, 0xcc, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x7c, 0xc6, 0xfe, 0xc0, 0xc6, 0x7c, 0x00,
        0x00, 0x1c, 0x36, 0x30, 0x78, 0x30, 0x30, 0x30, 0x30, 0x78, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x76, 0xcc, 0xcc, 0x7c, 0x0c, 0xcc, 0x78,
        0x00, 0xe0, 0x60, 0x60, 0x6c, 0x76, 0x66, 0x66, 0x66, 0xe6, 0x00,
        0x00, 0x18, 0x18, 0x00, 0x38, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x00,
        0x0c, 0x0c, 0x00, 0x1c, 0x0c, 0x0c, 0x0c, 0x0c, 0xcc, 0xcc, 0x78,
        0x00, 0xe0, 0x60, 0x60, 0x66, 0x6c, 0x78, 0x78, 0x6c, 0xe6, 0x00,
        0x00, 0x38, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xec, 0xfe, 0xd6, 0xd6, 0xd6, 0xc6, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xdc, 0x66, 0x66, 0x66, 0x66, 0x66, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xdc, 0x66, 0x66, 0x7c, 0x60, 0x60, 0xf0,
        0x00, 0x00, 0x00, 0x00, 0x7c, 0xcc, 0xcc, 0x7c, 0x0c, 0x0c, 0x1e,
        0x00, 0x00, 0x00, 0x00, 0xde, 0x76, 0x60, 0x60, 0x60, 0xf0, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x7c, 0xc6, 0x70, 0x1c, 0xc6, 0x7c, 0x00,
        0x00, 0x10, 0x30, 0x30, 0xfc, 0x30, 0x30, 0x30, 0x34, 0x18, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xc6, 0xc6, 0xc6, 0x6c, 0x38, 0x10, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xc6, 0xd6, 0xd6, 0xd6, 0xfe, 0x6c, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xc6, 0x6c, 0x38, 0x38, 0x6c, 0xc6, 0x00,
        0x00, 0x00, 0x00, 0x00, 0xc6, 0xc6, 0xc6, 0x7e, 0x06, 0x0c, 0xf8,
        0x00, 0x00, 0x00, 0x00, 0xfe, 0x8c, 0x18, 0x30, 0x62, 0xfe, 0x00,

        # '0987654321^ !"\0$%&/()=?` °\\}][{'
        0x00, 0x7c, 0xc6, 0xce, 0xde, 0xf6, 0xe6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0x7e, 0x06, 0x06, 0xc6, 0x7c, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0x7c, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0xfe, 0xc6, 0x06, 0x0c, 0x18, 0x30, 0x30, 0x30, 0x30, 0x00,
        0x00, 0x7c, 0xc6, 0xc0, 0xc0, 0xfc, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0xfe, 0xc0, 0xc0, 0xfc, 0x06, 0x06, 0x06, 0xc6, 0x7c, 0x00,
        0x00, 0x0c, 0x1c, 0x3c, 0x6c, 0xcc, 0xfe, 0x0c, 0x0c, 0x1e, 0x00,
        0x00, 0x7c, 0xc6, 0x06, 0x06, 0x3c, 0x06, 0x06, 0xc6, 0x7c, 0x00,
        0x00, 0x7c, 0xc6, 0x06, 0x0c, 0x18, 0x30, 0x60, 0xc6, 0xfe, 0x00,
        0x00, 0x18, 0x38, 0x78, 0x18, 0x18, 0x18, 0x18, 0x18, 0x7e, 0x00,
        0x38, 0x6c, 0xc6, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x3c, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x18, 0x3c, 0x3c, 0x3c, 0x18, 0x18, 0x00, 0x18, 0x18, 0x00,
        0x66, 0x66, 0x22, 0x22, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x7c, 0x04, 0x14, 0x18, 0x10, 0x10, 0x20,
        0x10, 0x7c, 0xd6, 0xd6, 0x70, 0x1c, 0xd6, 0xd6, 0x7c, 0x10, 0x10,
        0x00, 0x60, 0x92, 0x96, 0x6c, 0x10, 0x6c, 0xd2, 0x92, 0x0c, 0x00,
        0x00, 0x38, 0x6c, 0x6c, 0x38, 0x76, 0xdc, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x00, 0x02, 0x06, 0x0c, 0x18, 0x30, 0x60, 0xc0, 0x80, 0x00,
        0x00, 0x0c, 0x18, 0x30, 0x30, 0x30, 0x30, 0x30, 0x18, 0x0c, 0x00,
        0x00, 0x30, 0x18, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x18, 0x30, 0x00,
        0x00, 0x00, 0x00, 0x7e, 0x00, 0x00, 0x7e, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x7c, 0xc6, 0xc6, 0x0c, 0x18, 0x18, 0x00, 0x18, 0x18, 0x00,
        0x18, 0x18, 0x10, 0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x7c, 0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x7c,
        0x00, 0x10, 0x28, 0x28, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x80, 0xc0, 0x60, 0x30, 0x18, 0x0c, 0x06, 0x02, 0x00, 0x00,
        0x00, 0x70, 0x18, 0x18, 0x18, 0x0e, 0x18, 0x18, 0x18, 0x70, 0x00,
        0x00, 0x3c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x3c, 0x00,
        0x00, 0x3c, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x30, 0x3c, 0x00,
        0x00, 0x0e, 0x18, 0x18, 0x18, 0x70, 0x18, 0x18, 0x18, 0x0e, 0x00,

        # "@ ~ |<>,;.:-_#'+* "
        0x00, 0x00, 0x3c, 0x42, 0x9d, 0xa5, 0xad, 0xb6, 0x40, 0x3c, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc0, 0xc0, 0x00, 0x00, 0x00,
        0x00, 0x76, 0xdc, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x08, 0x08, 0x7c, 0x08, 0x08, 0x18, 0x18, 0x28, 0x28, 0x48, 0x18,
        0x00, 0x18, 0x18, 0x18, 0x18, 0x00, 0x18, 0x18, 0x18, 0x18, 0x00,
        0x00, 0x06, 0x0c, 0x18, 0x30, 0x60, 0x30, 0x18, 0x0c, 0x06, 0x00,
        0x00, 0x60, 0x30, 0x18, 0x0c, 0x06, 0x0c, 0x18, 0x30, 0x60, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x30, 0x10, 0x20,
        0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x08, 0x10,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x30, 0x30, 0x00,
        0x00, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00, 0x18, 0x18, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff,
        0x00, 0x6c, 0x6c, 0xfe, 0x6c, 0x6c, 0xfe, 0x6c, 0x6c, 0x00, 0x00,
        0x18, 0x18, 0x08, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x18, 0x18, 0x7e, 0x18, 0x18, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x66, 0x3c, 0xff, 0x3c, 0x66, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

        # "äöüÄÖÜß"
        0x00, 0xcc, 0xcc, 0x00, 0x78, 0x0c, 0x7c, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0xc6, 0xc6, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0xcc, 0xcc, 0x00, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0x76, 0x00,
        0xc6, 0xc6, 0x38, 0x6c, 0xc6, 0xfe, 0xc6, 0xc6, 0xc6, 0xc6, 0x00,
        0xc6, 0xc6, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0xc6, 0xc6, 0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x3c, 0x66, 0x66, 0x66, 0x7c, 0x66, 0x66, 0x66, 0x6c, 0x60,

        # "àäòöùüèéêëôöûîïÿç"
        0x00, 0x60, 0x18, 0x00, 0x78, 0x0c, 0x7c, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x6c, 0x6c, 0x00, 0x78, 0x0c, 0x7c, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x60, 0x18, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x6c, 0x6c, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x60, 0x18, 0x00, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x6c, 0x6c, 0x00, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x60, 0x18, 0x00, 0x7c, 0xc6, 0xfe, 0xc0, 0xc6, 0x7c, 0x00,
        0x00, 0x18, 0x60, 0x00, 0x7c, 0xc6, 0xfe, 0xc0, 0xc6, 0x7c, 0x00,
        0x00, 0x10, 0x6c, 0x00, 0x7c, 0xc6, 0xfe, 0xc0, 0xc6, 0x7c, 0x00,
        0x00, 0x6c, 0x6c, 0x00, 0x7c, 0xc6, 0xfe, 0xc0, 0xc6, 0x7c, 0x00,
        0x00, 0x10, 0x6c, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x6c, 0x6c, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,
        0x00, 0x10, 0x6c, 0x00, 0xcc, 0xcc, 0xcc, 0xcc, 0xcc, 0x76, 0x00,
        0x00, 0x10, 0x6c, 0x00, 0x38, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x00,
        0x00, 0x6c, 0x6c, 0x00, 0x38, 0x18, 0x18, 0x18, 0x18, 0x3c, 0x00,
        0x00, 0x6c, 0x6c, 0x00, 0xc6, 0xc6, 0xc6, 0x7e, 0x06, 0x0c, 0xf8,
        0x00, 0x00, 0x00, 0x7c, 0xc6, 0xc0, 0xc0, 0xc6, 0x7c, 0x10, 0x30,

        # "ÀÅÄÉÈÊËÖÔÜÛÙŸ"
        0x60, 0x18, 0x38, 0x6c, 0xc6, 0xfe, 0xc6, 0xc6, 0xc6, 0xc6, 0x00,
        0x10, 0x6c, 0x38, 0x6c, 0xc6, 0xfe, 0xc6, 0xc6, 0xc6, 0xc6, 0x00,
        0x6c, 0x6c, 0x38, 0x6c, 0xc6, 0xfe, 0xc6, 0xc6, 0xc6, 0xc6, 0x00,
        0x18, 0x60, 0xfe, 0x62, 0x68, 0x78, 0x68, 0x62, 0x66, 0xfe, 0x00,
        0x60, 0x18, 0xfe, 0x62, 0x68, 0x78, 0x68, 0x62, 0x66, 0xfe, 0x00,
        0x10, 0x6c, 0xfe, 0x62, 0x68, 0x78, 0x68, 0x62, 0x66, 0xfe, 0x00,
        0x6c, 0x6c, 0xfe, 0x62, 0x68, 0x78, 0x68, 0x62, 0x66, 0xfe, 0x00,
        0x6c, 0x6c, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,  # Ö
        0x10, 0x6c, 0x00, 0x7c, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,  # Ô
        0x6c, 0x6c, 0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,  # Ü
        0x10, 0x6c, 0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,  # Û
        0x60, 0x18, 0x00, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0xc6, 0x7c, 0x00,  # Ù
        0x66, 0x66, 0x00, 0x66, 0x66, 0x66, 0x3c, 0x18, 0x18, 0x3c, 0x00,  # Ÿ
    )

    charmap = u'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + \
              u'abcdefghijklmnopqrstuvwxyz' + \
              u'0987654321^ !"\0$%&/()=?` °\\}][{' + \
              u"@ ~ |<>,;.:-_#'+* " + \
              u"äöüÄÖÜß" + \
              u"àäòöùüèéêëôöûîïÿç" + \
              u"ÀÅÄÉÈÊËÖÔÜÛÙŸ"

    char_offsets = {}
    for i in range(len(charmap)):
        char_offsets[charmap[i]] = 11 * i
        # print(i, charmap[i], char_offsets[charmap[i]])

    bitmap_named = {
        'ball':      (array('B', (
            0b00000000,
            0b00000000,
            0b00111100,
            0b01111110,
            0b11111111,
            0b11111111,
            0b11111111,
            0b11111111,
            0b01111110,
            0b00111100,
            0b00000000
        )), 1, '\x1e'),
        'happy':     (array('B', (
            0b00000000,  # 0x00
            0b00000000,  # 0x00
            0b00111100,  # 0x3c
            0b01000010,  # 0x42
            0b10100101,  # 0xa5
            0b10000001,  # 0x81
            0b10100101,  # 0xa5
            0b10011001,  # 0x99
            0b01000010,  # 0x42
            0b00111100,  # 0x3c
            0b00000000  # 0x00
        )), 1, '\x1d'),
        'happy2':    (array('B', (0x00, 0x08, 0x14, 0x08, 0x01, 0x00, 0x00, 0x61, 0x30, 0x1c, 0x07,
                                  0x00, 0x20, 0x50, 0x20, 0x00, 0x80, 0x80, 0x86, 0x0c, 0x38, 0xe0)), 2, '\x1c'),
        'heart':     (array('B', (0x00, 0x00, 0x6c, 0x92, 0x82, 0x82, 0x44, 0x28, 0x10, 0x00, 0x00)), 1, '\x1b'),
        'HEART':     (array('B', (0x00, 0x00, 0x6c, 0xfe, 0xfe, 0xfe, 0x7c, 0x38, 0x10, 0x00, 0x00)), 1, '\x1a'),
        'heart2':    (array('B', (0x00, 0x0c, 0x12, 0x21, 0x20, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01,
                                  0x00, 0x60, 0x90, 0x08, 0x08, 0x08, 0x10, 0x20, 0x40, 0x80, 0x00)), 2, '\x19'),
        'HEART2':    (array('B', (0x00, 0x0c, 0x1e, 0x3f, 0x3f, 0x3f, 0x1f, 0x0f, 0x07, 0x03, 0x01,
                                  0x00, 0x60, 0xf0, 0xf8, 0xf8, 0xf8, 0xf0, 0xe0, 0xc0, 0x80, 0x00)), 2, '\x18'),
        'fablab':    (array('B', (0x07, 0x0e, 0x1b, 0x03, 0x21, 0x2c, 0x2e, 0x26, 0x14, 0x1c, 0x06,
                                  0x80, 0x60, 0x30, 0x80, 0x88, 0x38, 0xe8, 0xc8, 0x10, 0x30, 0xc0)), 2, '\x17'),
        'bicycle':   (array('B', (0x01, 0x02, 0x00, 0x01, 0x07, 0x09, 0x12, 0x12, 0x10, 0x08, 0x07,
                                  0x00, 0x87, 0x81, 0x5f, 0x22, 0x94, 0x49, 0x5f, 0x49, 0x80, 0x00,
                                  0x00, 0x80, 0x00, 0x80, 0x70, 0xc8, 0x24, 0xe4, 0x04, 0x88, 0x70)), 3, '\x16'),
        'bicycle_r': (array('B', (0x00, 0x00, 0x00, 0x00, 0x07, 0x09, 0x12, 0x13, 0x10, 0x08, 0x07,
                                  0x00, 0xf0, 0x40, 0xfd, 0x22, 0x94, 0x49, 0xfd, 0x49, 0x80, 0x00,
                                  0x40, 0xa0, 0x80, 0x40, 0x70, 0xc8, 0x24, 0x24, 0x04, 0x88, 0x70)), 3, '\x15'),
        'owncloud':  (array('B', (0x00, 0x01, 0x02, 0x03, 0x06, 0x0c, 0x1a, 0x13, 0x11, 0x19, 0x0f,
                                  0x78, 0xcc, 0x87, 0xfc, 0x42, 0x81, 0x81, 0x81, 0x81, 0x43, 0xbd,
                                  0x00, 0x00, 0x00, 0x80, 0x80, 0xe0, 0x30, 0x10, 0x28, 0x28, 0xd0)), 3, '\x14'),
    }

    bitmap_builtin = {}
    for i in bitmap_named:
        bitmap_builtin[bitmap_named[i][2]] = bitmap_named[i]

    def __init__(self):
        self.bitmap_preloaded = [([], 0)]
        self.bitmaps_preloaded_unused = False

    def add_preload_img(self, filename):
        """Still used by main, but deprecated. PLease use ":"-notation for bitmap() / bitmap_text()"""
        self.bitmap_preloaded.append(SimpleTextAndIcons.bitmap_img(filename))
        self.bitmaps_preloaded_unused = True

    def are_preloaded_unused(self):
        """Still used by main, but deprecated. PLease use ":"-notation for bitmap() / bitmap_text()"""
        return self.bitmaps_preloaded_unused is True

    @staticmethod
    def _get_named_bitmaps_keys():
        return SimpleTextAndIcons.bitmap_named.keys()

    def bitmap_char(self, ch):
        """Returns a tuple of 11 bytes, it is the bitmap data of given character.
            Example: ch = '_' returns (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 255).
            The bits in each byte are horizontal, highest bit is left.
        """
        if ord(ch) < 32:
            if ch in SimpleTextAndIcons.bitmap_builtin:
                return SimpleTextAndIcons.bitmap_builtin[ch][:2]

            self.bitmaps_preloaded_unused = False
            return self.bitmap_preloaded[ord(ch)]

        o = SimpleTextAndIcons.char_offsets[ch]
        return SimpleTextAndIcons.font_11x44[o:o + 11], 1

    def bitmap_text(self, text):
        """Returns a tuple of (buffer, length_in_byte_columns_aka_chars)
          We preprocess the text string for substitution patterns
          "::" is replaced with a single ":"
          ":1: is replaced with CTRL-A referencing the first preloaded or loaded image.
          ":happy:" is replaced with a reference to a builtin smiley glyph
          ":heart:" is replaced with a reference to a builtin heart glyph
          ":gfx/logo.png:" preloads the file gfx/logo.png and is replaced the corresponding control char.
        """

        def replace_symbolic(m):
            name = m.group(1)
            if name == '':
                return ':'
            if re.match('^[0-9]*$', name):  # py3 name.isdecimal()
                return chr(int(name))
            if '.' in name:
                self.bitmap_preloaded.append(SimpleTextAndIcons.bitmap_img(name))
                return chr(len(self.bitmap_preloaded) - 1)
            return SimpleTextAndIcons.bitmap_named[name][2]

        text = re.sub(r':([^:]*):', replace_symbolic, text)
        buf = array('B')
        cols = 0
        for c in text:
            (b, n) = self.bitmap_char(c)
            buf.extend(b)
            cols += n
        return buf, cols

    @staticmethod
    def bitmap_img(file):
        """Returns a tuple of (buffer, length_in_byte_columns) representing the given image file.
            It has to be an 8-bit grayscale image or a color image with 8 bit per channel. Color pixels are converted to
            grayscale by arithmetic mean. Threshold for an active led is then > 127.
            If the width is not a multiple on 8 it will be padded with empty pixel-columns.
        """
        try:
            from PIL import Image
        except:
            print("If you like to use images, the module pillow is needed. Try:")
            print("$ pip install pillow")
            LedNameBadge._print_common_install_hints('pillow', 'python3-pillow')
            sys.exit(1)

        im = Image.open(file)
        print("fetching bitmap from file %s -> (%d x %d)" % (file, im.width, im.height))
        if im.height != 11:
            sys.exit("%s: image height must be 11px. Seen %d" % (file, im.height))
        buf = array('B')
        cols = int((im.width + 7) / 8)
        for col in range(cols):
            for row in range(11):  # [0..10]
                byte_val = 0
                for bit in range(8):  # [0..7]
                    bit_val = 0
                    x = 8 * col + bit
                    if x < im.width and row < im.height:
                        pixel_color = im.getpixel((x, row))
                        if isinstance(pixel_color, tuple):
                            monochrome_color = sum(pixel_color[:3]) / len(pixel_color[:3])
                        elif isinstance(pixel_color, int):
                            monochrome_color = pixel_color
                        else:
                            sys.exit("%s: Unknown pixel format detected (%s)!" % (file, pixel_color))
                        if monochrome_color > 127:
                            bit_val = 1 << (7 - bit)
                        byte_val += bit_val
                buf.append(byte_val)
        im.close()
        return buf, cols

    def bitmap(self, arg):
        """If arg is a valid and existing path name, we load it as an image.
            Otherwise, we take it as a string (with ":"-notation, see bitmap_text()).
        """
        if os.path.exists(arg):
            return SimpleTextAndIcons.bitmap_img(arg)
        return self.bitmap_text(arg)


class WriteMethod:
    """Base class for a write method. That is a way to communicate with a device. Think of using different access
    libraries or interfaces for communication. Basically it implements the common parts of the functionalities
    'device detection' and 'write data' and defines te interfaces to the user and the concrete write method class.
    """

    def __init__(self):
        """Call it from your concrete class in your __init__ method with!
        """
        self.devices = {}

    def __del__(self):
        self.close()

    def get_name(self):
        """Returns the name of the write method.
        This method is to be implemented in your concrete class. It should just return a short and unique name.
        """
        raise NotImplementedError()

    def get_description(self):
        """Returns a description of the write method.
        This method is to be implemented in your concrete class. It should just return a short description
        of how the write method communicates with the device (think of libraries and interfaces).
        """
        raise NotImplementedError()

    def open(self, device_id):
        """Opens the communication channel to the device, similar to open a file. The device id is one of the ids
        returned by get_available_devices() or 'auto', which selects just the first device in that dict.
        It is the common part of the opening process. The concrete open is done in _open() and is to be implemented
        individually.
        """
        if self.is_ready() and self.is_device_present():
            actual_device_id = None
            if device_id == 'auto':
                actual_device_id = sorted(self.devices.keys())[0]
            else:
                if device_id in self.devices.keys():
                    actual_device_id = device_id

            if actual_device_id:
                return self._open(actual_device_id)
        return False

    def close(self):
        """Close the communication channel to the device, similar to closing a file.
        This method is to be implemented in your concrete class. It should close and free all handles and resources.
        """
        raise NotImplementedError()

    def get_available_devices(self):
        """Get all devices available via the concrete write method. It returns a dict with the device ids as keys
        and the device descriptions as values. These device ids are used with 'open()' to specify the wanted device.
        It the common part of this process. The concrete part is to be implemented in _get_available_devices()
        individually.
        """
        if self.is_ready() and not self.devices:
            self.devices = self._get_available_devices()
        return {did: data[0] for did, data in self.devices.items()}

    def is_device_present(self):
        """Returns True if there is one or more devices available via the concrete write method, False otherwise.
        """
        self.get_available_devices()
        return self.devices and len(self.devices) > 0

    def _open(self, device_id):
        """The concrete open action. This method is to be implemented in your concrete class. It shall open
        the communication channel to the device with the specified id, which is one of the ids returned by
        _get_available_devices(). It shall return True, if successful, otherwise False. The special id 'auto'
        is handled in open(). So, this method is called only with device ids from the dict returned by
        _get_available_devices().
        """
        raise NotImplementedError()

    def _get_available_devices(self):
        """The concrete get-the-list action. This method is to be implemented in your concrete class. It shall
        Return a dict with one entry per available device. The key of an entry is the device id, like it will be
        used in open() / _open(). The value af an entry is a tuple with any data according to the needs of your
        write method. The only defined element is the first one, which shall be a description of the individual
        device (e.g. manufacturer or bus number / address). E.g. { '1:5': ('Nametag 5 on bus 1', any, data)}
        """
        raise NotImplementedError()

    def is_ready(self):
        """Returns True, if the concrete write method is basically ready for operation, otherwise False.
        This method is to be implemented in your concrete class. Basically, if the import instruction for the
        needed Python modules and potentially a library / module initialization was successful, it shall return True.
        This method does not make any statement about concrete devices or device availability.
        """
        raise NotImplementedError()

    def has_device(self):
        """Returns True, if there is at least one device available with the concrete write method, otherwise False.
        This method is to be implemented in your concrete class.
        """
        raise NotImplementedError()

    def write(self, buf):
        """Call this to write data to the opened device.
        The concrete write action is to be implemented in _write()."""
        self.add_padding(buf, 64)
        self.check_length(buf, 8192)
        self._write(buf)

    @staticmethod
    def add_padding(buf, block_size):
        """The given data array will be extended with zeros according to the given block size. SO, afterwards the
        length of the array is a multiple of block_size.
        """
        need_padding = len(buf) % block_size
        if need_padding:
            buf.extend((0,) * (block_size - need_padding))

    @staticmethod
    def check_length(buf, max_size):
        """Just checks the length of the given data array and abort the program execution if it exceeds max_size.
        """
        if len(buf) > max_size:
            print("Writing more than %d bytes damages the display! Nothing written." % (max_size,))
            sys.exit(1)

    def _write(self, buf):
        """Write the given data array to the opened device.
        This method is to be implemented in your concrete class. It shall write the given data array to the opened
        device.
        """
        raise NotImplementedError()


class WriteLibUsb(WriteMethod):
    """Write to a device using pyusb and libusb. The device ids consist of the bus number, the device number on that bus
    and the endpoint number.
    """
    _module_loaded = False
    try:
        import usb.core
        import usb.util
        _module_loaded = True
        print("Module usb.core detected")
    except:
        pass

    def __init__(self):
        WriteMethod.__init__(self)
        self.description = None
        self.dev = None
        self.endpoint = None

    def get_name(self):
        return 'libusb'

    def get_description(self):
        return 'Program a device connected via USB using the pyusb package and libusb.'

    def _open(self, device_id):
        self.description = self.devices[device_id][0]
        self.dev = self.devices[device_id][1]
        self.endpoint = self.devices[device_id][2]
        print("Libusb device initialized")
        return True

    def close(self):
        if self.dev:
            self.dev.reset()
            WriteLibUsb.usb.util.dispose_resources(self.dev)
        self.description = None
        self.dev = None
        self.endpoint = None

    def _get_available_devices(self):
        devs = WriteLibUsb.usb.core.find(idVendor=0x0416, idProduct=0x5020, find_all=True)
        devices = {}
        for d in devs:
            try:
                # win32: NotImplementedError: is_kernel_driver_active
                if d.is_kernel_driver_active(0):
                    d.detach_kernel_driver(0)
            except:
                pass
            try:
                d.set_configuration()
            except WriteLibUsb.usb.core.USBError:
                # TODO: use all the nice output in _find_write_method(), somehow.
                print("No read access to device list!")
                LedNameBadge._print_sudo_hints()
                sys.exit(1)

            cfg = d.get_active_configuration()[0, 0]
            eps = WriteLibUsb.usb.util.find_descriptor(
                cfg,
                find_all=True,
                custom_match=lambda e: WriteLibUsb.usb.util.endpoint_direction(e.bEndpointAddress) == WriteLibUsb.usb.util.ENDPOINT_OUT)
            for ep in eps:
                did = "%d:%d:%d" % (d.bus, d.address, ep.bEndpointAddress)
                descr = ("%s - %s (bus=%d dev=%d endpoint=%d)" %
                         (d.manufacturer, d.product, d.bus, d.address, ep.bEndpointAddress))
                devices[did] = (descr, d, ep)
        return devices

    def is_ready(self):
        return WriteLibUsb._module_loaded

    def has_device(self):
        return self.dev is not None

    def _write(self, buf):
        if not self.dev:
            return

        try:
            # win32: NotImplementedError: is_kernel_driver_active
            if self.dev.is_kernel_driver_active(0):
                self.dev.detach_kernel_driver(0)
        except:
            pass

        try:
            self.dev.set_configuration()
        except WriteLibUsb.usb.core.USBError:
            # TODO: use all the nice output in _find_write_method(), somehow.
            print("No write access to device!")
            LedNameBadge._print_sudo_hints()
            sys.exit(1)

        print("Write using %s via libusb" % (self.description,))
        for i in range(int(len(buf) / 64)):
            time.sleep(0.1)
            self.endpoint.write(buf[i * 64:i * 64 + 64])


class WriteUsbHidApi(WriteMethod):
    """Write to a device connected to USB using pyhidapi and libhidapi. The device ids are simply the device paths as
    used by libhidapi.
    """
    _module_loaded = False
    try:
        import pyhidapi
        pyhidapi.hid_init()
        _module_loaded = True
        print("Module pyhidapi detected")
    except:
        pass

    def __init__(self):
        WriteMethod.__init__(self)
        self.description = None
        self.path = None
        self.dev = None

    def get_name(self):
        return 'hidapi'

    def get_description(self):
        return 'Program a device connected via USB using the pyhidapi package and libhidapi.'

    def _open(self, device_id):
        self.description = self.devices[device_id][0]
        self.path = self.devices[device_id][1]
        self.dev = WriteUsbHidApi.pyhidapi.hid_open_path(self.path)
        if self.dev:
            print("Hidapi device initialized")

        return self.dev is not None

    def close(self):
        if self.dev is not None:
            WriteUsbHidApi.pyhidapi.hid_close(self.dev)
        self.description = None
        self.path = None
        self.dev = None

    def _get_available_devices(self):
        device_infos = WriteUsbHidApi.pyhidapi.hid_enumerate(0x0416, 0x5020)
        devices = {}
        for d in device_infos:
            did = "%s" % (str(d.path.decode('ascii')),)
            descr = "%s - %s (if=%d)" % (d.manufacturer_string, d.product_string, d.interface_number)
            devices[did] = (descr, d.path)
        return devices

    def is_ready(self):
        return WriteUsbHidApi._module_loaded

    def has_device(self):
        return self.dev is not None

    def _write(self, buf):
        if not self.dev:
            return

        print("Write using [%s] via hidapi" % (self.description,))
        for i in range(int(len(buf) / 64)):
            # sendbuf must contain "report ID" as first byte. "0" does the job here.
            sendbuf = array('B', [0])
            # Then, put the 64 payload bytes into the buffer
            sendbuf.extend(buf[i * 64:i * 64 + 64])
            WriteUsbHidApi.pyhidapi.hid_write(self.dev, sendbuf)


class WriteSerial(WriteMethod):
    """Write to a device with the open-source firmware via the USB serial port using pyserial.
    """
    _module_loaded = False
    try:
        import serial
        _module_loaded = True
        print("Module pyserial detected")
    except:
        pass

    def __init__(self):
        WriteMethod.__init__(self)
        self.description = None
        self.path = None
        self.dev = None

    def get_name(self):
        return 'pyserial'

    def get_description(self):
        return 'Program a device with the open-source firmware, connected via USB, using the pyserial package.'

    def _open(self, device_id):
        import serial
        self.description = self.devices[device_id][0]
        self.path = self.devices[device_id][1]
        self.dev = serial.Serial(self.path)
        if self.dev:
            print("Pyserial device initialized")

        return self.dev is not None

    def close(self):
        if self.dev is not None:
            self.dev.close()
        self.description = None
        self.path = None
        self.dev = None

    def _get_available_devices(self):
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()

        devices = {}
        for port, desc, hwid in ports:
            if desc == "n/a": 
                continue
            devices[port] = (f"{desc} ({hwid})", port)
        return devices

    def is_ready(self):
        return WriteSerial._module_loaded

    def has_device(self):
        return self.dev is not None

    def _write(self, buf):
        if not self.dev:
            return

        print("Write using [%s] via pyserial" % (self.description,))
        self.dev.write(buf)


class LedNameBadge:
    _protocol_header_template = (
        0x77, 0x61, 0x6e, 0x67, 0x00, 0x00, 0x00, 0x00, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40, 0x40,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
    )

    @staticmethod
    def header(lengths, speeds, modes, blinks, ants, brightness=100, date=datetime.now()):
        """Create a protocol header
            * length, speeds, modes, blinks, ants are iterables with at least one element
            * lengths[0] is the number of chars/byte-columns of the first text/bitmap, lengths[1] of the second,
              and so on...
            * len(length) should match the designated bitmap data
            * speeds come in as 1..8, but will be decremented to 0..7, here.
            * modes: 0..8
            * blinks and ants: 0..1 or even False...True,
            * brightness, if given, is any number, but it'll be limited to 25, 50, 75, 100 (percent), here
            * date, if given, is a datetime object. It will be written in the header, but is not to be seen on the
              devices screen.
        """
        try:
            lengths_sum = sum(lengths)
        except:
            raise TypeError("Please give a list or tuple with at least one number: " + str(lengths))
        if lengths_sum > (8192 - len(LedNameBadge._protocol_header_template)) / 11 + 1:
            raise ValueError("The given lengths seem to be far too high: " + str(lengths))

        ants = LedNameBadge._prepare_iterable(ants, 0, 1)
        blinks = LedNameBadge._prepare_iterable(blinks, 0, 1)
        speeds = LedNameBadge._prepare_iterable(speeds, 1, 8)
        modes = LedNameBadge._prepare_iterable(modes, 0, 8)

        speeds = [x - 1 for x in speeds]

        h = list(LedNameBadge._protocol_header_template)

        if brightness <= 25:
            h[5] = 0x40
        elif brightness <= 50:
            h[5] = 0x20
        elif brightness <= 75:
            h[5] = 0x10
        # else default 100% == 0x00

        for i in range(8):
            h[6] += blinks[i] << i
            h[7] += ants[i] << i

        for i in range(8):
            h[8 + i] = 16 * speeds[i] + modes[i]

        for i in range(len(lengths)):
            h[17 + (2 * i) - 1] = lengths[i] // 256
            h[17 + (2 * i)] = lengths[i] % 256

        try:
            h[38 + 0] = date.year % 100
            h[38 + 1] = date.month
            h[38 + 2] = date.day
            h[38 + 3] = date.hour
            h[38 + 4] = date.minute
            h[38 + 5] = date.second
        except:
            raise TypeError("Please give a datetime object: " + str(date))

        return h

    @staticmethod
    def _prepare_iterable(iterable, min_, max_):
        try:
            iterable = [min(max(x, min_), max_) for x in iterable]
            iterable = tuple(iterable) + (iterable[-1],) * (8 - len(iterable))  # repeat last element
            return iterable
        except:
            raise TypeError("Please give a list or tuple with at least one number: " + str(iterable))

    @staticmethod
    def write(buf, method='auto', device_id='auto'):
        """Write the given buffer to the given device.
            It has to begin with a protocol header as provided by header() and followed by the bitmap data.
            In short: the bitmap data is organized in bytes with 8 horizontal pixels per byte and 11 resp. 12
            bytes per (8 pixels wide) byte-column. Then just put one byte-column after the other and one bitmap
            after the other.
            The two optional parameters specify the write method and device, which shall be programmed. See
            get_available_methods() and get_available_device_ids(). There are two special values each: 'list'
            will print the implemented / available write methods resp. the available devices, 'auto' (default) will
            choose an appropriate write method resp. the first device found.
        """
        write_method = LedNameBadge._find_write_method(method, device_id)
        if write_method:
            write_method.write(buf)
            write_method.close()

    @staticmethod
    def get_available_methods():
        """
        Returns the implemented / available write methods as a dict. Each entry has the method name as the key and a
        tuple as the value with the method description and a boolean indicating the readiness of that write method.
        Basically it is ready if all necessary libraries and Python modules could be loaded. The method name can be
        used as a parameter value for write().
        """
        auto_order_methods = LedNameBadge._get_auto_order_method_list()
        return {m.get_name(): (m.get_description(), m.is_ready()) for m in auto_order_methods}

    @staticmethod
    def get_available_device_ids(method):
        """Returns all devices available via the given write method as a dict. Each entry has the device id as the key
        and the device description as the value. The device id can be used as a parameter value for write().
        """
        auto_order_methods = LedNameBadge._get_auto_order_method_list()
        wanted_method = [m for m in auto_order_methods if m.get_name() == method]
        if wanted_method:
            return wanted_method[0].get_available_devices()
        return []

    @staticmethod
    def _find_write_method(method, device_id):
        """Here we try to concentrate all special cases, decisions and messages around the manual or automatic
        selection of write methods and device. This way it is a bit easier to extend or modify the different
        working run time environments (think of operating system, python version, installed libraries and python
        modules, ands so on.)"""
        auto_order_methods = LedNameBadge._get_auto_order_method_list()
        hidapi = [m for m in auto_order_methods if m.get_name() == 'hidapi'][0]
        libusb = [m for m in auto_order_methods if m.get_name() == 'libusb'][0]

        if method == 'list':
            LedNameBadge._print_available_methods(auto_order_methods)
            sys.exit(0)

        if method not in [m.get_name() for m in auto_order_methods] and method != 'auto':
            print("Unknown write method '%s'." % (method,))
            LedNameBadge._print_available_methods(auto_order_methods)
            sys.exit(1)

        if method == 'auto':
            if sys.version_info[0] < 3:
                method = libusb.get_name()
                print("Preferring method %s over %s with Python 2.x" % (libusb.get_name(), hidapi.get_name()))
                print("because of https://github.com/jnweiger/led-badge-ls32/issues/9")
            elif sys.platform.startswith('darwin'):
                method = hidapi.get_name()
                print("Selected method %s with MacOs" % (hidapi.get_name(),))
            elif sys.platform.startswith('win'):
                method = libusb.get_name()
                print("Selected method %s with Windows" % (libusb.get_name(),))
            elif not libusb.is_ready() and not hidapi.is_ready():
                if sys.version_info[0] < 3 or sys.platform.startswith('win'):
                    LedNameBadge._print_libusb_install_hints(libusb.get_name())
                    sys.exit(1)
                elif sys.platform.startswith('darwin'):
                    LedNameBadge._print_hidapi_install_hints(hidapi.get_name())
                    sys.exit(1)
                else:
                    print("One of the python packages 'pyhidapi' or 'pyusb' is needed to run this program (or both).")
                    LedNameBadge._print_libusb_install_hints(libusb.get_name())
                    LedNameBadge._print_hidapi_install_hints(hidapi.get_name())
                    sys.exit(1)

        if method == libusb.get_name():
            if sys.platform.startswith('darwin'):
                print("For MacOs, please use method '%s' or 'auto'." % (hidapi.get_name(),))
                print("Or help us implementing support for MacOs.")
                sys.exit(1)
            elif not libusb.is_ready():
                LedNameBadge._print_libusb_install_hints(libusb.get_name())
                sys.exit(1)

        if method == hidapi.get_name():
            if sys.version_info[0] < 3:
                print("Please use method '%s' or 'auto' with python-2.x" % (libusb.get_name(),))
                print("because of https://github.com/jnweiger/led-badge-ls32/issues/9")
                sys.exit(1)
            elif not hidapi.is_ready():
                LedNameBadge._print_hidapi_install_hints(hidapi.get_name())
                sys.exit(1)

            if sys.platform.startswith('win') and hidapi.is_ready():
                print("Method '%s' is not tested under Windows. If not working, please use '%s' or 'auto'" % (
                    hidapi.get_name(), libusb.get_name()))
                print("Or help us implementing support for Windows.")
                # But it is not forbidden

        first_method_found = None
        for m in auto_order_methods:
            if method == 'auto' or method == m.get_name():
                if not first_method_found:
                    first_method_found = m
                if device_id == 'list':
                    LedNameBadge._print_available_devices(m)
                    sys.exit(0)
                elif m.open(device_id):
                    return m

        device_id_str = ''
        if device_id != 'auto':
            device_id_str = ' with device_id %s' % (device_id,)

        print("The device is not available with write method '%s'%s." % (method, device_id_str))
        if first_method_found:
            LedNameBadge._print_available_devices(first_method_found)
        print("* Is a led tag device with vendorID 0x0416 and productID 0x5020 connected?")
        if device_id != 'auto':
            print("* Have you given the right device_id?")
            print("  Find the available device ids with option -D list")
        print("* If it is connected and still do not work:")
        LedNameBadge._print_sudo_hints()
        sys.exit(1)

    @staticmethod
    def _get_auto_order_method_list():
        return [WriteUsbHidApi(), WriteLibUsb(), WriteSerial()]

    @staticmethod
    def _print_available_methods(methods):
        print("Available write methods:")
        print("  'auto': selects the most appropriate of the available methods (default)")
        for m in methods:
            LedNameBadge._print_one_method(m)

    @staticmethod
    def _print_one_method(m):
        print("  '%s': %s" % (m.get_name(), m.get_description()))

    @staticmethod
    def _print_available_devices(method_obj):
        if method_obj.is_device_present():
            print("Known device ids with method '%s' are:" % (method_obj.get_name(),))
            for did, descr in sorted(method_obj.get_available_devices().items()):
                LedNameBadge._print_one_device(did, descr)
        else:
            print("No devices with method '%s' found." % (method_obj.get_name(),))

    @staticmethod
    def _print_one_device(did, descr):
        print("  '%s': %s" % (did, descr))

    @staticmethod
    def _print_libusb_install_hints(name):
        print("The method %s is not possible to be used:" % (name,))
        print("The modules 'usb.core' and 'usb.util' could not be loaded.")
        print("* Have you installed the corresponding python package 'pyusb'? Try:")
        print("  $ pip install pyusb")
        LedNameBadge._print_common_install_hints('pyusb', 'python3-usb')
        if sys.platform.startswith('win'):
            print("* Have you installed the libusb driver or libusb-filter for the device?")
        elif sys.platform.startswith('linux'):
            print("* Is the library itself installed? Try the following")
            print("  (or similar, suitable for your distro; the exact command and package name might be different):")
            print("  $ sudo apt-get install libusb-1.0-0")

    @staticmethod
    def _print_hidapi_install_hints(name):
        print("The method %s is not possible to be used:" % (name,))
        print("The module 'pyhidapi' could not be loaded.")
        print("* Have you installed the corresponding python package 'pyhidapi'? Try:")
        print("  $ pip install pyhidapi")
        LedNameBadge._print_common_install_hints('pyhidapi', 'python3-hidapi')
        if sys.platform.startswith('darwin'):
            print("* Have you installed the library itself? Try:")
            print("  $ brew install hidapi")
        elif sys.platform.startswith('linux'):
            print("* Is the library itself installed? Try the following")
            print("  (or similar, suitable for your distro; the exact command and package name might be different):")
            print("  $ sudo apt-get install libhidapi-hidraw0")
            print("* If the library is still not found by the module. Try the following")
            print(
                "  (or similar, suitable for your distro; the exact command, library name and paths might be different):")
            print("  $ sudo ln -s /usr/lib/x86_64-linux-gnu/libhidapi-hidraw.so.0  /usr/local/lib/")

    @staticmethod
    def _print_common_install_hints(pip_package, pm_package):
        print("  (You may need to use pip3 or pip2 instead of pip depending on your python version.)")
        if sys.platform.startswith('win'):
            print("  (You may need to run cmd.exe as Administrator for system wide module installation.)")
        if sys.platform.startswith('linux'):
            print("  (You may need prepend 'sudo' for system wide module installation.)")
            print("  (You may also use your package manager. Try the following, e.g for %s)" % (pip_package,))
            print("  (or similar, suitable for your distro; the exact command and package name might be different):")
            print("  $ sudo apt install %s" % (pm_package,))

    @staticmethod
    def _print_sudo_hints():
        print("Maybe, you have to run this program with administrator rights.")
        if sys.platform.startswith('win'):
            print("* Open start menu, type 'cmd', click 'Run as Administrator'")
        if sys.platform.startswith('linux'):
            print("* If Try with sudo or")
            print("* If you run the program from a virtual env, you may need to open a root shell beforehand.")
            print("* Best: add a udev rule like described in README.md.")


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='Upload messages or graphics to a 11x44 led badge via USB HID.\nVersion %s from https://github.com/jnweiger/led-badge-ls32\n -- see there for more examples and for updates.' % __version,
                                     epilog='Example combining image and text:\n sudo %s "I:HEART2:you"' % sys.argv[0])
    parser.add_argument('-t', '--type', default='11x44',
                        help="Type of display: supported values are 12x48 or (default) 11x44. Rename the program to led-badge-12x48, to switch the default.")
    parser.add_argument('-H',
                        '--hid',
                        default='0',
                        help="Deprecated, only for backwards compatibility, please use -M! Set to 1 to ensure connect via HID API, program will then not fallback to usb.core library.")
    parser.add_argument('-M',
                        '--method',
                        default='auto',
                        help="Force using the given write method. Use one of 'auto', 'list' or whatever list is printing.")
    parser.add_argument('-D',
                        '--device-id',
                        default='auto',
                        help="Force using the given device id, if ambiguous. Use one of 'auto', 'list' or whatever list is printing.")
    parser.add_argument('-s', '--speed', default='4', help="Scroll speed (Range 1..8). Up to 8 comma-separated values.")
    parser.add_argument('-B', '--brightness', default='100',
                        help="Brightness for the display in percent: 25, 50, 75, or 100.")
    parser.add_argument('-m', '--mode', default='0',
                        help="Up to 8 mode values: Scroll-left(0) -right(1) -up(2) -down(3); still-centered(4); animation(5); drop-down(6); curtain(7); laser(8); See '--mode-help' for more details.")
    parser.add_argument('-b', '--blink', default='0', help="1: blinking, 0: normal. Up to 8 comma-separated values.")
    parser.add_argument('-a',
                        '--ants',
                        default='0',
                        help="1: animated border, 0: normal. Up to 8 comma-separated values.")
    parser.add_argument('-p', '--preload', metavar='FILE', action='append',
                        help=argparse.SUPPRESS)  # "Load bitmap images. Use ^A, ^B, ^C, ... in text messages to make them visible. Deprecated, embed within ':' instead")
    parser.add_argument('-l',
                        '--list-names',
                        action='version',
                        help="list named icons to be embedded in messages and exit.",
                        version=':' + ':  :'.join(SimpleTextAndIcons._get_named_bitmaps_keys()) + ':  ::  or e.g. :path/to/some_icon.png:')
    parser.add_argument('message', metavar='MESSAGE', nargs='+',
                        help="Up to 8 message texts with embedded builtin icons or loaded images within colons(:) -- See -l for a list of builtins.")
    parser.add_argument('--mode-help', action='version', help=argparse.SUPPRESS, version="""
    
    -m 5 "Animation"
    
     Animation frames are 6 character (or 48px) wide. Upload an animation of
     N frames as one image N*48 pixels wide, 11 pixels high.
     Frames run from left to right and repeat endless.
     Speeds [1..8] result in ca. [1.2 1.3 2.0 2.4 2.8 4.5 7.5 15] fps.
    
     Example of a slowly beating heart:
      sudo %s -s1 -m5 "  :heart2:    :HEART2:"
    
    -m 9 "Smooth"
    -m 10 "Rotate"
    
     These modes are mentioned in the BMP Badge software.
     Text is shown static, or sometimes (longer texts?) not shown at all.
     One significant difference is: The text of the first message stays visible after
     upload, even if the USB cable remains connected.
     (No "rotation" or "smoothing"(?) effect can be expected, though)
    """ % sys.argv[0])
    args = parser.parse_args()

    creator = SimpleTextAndIcons()

    if args.preload:
        for filename in args.preload:
            creator.add_preload_img(filename)

    msg_bitmaps = []
    for msg_arg in args.message:
        msg_bitmaps.append(creator.bitmap(msg_arg))

    if creator.are_preloaded_unused():
        print(
            "\nWARNING:\n Your preloaded images are not used.\n Try without '-p' or embed the control character '^A' in your message.\n")

    if '12' in args.type or '12' in sys.argv[0]:
        print("Type: 12x48")
        for msg_bitmap in msg_bitmaps:
            # trivial hack to support 12x48 badges:
            # patch extra empty lines into the message stream.
            for i in reversed(range(1, int(len(msg_bitmap[0]) / 11) + 1)):
                msg_bitmap[0][i * 11:i * 11] = array('B', [0])
    else:
        print("Type: 11x44")

    lengths = [b[1] for b in msg_bitmaps]
    speeds = split_to_ints(args.speed)
    modes = split_to_ints(args.mode)
    blinks = split_to_ints(args.blink)
    ants = split_to_ints(args.ants)
    brightness = int(args.brightness)

    buf = array('B')
    buf.extend(LedNameBadge.header(lengths, speeds, modes, blinks, ants, brightness))

    for msg_bitmap in msg_bitmaps:
        buf.extend(msg_bitmap[0])

    # Translate -H to -M parameter
    method = args.method
    if args.hid == 1:
        print("Option -H is deprecated, please use -M!")
        if not method or method == 'auto':
            method = 'hidapi'
        else:
            sys.exit("Parameter values are ambiguous. Please use -M only.")

    LedNameBadge.write(buf, method, args.device_id)


def split_to_ints(list_str):
    return [int(x) for x in re.split(r'[\s,]+', list_str)]


if __name__ == '__main__':
    main()
