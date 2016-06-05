# -*- coding : utf-8 -*-

##    Copyright (C) 2015 Hungler Arnaud
##
##    This program is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.
##
##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
##    GNU General Public License for more details.
##
##    You should have received a copy of the GNU General Public License along
##    with this program; if not, write to the Free Software Foundation, Inc.,
##    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
    Communication with the cluster through a SSH connection
    =======================================================

    This module provides a layer to allow an easy communication between Django
    and the cluster where ContaMiner is. Configuration is done in apps.py
"""

import os
import paramiko
import logging
import errno

from .apps import ContaminerConfig

class SSHChannel():
    """
        A connection to the cluster or supercomputer
    """

    def __init__(self):
        self.sshclient = paramiko.SSHClient()
        self.sshconfig = {}
        self.sftpclient = None
        self.is_configured = False
        self.is_connected = False

    def configure(self):
        log = logging.getLogger(__name__)
        log.debug("Entering function with arg : \n\
                self : " + str(self))

        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshconfig = {
                'hostname': ContaminerConfig.ssh_hostname,
                'port': ContaminerConfig.ssh_port,
                'username': ContaminerConfig.ssh_username,
                'password': ContaminerConfig.ssh_password,
                'key_filename': ContaminerConfig.ssh_identityfile,
                }

        self.is_configured = True

    def connectSSH(self):
        if not self.is_configured:
            self.configure()

        self.sshclient.connect(**self.sshconfig)

        self.is_connected = True

    def connectFTP(self):
        if not self.is_connected:
            self.connectSSH()

        self.sftpclient = self.sshclient.open_sftp()

    def send_file(self, filename):
        if not self.sftpclient:
            self.connectFTP()

        remote_filename = os.path.join(ContaminerConfig.ssh_work_directory,
                os.path.basename(filename))

        self.sftpclient.put(filename, remote_filename)

    def get_file(self, remote_filename, local_filename):
        if not self.sftpclient:
            self.connectFTP()

        self.sftpclient.get(remote_filename, local_filename)

    def command(self, command):
        if not self.is_connected:
            self.connectSSH()
        _, stdout, stderr = self.sshclient.exec_command(command)
        return (stdout.readlines(), stderr.readlines())

    def launch_contaminer(self, filename, listname):
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                self : " + str(self) +  "\n\
                filename : " + str(filename) + "\n\
                listname : " + str(listname))
        cm_bin_path = ContaminerConfig.ssh_contaminer_location + "/contaminer"
        remote_filename = os.path.basename(filename)
        remote_listname = os.path.basename(listname)

        cm_cd = "cd " + ContaminerConfig.ssh_work_directory

        command = cm_cd + " && "\
            + cm_bin_path + " "\
            + str(remote_filename) + " "\
            + str(remote_listname)

        log.warning("Debug : " + command)
        res = self.command(command)
        return res

    def get_result(self, job_id):
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                self : " + str(self) + "\n\
                job_id : " + str(job_id))

        tmp_dir = ContaminerConfig.tmp_dir
        try:
            os.makedirs(tmp_dir)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(tmp_dir):
                pass
            else:
                raise

        job_tmp_dir = os.path.join(tmp_dir, "contaminer_" + str(job_id))
        try:
            os.makedirs(job_tmp_dir)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(job_tmp_dir):
                pass
            else:
                raise

        remote_result_dir = "contaminer_" + str(job_id)
        remote_result_file = ContaminerConfig.ssh_work_directory
        remote_result_file = os.path.join(remote_result_file, remote_result_dir)
        remote_result_file = os.path.join(remote_result_file, "results.txt")
        local_result_file = os.path.join(job_tmp_dir, "results.txt")

        self.get_file(remote_result_file, local_result_file)
        log.debug(job_tmp_dir)

        return local_result_file
