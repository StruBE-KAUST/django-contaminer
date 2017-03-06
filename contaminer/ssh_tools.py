# -*- coding : utf-8 -*-

##    Copyright (C) 2017 King Abdullah University of Science and Technology
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
    Communication with the cluster or supercomputer through a SSH connection
    ========================================================================

    This module provides a layer to allow an easy communication between Django
    and the cluster or supercomputer where ContaMiner is.
    Configuration is done in apps.py
"""

import os
import paramiko
from paramiko import SSHException
import logging
import errno
import socket

from django.conf import settings

from .apps import ContaminerConfig

class SSHChannel(paramiko.SSHClient):
    """
        A connection to the cluster or supercomputer
        This class should always be used with 'with' statement
    """
    def __enter__(self):
        """ Implements with statement """
        log = logging.getLogger(__name__)
        log.debug("Entering function")
        self.__connect__()
        log.debug("Exiting function")
        return self

    def __exit__(self, *args):
        """ Implements with statement """
        log = logging.getLogger(__name__)
        log.debug("Entering function")
        self.close()
        log.debug("Exiting function")

    def __get_config__(self):
        """ Configure SSH parameters """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not hasattr(self, 'sshconfig') or self.sshconfig == {}:
            log.debug("Configuring SSH connection")
            self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            contaminer_config = ContaminerConfig()
            self.sshconfig = {
                    'hostname': contaminer_config.ssh_hostname,
                    'port': contaminer_config.ssh_port,
                    'username': contaminer_config.ssh_username,
                    'password': contaminer_config.ssh_password,
                    'key_filename': contaminer_config.ssh_identityfile,
                    }

        return self.sshconfig

        log.debug("Exiting function")

    def __connect__(self):
        """ Open SSH connection to host """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        ssh_config = self.__get_config__()

        log.debug("Open SSH connection")
        super(SSHChannel, self).connect(**ssh_config)

        log.debug("Exiting function")

    def get_contabase(self):
        """ Get the full ContaBase from the cluster """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        command = "sh " + os.path.join(
                ContaminerConfig().ssh_contaminer_location,
                "contaminer") \
                + " display"
        with self as sshChannel:
            (_, stdout, stderr) = sshChannel.exec_command(command)
            stdout = stdout.read()
            stderr = stderr.read()

        if stderr is not '':
            raise RuntimeError(stderr)

        return stdout

    def read_file(self, remote_path):
        """ Read a remote and return the content as a string """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        command = "cat " + str(remote_path)
        with self as sshChannel:
            (_, stdout, stderr) = sshChannel.exec_command(command)
            stdout = stdout.read()
            stderr = stderr.read()

        if stderr is not '':
            raise RuntimeError(stderr)

        return stdout


class SFTPChannel(SSHChannel):
    """
        An SFTP connection to the cluster or superconputer
    """
    def __init__(self):
        self.sftpclient = None

    def __enter__(self):
        """ Implements with statement """
        log = logging.getLogger(__name__)
        log.debug("Enter")
        self.__connect__()
        log.debug("Exit")
        return self.sftpclient

    def __exit__(self, *args):
        """ Implements with statement """
        log = logging.getLogger(__name__)
        log.debug("Enter")
        self.sftpclient.close()
        super(SFTPChannel, self).__exit__(args)
        self.sftpclient = None
        log.debug("Exit")

    def __connect__(self):
        """ Open SFTP connection to host """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        log.debug("Open SSH connection")
        super(SFTPChannel, self).__connect__()

        log.debug("Open SFTP connection")
        self.sftpclient = self.open_sftp()

        log.debug("Exiting function")

    def send_file(self, filename, remote_directory):
        """ Send filename to host through SFTP on the remote_directory """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        remote_filename = os.path.join(
                remote_directory,
                os.path.basename(filename)
                )

        with self as sftpClient:
            log.info("Send " + str(filename) + " to " + str(remote_filename))
            sftpClient.put(filename, remote_filename, confirm = True)

        log.debug("Exiting function")

    def upload_to_contaminer(self, filename):
        """ Send filename to host and put it in ContaMiner work dir """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        remote_directory = ContaminerConfig().ssh_work_directory

        self.send_file(filename, remote_directory)

        log.debug("Exit")

    def write_file(self, remote_filename, content):
        """ Write content in filename in remote_directory """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        with self as sftpClient:
            log.info("Write in remote file: " + str(remote_filename))
            with sftpClient.open(remote_filename, 'w') as remote_file:
                remote_file.write(content)

        log.debug("Exit")

    def get_file(self, remote_filename, local_filename):
        """ Get remote_filename from host through SFTP """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        with self as sftpClient:
            log.info("Get " + str(remote_filename) \
                    + " to " + str(local_filename))
            sftpClient.get(remote_filename, local_filename)

        log.debug("Exit")

    def download_from_contaminer(self, filename, local_filename):
        """ Download file from ContaMiner work dir and put it in localdir """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        remote_directory = ContaminerConfig().ssh_work_directory
        remote_filename = os.path.join(remote_directory, filename)

        self.get_file(remote_filename, local_filename)

        log.debug("Exit")
