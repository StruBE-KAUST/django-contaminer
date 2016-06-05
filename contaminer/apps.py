from __future__ import unicode_literals

from django.apps import AppConfig
import os
import ConfigParser
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config = ConfigParser.ConfigParser()
config_file = os.path.join(BASE_DIR, "config.ini")
config.read(config_file)

class ContaminerConfig(AppConfig):
    name = 'contaminer'
    verbose_name = 'ContaMiner'

    ssh_hostname = config.get("SSH", "hostname")
    ssh_port = eval(config.get("SSH", "port"))
    ssh_username = config.get("SSH", "username")
    ssh_password = config.get("SSH", "password")
    ssh_identityfile = config.get("SSH", "identityfile")
    ssh_contaminer_location = config.get("CLUSTER", "contaminer_location")
    ssh_work_directory = config.get("CLUSTER", "work_directory")
    tmp_dir = config.get("LOCAL", "tmp_dir")
