#!/usr/bin/env python

import os
import sys
import argparse

from EC2Init import EC2Init

def main():

    """ Init EC2 Instance """
    
    instance = EC2Init()
    instance.write_ssh_key()
    instance.set_metadata_hostname()
    instance.swap_on()
    instance.clean_net_rules()

if __name__ == '__main__':
    main()

