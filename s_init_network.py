#!/usr/bin/python

import os
import sys
import json
import time
import requests
import subprocess
from c_cfgNET import cfgNET


def main():
    if len(sys.argv) > 1:
        sys.exit("Usage: ./s_init_network.py")
        sys.exit(1)
    else:
        print "Iniating new network configuration - %s" % (time.ctime())

        cfg = cfgNET()
        cfg.applyCfg()
        cfg.set_eip()

if __name__ == '__main__':
    main()

