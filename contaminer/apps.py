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
    This module reads the config.ini file for contaminer, then provides this
    configuration through the class ContaminerConfig
"""

from django.apps import AppConfig
import os
import ConfigParser
import logging


class ContaminerConfig(AppConfig):
    """ Configuration of contaminer application """

    name = 'contaminer'
    verbose_name = 'ContaMiner'

    def __init__(self):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        config = ConfigParser.ConfigParser()
        config_file = os.path.join(BASE_DIR, "config.ini")
        res = config.read(config_file)

        if res == []:
            log.error("config.ini does not exist.")
            log.info("Use config.template to create your config.ini")
            raise IOError

        self.ssh_hostname = config.get("SSH", "hostname")
        self.ssh_port = eval(config.get("SSH", "port"))
        self.ssh_username = config.get("SSH", "username")
        self.ssh_password = config.get("SSH", "password")
        self.ssh_identityfile = config.get("SSH", "identityfile")
        self.ssh_contaminer_location = config.get("CLUSTER",
                "contaminer_location")
        self.ssh_work_directory = config.get("CLUSTER", "work_directory")
        self.tmp_dir = config.get("LOCAL", "tmp_dir")

        log.debug("Exit function")
