from __future__ import unicode_literals

from django.apps import AppConfig


class ContaminerConfig(AppConfig):
    name = 'contaminer'
    verbose_name = 'ContaMiner'
    ssh_hostname = 'login.cbrc.kaust.edu.sa'
    ssh_port = 22
    ssh_username = 'hungleaj'
    ssh_password = ''
    ssh_identityfile = '/home/dunatotatos/.ssh/id_rsa3'
