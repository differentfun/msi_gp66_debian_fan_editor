#!/usr/bin/env python3

import os
import pathlib
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import fan_profile


def main():
    if os.geteuid() != 0:
        raise PermissionError("apply_fan_profile.py must run as root")
    profile = fan_profile.load_profile()
    fan_profile.apply_profile(profile)


if __name__ == "__main__":
    main()
