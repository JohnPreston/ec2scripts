###############################################################################
# Class cfgVM -> will be used to manage get and set all VM parameters

import os
import sys
import json
import time
import requests
import subprocess

class cfgVM(object):

    def clean_net_rules(self):
        os.system("rm -rfv /etc/udev/rules.d/*")

    def reset_ssh_keys(self):
        ssh_type = ['rsa', 'dsa', 'ecdsa']
        for key_type in ssh_type:
            if os.path.exists("/etc/ssh/ssh_host_%s_key" % (key_type)):
                print "Key file %s already exists" % (key_type)
            else:
                os.system("/usr/bin/ssh-keygen -t %s -N '' -q -f /etc/ssh/ssh_host_%s_key" % (key_type, key_type))
        if os.path.exists("/etc/init.d/ssh"):
            os.system("/etc/init.d/ssh restart")
        else:
            os.system("/etc/init.d/sshd restart")

    def swap_on(self):
        ephemeral = "/dev/vdb"
        with os.popen("/sbin/swapon -s | /bin/grep vdb | /usr/bin/cut -d ' ' -f 1") as swapon_list_cmd:
            swapon_list = swapon_list_cmd.read().strip()
            if not ephemeral in swapon_list:
                os.system("echo -e 'n\np\n1\n\n\nw\n' | /sbin/fdisk %s 2>/dev/null 1>/dev/null" % (ephemeral))
                os.system("/sbin/mkswap -f %s" % (ephemeral))
                os.system("/sbin/swapon %s" % (ephemeral))
            else:
                print "%s is already in swap" % (ephemeral)
