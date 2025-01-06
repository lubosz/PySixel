#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2023 Lubosz Sarnecki <lubosz@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import sys
from pathlib import Path
import argparse
from sixel import converter, is_term_sixel_capable


def main():
    parser = argparse.ArgumentParser(prog='PySixel converter example')

    parser.add_argument('image_path', type=Path)
    args = parser.parse_args()

    if not args.image_path.exists():
        logging.error(f"Path '{args.image_path}' does not exist.")
        return

    sixel_converter = converter.SixelConverter(args.image_path)
    sixel_converter.write(sys.stdout)


if __name__ == "__main__":
    if is_term_sixel_capable():
        main()
    else:
        raise EnvironmentError("Your current terminal emulator does not support SIXEL!")
