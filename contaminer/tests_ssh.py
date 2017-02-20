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
    Testing module for cluster.py
    =============================

    This module contains unitary tests for the communication tools which
    manages communicating with the cluster
"""

from django.test import TestCase
import mock

from .ssh_tools import SSHChannel
from .ssh_tools import SFTPChannel


class SSHChannelTestCase(TestCase):
    """
        Test the correct communication with the cluster
    """
    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.' \
            + 'set_missing_host_key_policy')
    @mock.patch('contaminer.ssh_tools.paramiko.AutoAddPolicy')
    def test_configure_accepts_new_host_keys(
            self,
            mock_paramiko_policy,
            mock_paramiko_set_policy,
            mock_config):
        sshChannel = SSHChannel()
        return_value = mock.MagicMock()
        return_value.ssh_hostname = 'localhost'
        return_value.ssh_port = 22
        return_value.ssh_username = 'username'
        return_value.ssh_password = 'password'
        return_value.ssh_identityfile = 'identityfile'
        mock_config.return_value = return_value
        mock_paramiko_policy.return_value = "AutoAddPolicy"
        sshChannel.__get_config__()
        mock_paramiko_set_policy.assert_called_once_with("AutoAddPolicy")

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    def test_configure_uses_cache_results(self, mock_config):
        sshChannel = SSHChannel()
        return_value = mock.MagicMock()
        return_value.ssh_hostname = 'localhost'
        return_value.ssh_port = 22
        return_value.ssh_username = 'username'
        return_value.ssh_password = 'password'
        return_value.ssh_identityfile = 'identityfile'
        mock_config.return_value = return_value
        sshChannel.__get_config__()
        sshChannel.__get_config__()
        mock_config.assert_called_once()

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    def test_configure_returns_expected_results(self, mock_config):
        sshChannel = SSHChannel()
        return_value = mock.MagicMock()
        return_value.ssh_hostname = 'localhost'
        return_value.ssh_port = 22
        return_value.ssh_username = 'username'
        return_value.ssh_password = 'password'
        return_value.ssh_identityfile = 'identityfile'
        mock_config.return_value = return_value
        sshconfig = sshChannel.__get_config__()
        self.assertEqual(sshconfig['hostname'], "localhost")
        self.assertEqual(sshconfig['port'], 22)
        self.assertEqual(sshconfig['username'], "username")
        self.assertEqual(sshconfig['password'], "password")
        self.assertEqual(sshconfig['key_filename'], "identityfile")

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    def test_configure_returns_expected_cached_results(self, mock_config):
        sshChannel = SSHChannel()
        return_value = mock.MagicMock()
        return_value.ssh_hostname = 'localhost'
        return_value.ssh_port = 22
        return_value.ssh_username = 'username'
        return_value.ssh_password = 'password'
        return_value.ssh_identityfile = 'identityfile'
        mock_config.return_value = return_value
        sshChannel.__get_config__()
        sshconfig = sshChannel.__get_config__()
        self.assertEqual(sshconfig['hostname'], "localhost")
        self.assertEqual(sshconfig['port'], 22)
        self.assertEqual(sshconfig['username'], "username")
        self.assertEqual(sshconfig['password'], "password")
        self.assertEqual(sshconfig['key_filename'], "identityfile")

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.connect')
    def test_connect_takes_configuration(self, mock_paramiko, mock_config):
        sshChannel = SSHChannel()
        return_value = mock.MagicMock()
        return_value.ssh_hostname = 'localhost'
        return_value.ssh_port = 22
        return_value.ssh_username = 'username'
        return_value.ssh_password = 'password'
        return_value.ssh_identityfile = 'identityfile'
        mock_config.return_value = return_value
        sshChannel.__connect__()
        mock_paramiko.assert_called_once_with(
                hostname = 'localhost',
                port = 22,
                username = 'username',
                password = 'password',
                key_filename = 'identityfile',
                )

    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.connect')
    def test___enter___returns_self(self, mock_paramiko):
        sshChannel = SSHChannel()
        sshChannel2 = sshChannel.__enter__()
        self.assertEqual(sshChannel, sshChannel2)

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.exec_command')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.connect')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.close')
    def test_get_contabase_closes_channel(self, mock_close, mock_connect,
            mock_command, mock_config):
        sshChannel = SSHChannel()
        config = mock.MagicMock()
        config.ssh_contaminer_location = "/home/user/ContaMiner"
        mock_config.return_value = config
        stdout = mock.MagicMock()
        stdout.read.return_value = "2"
        stderr = mock.MagicMock()
        stderr.read.return_value = ""
        mock_command.return_value = (0, stdout, stderr)
        sshChannel.get_contabase()
        self.assertTrue(mock_close.called)

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.exec_command')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.connect')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.close')
    def test_get_contabase_closes_channel_on_exception(self,
            mock_close, mock_connect, mock_command, mock_config):
        sshChannel = SSHChannel()
        config = mock.MagicMock()
        config.ssh_contaminer_location = "/home/user/ContaMiner"
        mock_config.return_value = config
        stdout = mock.MagicMock()
        stdout.read.return_value = "2"
        stderr = mock.MagicMock()
        stderr.read.return_value = "3"
        mock_command.return_value = (0, stdout, stderr)
        try:
            sshChannel.get_contabase()
        except RuntimeError:
            pass
        self.assertTrue(mock_close.called)

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.exec_command')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.connect')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.close')
    def test_get_contabase_sends_correct_command(self, mock_close, mock_connect,
            mock_command, mock_config):
        sshChannel = SSHChannel()
        config = mock.MagicMock()
        config.ssh_contaminer_location = "/home/user/ContaMiner"
        mock_config.return_value = config
        stdout = mock.MagicMock()
        stdout.read.return_value = "2"
        stderr = mock.MagicMock()
        stderr.read.return_value = ""
        mock_command.return_value = (0, stdout, stderr)
        sshChannel.get_contabase()
        mock_command.assert_called_once_with(
            "sh /home/user/ContaMiner/contaminer display")

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.exec_command')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.connect')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.close')
    def test_get_contabase_gives_correct_results(self, mock_close, mock_connect,
            mock_command, mock_config):
        sshChannel = SSHChannel()
        config = mock.MagicMock()
        config.ssh_contaminer_location = "/home/user/ContaMiner"
        mock_config.return_value = config
        stdout = mock.MagicMock()
        stdout.read.return_value = "2"
        stderr = mock.MagicMock()
        stderr.read.return_value = ""
        mock_command.return_value = (0, stdout, stderr)
        answer = sshChannel.get_contabase()
        self.assertEqual(answer, "2")

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.exec_command')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.connect')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.close')
    def test_get_contabase_raises_exception_with_stderr(self,
            mock_close, mock_connect, mock_command, mock_config):
        sshChannel = SSHChannel()
        config = mock.MagicMock()
        config.ssh_contaminer_location = "/home/user/ContaMiner"
        mock_config.return_value = config
        stdout = mock.MagicMock()
        stdout.read.return_value = "2"
        stderr = mock.MagicMock()
        stderr.read.return_value = "3"
        mock_command.return_value = (0, stdout, stderr)
        with self.assertRaisesMessage(RuntimeError, "3"):
            answer = sshChannel.get_contabase()


class SFTPChannelTestCase(TestCase):
    """
        Test the correct file sending/retrieveing with the remote server
    """
    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.SSHChannel.open_sftp')
    def test_connect_connects_to_ssh(self, mock_sftp, mock_connect):
        sftpChannel = SFTPChannel()
        sftpChannel.__connect__()
        self.assertTrue(mock_connect.called)

    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.SSHChannel.open_sftp')
    def test_connect_connects_to_sftp(self, mock_sftp, mock_connect):
        sftpChannel = SFTPChannel()
        sftpChannel.__connect__()
        self.assertTrue(mock_sftp.called)

    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.SSHChannel.open_sftp')
    def test_connect_changes_sftpclient_attribute(self, mock_sftp, mock_connect):
        mock_sftp.return_value = "sftp_client"
        sftpChannel = SFTPChannel()
        sftpChannel.__connect__()
        self.assertEqual(sftpChannel.sftpclient, "sftp_client")

    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.open_sftp')
    @mock.patch('contaminer.ssh_tools.paramiko.SFTPClient.close')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.close')
    def test_send_file_closes_connections(self, mock_ssh_close,
            mock_open_sftp, mock_sftp_close, mock_connect):
        sftpChannel = SFTPChannel()
        sftpChannel.send_file("foo.txt", "/remote/dir")
        self.assertTrue(mock_ssh_close.called)
        self.assertTrue(mock_sftp_close.called)

    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.open_sftp')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.__exit__')
    def test_send_file_connects(self, mock_exit,
            mock_open_sftp, mock_connect):
        sftpChannel = SFTPChannel()
        sftpChannel.send_file("foo.txt", "/remote/dir")
        self.assertTrue(mock_connect.called)
        self.assertTrue(mock_open_sftp.called)

    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.open_sftp')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.__exit__')
    def test_send_file_sends_to_correct_location(self, mock_ssh_close,
            mock_open_sftp, mock_connect):
        client = mock.MagicMock()
        mock_open_sftp.return_value = client
        sftpChannel = SFTPChannel()
        sftpChannel.send_file("foo.txt", "/remote/dir")
        client.put.called_once_with("foo.txt", "/remote/dir/foo.txt")

    @mock.patch('contaminer.ssh_tools.ContaminerConfig')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.send_file')
    def test_upload_calls_send_with_good_params(self, mock_send, mock_config):
        config = mock.MagicMock()
        config.ssh_work_directory = "/work/dir"
        mock_config.return_value = config
        SFTPChannel().upload_to_contaminer("foo.txt")
        mock_send.assert_called_once_with("foo.txt", "/work/dir")

    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.open_sftp')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.__exit__')
    def test_write_file_connects(self, mock_exit,
            mock_open_sftp, mock_connect):
        sftpChannel = SFTPChannel()
        sftpChannel.write_file("/remote/dir/foo.txt", "bar\n")
        mock_connect.called_once()
        mock_open_sftp.called_once()

    @mock.patch('contaminer.ssh_tools.SSHChannel.__connect__')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.open_sftp')
    @mock.patch('contaminer.ssh_tools.paramiko.SFTPClient.close')
    @mock.patch('contaminer.ssh_tools.paramiko.SSHClient.close')
    def test_write_file_closes_connections(self, mock_ssh_close,
            mock_open_sftp, mock_sftp_close, mock_connect):
        sftpChannel = SFTPChannel()
        sftpChannel.write_file("/remote/dir/foo.txt", "bar\n")
        mock_ssh_close.called_once()
        mock_sftp_close.called_once()

    @mock.patch('contaminer.ssh_tools.SFTPChannel.__enter__')
    @mock.patch('contaminer.ssh_tools.SFTPChannel.__exit__')
    def test_write_file_calls_correct_write(self, mock_exit, mock_enter):
        mock_file = mock.MagicMock()
        mock_client = mock.MagicMock()
        mock_client.open.return_value = mock_file
        mock_enter.return_value = mock_client
        sftpChannel = SFTPChannel()
        sftpChannel.write_file("/remote/dir/foo.txt", "bar\n")
        mock_client.open.called_once_with("/remote/dir/foo.txt", 'w')
        mock_file.write.called_once_with("bar\n")
