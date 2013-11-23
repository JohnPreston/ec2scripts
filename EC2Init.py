#!/usr/bin/env python

import re
import os
import sys
import time
import platform
import requests

class EC2Init(object):

    __urls = {'base': '169.254.169.254/latest/',
              'metadata': 'meta-data/',
              'hostname': 'local-hostname',
              'pv-v4': 'local-ipv4',
              'pub-v4': 'public-ipv4',
              'sshkey': 'public-keys/0/openssh-key/'}

    def set_metadata_hostname(self):
        """
        Sets the hosts file with localhost and pv ipv4
        """

        ipv4_url = 'http://%s%s%s' % (self.__urls['base'],
                                      self.__urls['metadata'],
                                      self.__urls['pv-v4'])
        ipv4_r = requests.get(ipv4_url)

        hostname_url = 'http://%s%s%s' % (self.__urls['base'],
                                          self.__urls['metadata'],
                                          self.__urls['hostname'])
        hostname_r = requests.get(hostname_url)
        dist = platform.linux_distribution()[0]

        if (ipv4_r.status_code and hostname_r.status_code) == requests.codes.ok:
            print "Values received - Editing the hosts file"
            hosts_path = '/etc/hosts'
            with open(hosts_path, 'w') as hosts_fd:
                hosts_fd.write('127.0.0.1\tlocalhost\n%s\t%s\n' % (ipv4_r.text, hostname_r.text))
            os.system("hostname %s" % (hostname_r.text))
        else:
            sys.exit("All values not received. Quit --")
            sys.exit(-1)

        if (dist.lower() == 'centos') or (dist.lower() == 'redhat'):
            print "On CentOS/RedHat distrib. Changing the sysconfig"


    def set_ssh_key(self):
        """
        Define the SSH Key from meta-data
        """
        ssh_try = 1
        ssh_key_url = 'http://%s%s%s' % (self.__urls['base'],
                                         self.__urls['metadata'],
                                         self.__urls['sshkey'])
        while True:
            ssh_key_r = requests.get(url=ssh_key_url, timeout=5)
            if ssh_try == 5:
                time.sleep(5)
                os.system("reboot")
            elif ssh_key_r.status_code == requests.codes.ok:
                break
            else:
                time.sleep(2)
                ssh_try += 1
        return ssh_key_r.text
        
    def write_ssh_key(self):
        """ Set SSH key for users """

        ssh_key = self.set_ssh_key()
        user_home = '/home/ec2-user/.ssh/authorized_keys'

        with open(user_home, 'w') as sshkey_fd:
            sshkey_fd.write("%s\n" % (ssh_key))
        print "=====\tAuthorized keys\t=====\n%s\n=====" % (ssh_key)
        os.system("chown ec2-user:ec2-user /home/ec2-user -R")

    def clean_net_rules(self):
        """ Delete network rules """
        os.system("rm -rfv /etc/udev/rules.d/*")

    def reset_ssh_keys(self):
        """ Generate ssh keys """
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
        """ Sets the SWAP """
        ephemeral = "/dev/vdb"
        with os.popen("/sbin/swapon -s | /bin/grep vdb | /usr/bin/cut -d ' ' -f 1") as swapon_list_cmd:
            swapon_list = swapon_list_cmd.read().strip()
            if not ephemeral in swapon_list:
                os.system("echo -e 'n\np\n1\n\n\nw\n' | /sbin/fdisk %s 2>/dev/null 1>/dev/null" % (ephemeral))
                os.system("/sbin/mkswap -f %s" % (ephemeral))
                os.system("/sbin/swapon %s" % (ephemeral))
            else:
                print "%s is already in swap" % (ephemeral)
