#!/usr/bin/env python

import os
import sys
import git
import json
import codecs
import requests
import ConfigParser

from c_cfgFILE import cfgFILE

class cfgGIT(object):

    # Local config file values

    def set_local_config(self, key):
        value  = self.local_git_config.get_value(self.section, key)
        setattr(self, key, value)

    def set_repo(self):
        if not hasattr(self, 'local_working_dir'):
            self.set_local_config("local_working_dir")
        self.repo = git.Repo(self.local_working_dir)

    # Git Functions

    def git_get_current_branch(self):
        with os.popen("cd %s ; git status | head -1 | sed 's/^$*.*_//g'" % (self.local_working_dir)) as branch_id_cmd:
            self.branch_id = branch_id_cmd.read().strip()
        with os.popen("cd %s ; git status | head -1 | awk '/branch_/{print $NF}'" % (self.local_working_dir)) as branch_name_cmd:
            self.branch_name = branch_name_cmd.read().strip()

    def git_status(self):
        self.set_repo()
        print self.repo.git.status()

    def git_fetch(self):
        if not hasattr(self, 'repo'):
            self.set_repo()
        self.repo.git.fetch('--tags')

    def git_checkout(self, new):
        if not hasattr(self, 'repo'):
            self.set_repo()
        if new is True:
            print "===\tNew update - Checking out to  branch_%s\t===" % (self.remote_git_tag)
            self.repo.git.checkout(self.remote_git_tag, '-b', "branch_%s" % (self.remote_git_tag))
        else:
            print "===\tCheckout to branch_%s\t===" % (self.remote_git_tag)
            self.repo.git.checkout("branch_%s" % (self.remote_git_tag))

    # Remote config

    def get_remote_config(self):
        if not hasattr(self, 'remote_config_url'):
            self.set_local_config("remote_config_url")
        remote_config_r = requests.get("%s" % (self.remote_config_url))
        remote_config = remote_config_r.text
        self.remote_config = remote_config

        if not hasattr(self, 'repo'):
            self.set_repo()
        self.remote_config_file = "%s/.configuration_git/remote_config_git.config" % (self.local_working_dir)
        with open(self.remote_config_file, "w") as remote_config_fd:
            remote_config_fd.write(self.remote_config)

        with open(self.remote_config_file, "r") as remote_config_fd:
           self.remote_git_config = ConfigParser.ConfigParser()
           self.remote_git_config.readfp(remote_config_fd)

    def set_remote_config(self, key):
        if not hasattr(self, 'remote_git_config'):
            self.get_remote_config()

        value = self.remote_git_config.get(self.section, key)
        setattr(self, key, value)

    # Main Functions

    def run_pre_script(self):

        if not hasattr (self, 'pre_script'):
            self.set_local_config('pre_script')

        if os.path.isfile(self.pre_script) and os.access(self.pre_script, os.X_OK):
            os.system(self.pre_script)
        else:
            print "%s not able to run script" % (self.pre_script)

    def run_post_script(self):
        if not hasattr (self, 'post_script'):
            self.set_local_config('post_script')

        if os.path.isfile(self.post_script) and os.access(self.post_script, os.X_OK):
            os.system(self.post_script)
        else:
            print "%s not able to run script" % (self.run_post_script)

    def check_existing_branch(self):
        if not hasattr(self, 'repo'):
            self.set_repo()
        with os.popen("cd %s ; git branch | sed 's/ //g' | sed 's/\*//g'" % (self.local_working_dir)) as branches_cmd:
            branches = branches_cmd.read().splitlines()
        if "branch_%s" % (self.remote_git_tag) in branches:
            return True
        else:
            return False


    def update(self, reboot=True):
        self.set_repo()
        self.git_get_current_branch()
        print ("Local branch|id\t=\t%s|%s\nRemote_tag\t=\t%s" %
               (self.branch_name, self.branch_id, self.remote_git_tag))

        self.git_fetch()

        if self.branch_name == "branch_%s" % (self.remote_git_tag):
            sys.exit("Versions are the same - Exiting")
            sys.exit(0)
        else:
            if reboot is True:
                self.run_pre_script()
                print "Running pre script"
            if self.check_existing_branch() is True:
                self.git_checkout(False)
            else:
                self.git_checkout(True)
            if reboot is True:
                print "Running post script"
                self.run_post_script()

    def __init__(self, section, config_file=".configuration_git/git.config"):
        self.section = section
        self.local_git_config = cfgFILE(config_file)
        self.local_git_config.get_conf()
