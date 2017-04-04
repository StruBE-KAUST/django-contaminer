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
    Add a command to manage.py to launch the update_thread of non-archived jobs
"""

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.exceptions import ValidationError

from contaminer.models.contaminer import Job

import logging
import threading

class Command(BaseCommand):
    """
        Call update_thread on non archived jobs
    """

    help = 'Launch job updaters threads. Useful after a server shutdown.'

    def handle(self, *args, **options):
        log = logging.getLogger(__name__)
        log.debug("Enter")

        threads = [t for t in threading.enumerate()
                if t.name == "UpdateJobThread" ]
        if len(threads) > 0:
            raise CommandError(
                    'Threads are already running. Not launching again.'
                    )

        self.stdout.write("Launching updaters...")
        jobs = Job.objects.filter(status_archived == False)

        for job in jobs:
            job.update_thread

        log.debug("Exit")
        if len(job) == 0:
            self.stdout.write("No job to update.")
        else:
            self.stdout.write("The updater threads are now running.")
