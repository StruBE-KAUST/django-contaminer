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
This module provides the application configuration.

It first reads the config.ini file for contaminer, then provides this
configuration through the class ContaminerConfig
"""

import os
import ConfigParser
import logging

from django.apps import AppConfig


class ContaminerConfig(AppConfig):
    """Configuration of contaminer application."""

    # pylint: disable=too-many-instance-attributes

    name = 'contaminer'
    verbose_name = 'ContaMiner'

    def __init__(self, *args, **kwargs):
        """Create a new configuration."""
        super(ContaminerConfig, self).__init__(*args, **kwargs)

        # Init attributes
        self.admin_mail = None
        self.noreply_mail = None
        self.threshold = None
        self.bad_model_coverage_threshold = None
        self.bad_model_identity_threshold = None
        self.ssh_hostname = None
        self.ssh_port = None
        self.ssh_username = None
        self.ssh_password = None
        self.ssh_identityfile = None
        self.ssh_contaminer_location = None
        self.ssh_work_directory = None
        self.tmp_dir = None

    def ready(self):
        """Populate the configuration from config.ini."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        base_dir = os.path.dirname(os.path.abspath(__file__))
        config = ConfigParser.ConfigParser()
        config_file = os.path.join(base_dir, "config.ini")
        res = config.read(config_file)

        if res == []:
            log.error("config.ini does not exist.")
            log.error("Use config.template to create your config.ini")
            raise IOError

        self.admin_mail = config.get("DEFAULT", "admin_mail")
        self.noreply_mail = config.get("DEFAULT", "noreply_mail")
        self.threshold = int(config.get("THRESHOLDS", "positive"))
        self.bad_model_coverage_threshold = int(config.get(
            "THRESHOLDS",
            "bad_model_coverage"))
        self.bad_model_identity_threshold = int(config.get(
            "THRESHOLDS",
            "bad_model_identity"))
        self.ssh_hostname = config.get("SSH", "hostname")
        self.ssh_port = int(config.get("SSH", "port"))
        self.ssh_username = config.get("SSH", "username")
        self.ssh_password = config.get("SSH", "password")
        self.ssh_identityfile = config.get("SSH", "identityfile")
        self.ssh_contaminer_location = config.get(
            "CLUSTER",
            "contaminer_location")
        self.ssh_work_directory = config.get("CLUSTER", "work_directory")
        self.tmp_dir = config.get("LOCAL", "tmp_dir")

        log.debug("Exit")
