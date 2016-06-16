# -*- coding : utf-8 -*-

##    Copyright (C) 2016 Hungler Arnaud
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
from paramiko import SSHException
import logging
import errno
import socket

from django.conf import settings

from .apps import ContaminerConfig

class SSHChannel():
    """ A connection to the cluster or supercomputer """

    def __init__(self):
        self.sshclient = paramiko.SSHClient()
        self.sshconfig = {}
        self.sftpclient = None
        self.is_configured = False


    def is_ssh_connected(self):
        """ Test if SSH connection is open and active """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        try:
            self.sshclient.exec_command('ls')
        except SSHException:
            log.warning("SSH connection is closed")
            return False
        except AttributeError:
            log.debug("SSH connection is not initialized")
            return False

        log.debug("Exiting function")
        return True


    def is_sftp_connected(self):
        """ Test if SFTP connection is open and active """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        try:
            self.sftpclient.listdir('.')
        except socket.error as e:
            if e.message == 'Socket is closed':
                log.warning("SFTP connection is closed")
                return False
        except AttributeError:
            log.debug("Connection is not initialized")
            return False

        log.debug("Exiting function")
        return True


    def configure(self):
        """ Configure SSH parameters """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sshconfig = {
                'hostname': ContaminerConfig().ssh_hostname,
                'port': ContaminerConfig().ssh_port,
                'username': ContaminerConfig().ssh_username,
                'password': ContaminerConfig().ssh_password,
                'key_filename': ContaminerConfig().ssh_identityfile,
                }

        self.is_configured = True

        log.debug("Exiting function")


    def connectSSH(self):
        """ Open SSH connection to host """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not self.is_configured:
            log.debug("Configure channel")
            self.configure()

        log.debug("Open SSH connection")
        self.sshclient.connect(**self.sshconfig)

        log.debug("Exiting function")


    def connectSFTP(self):
        """ Open SFTP connection to host """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not self.is_ssh_connected():
            log.debug("Open SSH connection")
            self.connectSSH()

        log.debug("Open SFTP connection")
        self.sftpclient = self.sshclient.open_sftp()

        log.debug("Exiting function")


    def send_file(self, filename):
        """ Send filename to host through SFTP """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not self.is_sftp_connected():
            log.debug("Open SFTP connection")
            self.connectSFTP()

        remote_filename = os.path.join(
                ContaminerConfig().ssh_work_directory,
                os.path.basename(filename)
                )

        log.debug("Send " + str(filename) + " to " + str(remote_filename))
        self.sftpclient.put(filename, remote_filename)

        log.debug("Exiting function")


    def get_file(self, remote_filename, local_filename):
        """ Get remote_filename from host through SFTP """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not self.is_sftp_connected():
            log.debug("Open SFTP connection")
            self.connectSFTP()

        log.debug("Get " + str(remote_filename) + " to " + str(local_filename))
        self.sftpclient.get(remote_filename, local_filename)

        log.debug("Exiting function")


    def command(self, command):
        """ Execute command on remote host """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not self.is_ssh_connected():
            log.debug("Open SSH connection")
            self.connectSSH()

        log.debug("Execute " + str(command))
        _, stdout, stderr = self.sshclient.exec_command(command)

        log.debug("Exiting function")
        return (stdout.readlines(), stderr.readlines())


    def launch_contaminer(self, filename, listname):
        """ Execute ContaMiner on the remote host """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                filename : " + str(filename) + "\n\
                listname : " + str(listname))

        cm_bin_path = ContaminerConfig().ssh_contaminer_location + "/contaminer"
        remote_filename = os.path.basename(filename)
        remote_listname = os.path.basename(listname)

        cm_cd = "cd " + ContaminerConfig().ssh_work_directory

        command = cm_cd + " && "\
            + cm_bin_path + " "\
            + str(remote_filename) + " "\
            + str(remote_listname)

        log.debug("Execute command on remote host : \n" + command)
        stdout, stderr = self.command(command)

        log.debug("stdout : " + str(stdout))
        log.debug("stderr : " + str(stderr))

        if stderr is not "":
            log.warning("Standard error is not empty : \n" + str(stderr))


        log.debug("Exiting function")


    def get_final(self, job_id, contaminant, pack_nb, space_group):
        """ Get final files for the specified task """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                job_id : " + str(job_id) + "\n\
                pack_nb : " + str(pack_nb) + "\n\
                space_group : " + str(space_group))

        remote_result_rel_dir = "contaminer_" + str(job_id)
        remote_task_rel_dir = contaminant + "_"\
                + str(pack_nb) + "_"\
                + space_group.replace(' ', '-')

        remote_task_abs_dir = os.path.join(
                ContaminerConfig().ssh_work_directory,
                remote_result_rel_dir,
                remote_task_rel_dir,
                "results_solve")

        remote_pdb_file = os.path.join(
                remote_task_abs_dir,
                "final.pdb"
                )
        log.debug("Remote PDB file : " + remote_pdb_file)

        remote_mtz_file = os.path.join(
                remote_task_abs_dir,
                "final.mtz"
                )
        log.debug("Remote MTZ file : " + remote_mtz_file)

        local_dir = os.path.join(
                settings.STATIC_ROOT,
                "contaminer_" + str(job_id)
                )
        try:
            os.makedirs(local_dir)
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(local_dir):
                pass
            else:
                raise

        local_global_file = os.path.join(
                local_dir,
                contaminant + '_'\
                        + str(pack_nb) + '_'\
                        + space_group.replace(' ','-'))
        local_pdb_file = local_global_file + ".pdb"
        log.debug("Local PDB file : " + local_pdb_file)
        local_mtz_file = local_global_file + ".mtz"
        log.debug("Local MTZ file : " + local_mtz_file)

        self.get_file(remote_pdb_file, local_pdb_file)
        self.get_file(remote_mtz_file, local_mtz_file)

        log.debug("Exiting function")


    def get_result(self, job_id):
        """ Retrieve result file for the specified job """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                job_id : " + str(job_id))

        tmp_dir = ContaminerConfig().tmp_dir
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
        log.debug("Job tmp directory : " + job_tmp_dir)

        remote_result_dir = "contaminer_" + str(job_id)
        remote_result_file = ContaminerConfig().ssh_work_directory
        remote_result_file = os.path.join(remote_result_file, remote_result_dir)
        remote_result_file = os.path.join(remote_result_file, "results.txt")
        log.debug("Remote result file : " + remote_result_file)

        local_result_file = os.path.join(job_tmp_dir, "results.txt")
        log.debug("Local result file : " + local_result_file)

        self.get_file(remote_result_file, local_result_file)

        log.debug("Exiting function")
        return local_result_file
