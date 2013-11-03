###############################################################################
# Class cfgNET -> will be used to manage get and set all VMs network parameters

import os
import sys
import json
import time
import requests
import subprocess

class cfgNET:

    def set_metadata_hostname(self):
        if not hasattr(self, 'local_ipv4'):
            self.set_local_ipv4()
        meta_local_hostname_r = requests.get("%s/%s" % (self.ec2_metadata_url, self.ec2_metadata_euca_host))
        if meta_local_hostname_r.status_code == requests.codes.ok:
            self.meta_local_hostname = meta_local_hostname_r.text.split('.')

            with open("/etc/hostname", "w") as hostname_fd:
                hostname_fd.write("%s\n" % (self.meta_local_hostname[0]))

            with open("/etc/hosts", "w") as hosts_fd:
                hosts_fd.write("127.0.0.1\tlocalhost\n")
                hosts_fd.write("%s\t%s\t%s\n" % (self.local_ipv4, self.meta_local_hostname[0],
                                                 meta_local_hostname_r.text))
                os.system("hostname %s" % (self.meta_local_hostname[0]))

    def set_user_datas(self):
        user_data_r = requests.get(self.ec2_userdata_url)
        if user_data_r.status_code == requests.codes.ok:
            user_data_json = user_data_r.text
            self.user_datas = json.loads(user_data_json)
        else:
            print "No user-data - Exiting auto configuration"
            self.user_datas = {}

    def set_hostname(self):
        with os.popen("hostname") as host_fd:
            hostname = host_fd.read()
        with open("/etc/hosts", "w+") as hosts_fd:
            hosts_fd.write("127.0.0.1 %s\tlocalhost\n:1\tlocalhost\n" % (hostname.strip()))

    def change_sys_default_routes(self):
        if not (hasattr(self, 'vpc_cidr') and hasattr(self, 'subnet_new_gw') and hasattr(self, subnet_old_gw)):
            self.set_vpccidr()
            self.set_subnet_new_gw()
            self.set_subnet_old_gw()
        os.system("route del default gw %s" % (self.subnet_old_gw))
        os.system("route add default gw %s" % (self.subnet_new_gw))
        os.system("route add -net %s gw %s" % (self.vpc_cidr, self.subnet_old_gw))
        
    def auto_update(self):
        public_ip_r = requests.get("%s/%s" % (self.ec2_metadata_url, "public-ipv4"))
        if public_ip_r.status_code == requests.codes.ok:
            print "EIP Assigned - Not changing routes"
            if not (hasattr(self, 'vpc_cidr') and hasattr(self, 'subnet_new_gw') and hasattr(self, subnet_old_gw)):
                self.set_vpccidr()
                self.set_subnet_new_gw()
                self.set_subnet_old_gw()
            os.system("route del default gw %s" % (self.subnet_new_gw))
            os.system("route add default gw %s" % (self.subnet_old_gw))
            os.system("route del -net %s gw %s" % (self.vpc_cidr, self.subnet_old_gw))
        else:
            self.applyCfg()

    def applyCfg(self, dns_file_path="/etc/resolv.conf"):
        public_ip_r = requests.get("%s/%s" % (self.ec2_metadata_url, "public-ipv4"))
        if not public_ip_r.status_code == requests.codes.ok:
            print "No EIP - Changing GW to NAT"
            self.change_sys_default_routes()

    def get_ec2_conf(self):
        with open(self.ec2_conffile_path) as conf_file:
            print conf_file.read()

    def set_eip(self):
        if not hasattr(self, 'user_datas'):
            self.set_user_datas()
            self.get_instance_id()
            if ('EC2_KEY' in self.user_datas.keys() and 
                'EC2_SKEY' in self.user_datas.keys() and 
                'EC2_URL' in self.user_datas.keys() and 
                'EC2_EIP' in self.user_datas.keys()):
                os.system("euca-associate-address %s -i %s -a %s -s %s -U %s" % (self.user_datas['EC2_EIP'],
                                                                                 self.instance_id,
                                                                                 self.user_datas['EC2_KEY'],
                                                                                 self.user_datas['EC2_SKEY'],
                                                                                 self.user_datas['EC2_URL']))

    def set_hwaddr(self):
        hwaddr_r = requests.get("%s/%s/" % (self.ec2_metadata_url, self.ec2_metadata_hwaddr))
        self.hwaddr = hwaddr_r.text.strip('/')
        
    def set_vpccidr(self):
        if not hasattr(self, 'hwaddr'):
            self.set_hwaddr()
        vpccidr_r = requests.get("%s/%s/%s/%s" % (self.ec2_metadata_url, self.ec2_metadata_hwaddr, 
                                                  self.hwaddr, self.ec2_metadata_vpccidr))
        self.vpc_cidr = vpccidr_r.text
        
    def set_subnetcidr(self):
        if not hasattr(self, 'hwaddr'):
            self.set_hwaddr()
        subnetcidr_r = requests.get("%s/%s/%s/%s" % (self.ec2_metadata_url, self.ec2_metadata_hwaddr, 
                                                  self.hwaddr, self.ec2_metadata_subnetcidr))
        self.subnet_cidr = subnetcidr_r.text

    def set_subnet_net(self):
        if not hasattr(self, 'subnet_cidr'):
            self.set_subnetcidr()
        self.subnet_net = self.subnet_cidr.split("/")[0]

    def set_subnet_new_gw(self):
        if not hasattr(self, 'subnet_net'):
            self.set_subnet_net()
        self.subnet_new_gw = self.subnet_net.replace(".0", ".254")

    def set_subnet_old_gw(self):
        if not hasattr(self, 'subnet_net'):
            self.set_subnet_net()
        self.subnet_old_gw = self.subnet_net.replace(".0", ".1")
        
    def get_instance_id(self):
        instance_id_r = requests.get("%s/%s" % (self.ec2_metadata_url, "instance-id"))
        self.instance_id = instance_id_r.text

    def set_ssh_key(self):
        ssh_try = 1
        while True:
            ssh_key_r = requests.get("%s/%s"  % (self.ec2_metadata_url, self.ec2_metadata_key))
            if ssh_try == 5:
                print "Failed to get ssh_key - Reboot in 5 seconds"
                time.sleep(5)
                os.system("reboot")
            elif ssh_key_r.status_code == requests.codes.ok:
                break
            else:
                print "Could not get ssh_key - New try [%d]" % (ssh_try)
                time.sleep(2)
                ssh_try += 1
        self.ssh_key = ssh_key_r.text

    def write_ssh_key(self, user=None):
        if not hasattr(self, 'ssh_key'):
            self.set_ssh_key()
        with open("/home/ec2-user/.ssh/authorized_keys", "w") as ssh_key_file:
            ssh_key_file.write("%s\n" % (self.ssh_key))
            print "=====\tAuthorized keys\t=====\n%s\n=====" % (self.ssh_key)
        if user:
            user_path = "/home/%s/.ssh/authorized_keys" % (user)
            with open(user_path, "w") as ssh_key_file:
                ssh_key_file.write("%s\n" % (self.ssh_key))

    def set_local_ipv4(self):
        local_ipv4_r = requests.get("%s/%s" % (self.ec2_metadata_url, self.ec2_metadata_ipv4))
        self.local_ipv4 = local_ipv4_r.text

    def __init__(self):
        self.ec2_userdata_url = "http://169.254.169.254/latest/user-data"
        self.ec2_metadata_url = "http://169.254.169.254/latest/meta-data"
        self.ec2_conffile_path = "/etc/init_scripts/.ec2_conf.cfg"
        self.ec2_metadata_awszone = "placement/availability-zone/"
        self.ec2_metadata_hwaddr = "network/interfaces/macs"
        self.ec2_metadata_vpccidr = "vpc-ipv4-cidr-block"
        self.ec2_metadata_subnetcidr = "subnet-ipv4-cidr-block"
        self.ec2_metadata_key = "public-keys/0/openssh-key/"
        self.ec2_metadata_ipv4 = "local-ipv4"
        self.ec2_metadata_euca_host = "local-hostname"
        self.ec2_metadata_instance_id = "instance-id"
