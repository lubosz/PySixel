# -*- coding: utf-8 -*-
# Copyright 2012-2014 Hayaki Saito <user@zuse.jp>
# Copyright 2023 Lubosz Sarnecki <lubosz@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
import optparse
import select
import logging
import termios
import tty
from io import StringIO

from .cellsize import get_size
from .sixel import SixelWriter
from .__about__ import __version__


def _filenize(f):
    import stat
    mode = os.fstat(f.fileno()).st_mode
    if stat.S_ISFIFO(mode) or os.isatty(f.fileno()):
        return StringIO(f.read())
    return f

def is_term_sixel_capable():
    """based on `printf "\\033[c"`; returns if the current terminal emulator is capable of SIXEL"""
    # import sys, termios, tty
    if os.getenv("TERM", '').strip().startswith("yaft"):
        return True

    print("\033[c", end="", flush=True)
    fd = sys.stdin.fileno()
    orig = termios.tcgetattr(fd)

    try:
        tty.setcbreak(fd)  # or tty.setraw(fd) if you prefer raw mode's behavior.
        return '4' in sys.stdin.read(10).split(";")
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, orig)

def main():
    parser = optparse.OptionParser()

    parser.add_option("-8", "--8bit-mode",
                      action="store_true",
                      dest="f8bit",
                      help="Generate a sixel image for 8bit terminal or printer")

    parser.add_option("-7", "--7bit-mode",
                      action="store_false",
                      dest="f8bit",
                      help="Generate a sixel image for 7bit terminal or printer")

    parser.add_option("-r", "--relative-position",
                      action="store_false",
                      default=False,
                      dest="fabsolute",
                      help="Treat specified position as relative one")

    parser.add_option("-a", "--absolute-position",
                      action="store_true",
                      dest="fabsolute",
                      help="Treat specified position as absolute one")

    parser.add_option("-x", "--left",
                      action="store",
                      dest="left",
                      help="Left position in cell size, or pixel size with unit 'px'")

    parser.add_option("-y", "--top",
                      action="store",
                      dest="top",
                      help="Top position in cell size, or pixel size with unit 'px'")

    parser.add_option("-w", "--width",
                      action="store",
                      dest="width",
                      help="Width in cell size, or pixel size with unit 'px'")

    parser.add_option("-e", "--height",
                      action="store",
                      dest="height",
                      help="Height in cell size, or pixel size with unit 'px'")

    parser.add_option("-t", "--alpha-threshold",
                      action="store",
                      type="int",
                      dest="alpha_threshold",
                      default="0",
                      help="Alpha threshold for PNG-to-SIXEL image conversion")

    parser.add_option("-c", "--chromakey",
                      dest="chromakey",
                      default=False,
                      action="store_true",
                      help="Enable auto chroma key processing")

    parser.add_option("-n", "--ncolor",
                      action="store",
                      type="int",
                      dest="ncolor",
                      default=256,
                      help="Specify number of colors")

    parser.add_option("-b", "--body-only",
                      action="store_true",
                      dest="body_only",
                      default=False,
                      help="Output sixel without header and DCS envelope")

    parser.add_option("-f", "--fast",
                      action="store_true",
                      dest="fast",
                      default=True,
                      help="The speed priority mode (default)")

    parser.add_option("-s", "--size",
                      action="store_false",
                      dest="fast",
                      default=True,
                      help="The size priority mode")

    parser.add_option("-v", "--version",
                      action="store_true",
                      dest="version",
                      default=False,
                      help="Show version")

    options, args = parser.parse_args()

    if options.version:
        print(__version__)
        sys.exit(0)

    rcdir = os.path.join(os.getenv("HOME"), ".pysixel")
    logdir = os.path.join(rcdir, "log")
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logfile = os.path.join(logdir, "log.txt")
    logging.basicConfig(filename=logfile, filemode="w")

    stdin, stdout = sys.stdin, sys.stdout
    left = options.left
    top = options.top
    width = options.width
    height = options.height

    if (left, top, width, height) != (None, None, None, None):
        if os.isatty(stdout.fileno()) and os.isatty(stdin.fileno()):
            try:
                char_width, char_height = get_size()
            except Exception:
                char_width, char_height = (10, 20)
        else:
            char_width, char_height = (10, 20)

        if left is not None:
            pos = left.find("px")
            if pos > 0:
                left = int(left[:pos]) / char_width
            else:
                left = int(left)

        if top is not None:
            pos = top.find("px")
            if pos > 0:
                top = int(top[:pos]) / char_width
            else:
                top = int(top)

        if width is not None:
            pos = width.find("px")
            if pos > 0:
                width = int(width[:pos])
            else:
                width = int(width) * char_width

        if height is not None:
            pos = height.find("px")
            if pos > 0:
                height = int(height[:pos])
            else:
                height = int(height) * char_height

    writer = SixelWriter(f8bit=options.f8bit,
                         body_only=options.body_only)

    try:
        if select.select([stdin, ], [], [], 0.0)[0]:
            image_file = _filenize(stdin)
        elif len(args) == 0 or args[0] == '-':
            image_file = _filenize(stdin)
        else:
            image_file = args[0]

        writer.draw(image_file,
                    output=sys.stdout,
                    absolute=options.fabsolute,
                    x=left,
                    y=top,
                    w=width,
                    h=height,
                    ncolor=int(options.ncolor),
                    alpha_threshold=options.alpha_threshold,
                    chromakey=options.chromakey,
                    fast=options.fast)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
