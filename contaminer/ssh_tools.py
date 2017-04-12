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
Communication with the cluster or supercomputer through a SSH connection.

This module provides a layer to allow an easy communication between Django
and the cluster or supercomputer where ContaMiner is.
The configuration is done in apps.py
"""

import os
import logging
import paramiko

from django.apps import apps

class SSHChannel(paramiko.SSHClient):
    """
    A connection to the cluster or supercomputer.

    This class should always be used with 'with' statement.
    """

    def __init__(self, *args, **kwargs):
        """Create a new channel."""
        super(SSHChannel, self).__init__(*args, **kwargs)
        self.sshconfig = {}

    def __enter__(self):
        """Implement 'with' statement."""
        log = logging.getLogger(__name__)
        log.debug("Enter")
        self.__connect__()
        log.debug("Exit")
        return self

    def __exit__(self, *args):
        """Implement 'with' statement."""
        log = logging.getLogger(__name__)
        log.debug("Enter")
        self.close()
        log.debug("Exit")

    def __get_config__(self):
        """Configure SSH parameters."""
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if self.sshconfig == {}:
            log.debug("Configuring SSH connection")
            self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            contaminer_config = apps.get_app_config('contaminer')
            self.sshconfig = {
                'hostname': contaminer_config.ssh_hostname,
                'port': contaminer_config.ssh_port,
                'username': contaminer_config.ssh_username,
                'password': contaminer_config.ssh_password,
                'key_filename': contaminer_config.ssh_identityfile,
                }

        log.debug("Exit")
        return self.sshconfig

    def __connect__(self):
        """Open SSH connection to host."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        ssh_config = self.__get_config__()

        log.debug("Open SSH connection")
        super(SSHChannel, self).connect(**ssh_config)

        log.debug("Exit")

    def get_contabase(self):
        """Get the full ContaBase from the cluster."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        command = "sh " + os.path.join(
            apps.get_app_config('contaminer').ssh_contaminer_location,
            "contaminer") \
            + " display"
        stdout = self.exec_command(command)

        log.debug("Exit")
        return stdout

    def exec_command(self, *args, **kwargs):
        """Open a channel then execute command on remote destination."""
        log = logging.getLogger(__name__)
        log.debug("Enter with args: " + str(args) + " " + str(kwargs))

        with self as ssh_channel:
            (_, stdout, stderr) = super(SSHChannel, ssh_channel).exec_command(
                *args,
                **kwargs)
            stdout = stdout.read()
            stderr = stderr.read()

        if stderr is not '':
            raise RuntimeError(stderr)

        log.debug("Exit with arg: " + str(stdout))
        return stdout

    def read_file(self, remote_path):
        """Read a remote file and return the content as a string."""
        log = logging.getLogger(__name__)
        log.debug("Enter with arg: " + str(remote_path))

        command = "cat " + str(remote_path)
        with self as ssh_channel:
            stdout = ssh_channel.exec_command(command)

        log.debug("Exit with arg: " + str(stdout))
        return stdout


class SFTPChannel(SSHChannel):
    """An SFTP connection to the cluster or supercomputeri."""

    def __init__(self):
        """Create a new SFTP connection."""
        super(SFTPChannel, self).__init__()
        self.sftpclient = None

    def __enter__(self):
        """Implement 'with' statement."""
        log = logging.getLogger(__name__)
        log.debug("Enter")
        self.__connect__()
        log.debug("Exit")
        return self.sftpclient

    def __exit__(self, *args):
        """Implement 'with' statement."""
        log = logging.getLogger(__name__)
        log.debug("Enter")
        self.sftpclient.close()
        super(SFTPChannel, self).__exit__(args)
        self.sftpclient = None
        log.debug("Exit")

    def __connect__(self):
        """Open SFTP connection to host."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        log.debug("Open SSH connection")
        super(SFTPChannel, self).__connect__()

        log.debug("Open SFTP connection")
        self.sftpclient = self.open_sftp()

        log.debug("Exit")

    def send_file(self, filename, remote_directory):
        """Send filename to host through SFTP on the remote_directory."""
        log = logging.getLogger(__name__)
        log.debug("Enter with args: " + str(filename) + " " \
                + str(remote_directory))

        remote_filename = os.path.join(
            remote_directory,
            os.path.basename(filename)
            )

        with self as sftp_client:
            log.info("Send " + str(filename) + " to " + str(remote_filename))
            try:
                sftp_client.put(filename, remote_filename, confirm=True)
            except IOError as exception:
                log.warning("Unable to upload file.")
                raise exception

        log.debug("Exit")

    def upload_to_contaminer(self, filename):
        """Send filename to host and put it in ContaMiner work directory."""
        log = logging.getLogger(__name__)
        log.debug("Enter with arg: " + str(filename))

        remote_directory = apps.get_app_config('contaminer').ssh_work_directory
        self.send_file(filename, remote_directory)

        log.debug("Exit")

    def write_file(self, remote_filename, content):
        """Write content in remote filename on host."""
        log = logging.getLogger(__name__)
        log.debug("Enter with args: " + str(remote_filename) + " " \
                + str(content))

        with self as sftp_client:
            log.info("Write in remote file: " + str(remote_filename))
            with sftp_client.open(remote_filename, 'w') as remote_file:
                remote_file.write(content)

        log.debug("Exit")

    def get_file(self, remote_filename, local_filename):
        """Get remote_filename from host through SFTP."""
        log = logging.getLogger(__name__)
        log.debug("Enter with args: " + str(remote_filename) + " " \
                + str(local_filename))

        with self as sftp_client:
            log.info("Get " + str(remote_filename) \
                    + " to " + str(local_filename))
            sftp_client.get(remote_filename, local_filename)

        log.debug("Exit")

    def download_from_contaminer(self, filename, local_filename):
        """Download file from ContaMiner work dir and put it in localdir."""
        log = logging.getLogger(__name__)
        log.debug("Enter with args: " + str(filename) + " " \
                + str(local_filename))

        remote_directory = apps.get_app_config('contaminer').ssh_work_directory
        remote_filename = os.path.join(remote_directory, filename)
        self.get_file(remote_filename, local_filename)

        log.debug("Exit")
