#!/usr/bin/env python

import os
import sys
import json
import time
import argparse
import requests
from c_cfgGIT import cfgGIT

def main():

    parser = argparse.ArgumentParser(description='Update git to revision on remote server.')
    parser.add_argument("-s", "--section", metavar="section", type=str, help="define the section to be updated", required=True)
    parser.add_argument("-f", "--file", metavar="file", type=str, help="configuration file", required=True)

    args = parser.parse_args()

    section = args.section
    cfg_file = args.file

    print "Running auto config %s" % (time.ctime())
    git = cfgGIT(section, cfg_file)
    git.set_local_config("remote_config_url")
    git.set_remote_config("remote_git_tag")

    git.update()

if __name__ == '__main__':
    main()
