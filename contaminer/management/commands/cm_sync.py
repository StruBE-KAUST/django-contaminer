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
    Contact a complete preparation of morda to initiate the database of
    django-contaminer
"""

import os
import re
import logging

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ObjectDoesNotExist

from contaminer.models import Contaminant
from contaminer.models import Pack
from contaminer.models import Model
from contaminer.cluster import SSHChannel
from contaminer.apps import ContaminerConfig

class Command(BaseCommand):
    """ Command available in manage.py """

    help = "Retrieve information from the cluster to initiate the DB"

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not self.is_prep_complete():
            log.warning("Installation is not complete on the cluster. " \
                    + "Please retry later.")
            raise CommandError(
                    "Installation is not complete on the cluster. " \
                            + "Please retry later.")

        missing_contaminants = self.check_contaminants()
        if missing_contaminants:
            log.error("The contaminant DB is not synchronized with the cluster")
            raise CommandError(
                    "Please add these contaminants through the admin "\
                            + "interface : "\
                            + str(missing_contaminants))
        log.info("Contaminant DB up-to-date")

        self.update_packs()
        log.info("Pack DB updated")

        self.update_models()
        log.info("Model DB updated")

        self.stdout.write('Successfully updated database')


    def is_prep_complete(self):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        cluster_comm = SSHChannel()
        stdout, stderr = cluster_comm.command(
                "squeue -u cbrc-strube -n \"sbatch_prep.sh\""
                )

        if stderr:
            log.error("squeue command gives an error : " + stderr[0])
            raise RuntimeError(stderr[0])

        log.debug("Exiting function")
        return (len(stdout) <= 1)


    def check_contaminants(self):
        """ Returns a list of contaminants presents on the cluster but not in
        the local DB """
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        cluster_comm = SSHChannel()
        cm_bin_path = ContaminerConfig().ssh_contaminer_location
        cm_cont_path = os.path.join(cm_bin_path, "data/contaminants")
        log.debug("Remote contaminants path : " + cm_cont_path)

        stdin, stderr = cluster_comm.command(
                "ls " + cm_cont_path \
                + ' | grep -v "slurm-.*\.out"' \
                + ' | grep -v "big_struct.cif"'
                )

        if stderr:
            log.error("ls command gives an error : " + stderr[0])
            raise RuntimeError(stderr[0])


        missing_contaminants = []

        for uniprot_ID in stdin:
            uniprot_ID = re.sub(r'\n', '', uniprot_ID)

            try:
                exist_cont = Contaminant.objects.get(uniprot_ID = uniprot_ID)
            except ObjectDoesNotExist:
                missing_contaminants.append(uniprot_ID)

        log.debug("Exiting function")
        return missing_contaminants


    def update_packs(self):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        raise NotImplementedError


    def update_models(self):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        raise NotImplementedError


    def get_list_contaminants(self):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        raise NotImplementedError

