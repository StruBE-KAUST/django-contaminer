# -*- coding : utf-8 -*-

##    Copyright (C) 2015 Hungler Arnaud
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
    Add command to manage.py to terminate one job
"""

import re
import logging

from django.core.management.base import BaseCommand, CommandError
from contaminer.models import Job


class Command(BaseCommand):
    """ Command available in manage.py """

    help = 'Retrieve information from the cluster to terminate a job'

    def add_arguments(self, parser):
        parser.add_argument('job_id', nargs='+', type=int)

    def handle(self, *args, **options):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        for job_id in options['job_id']:
            log.info("Complete job : " + str(job_id))

            try:
                job = Job.objects.get(pk=job_id)
                job.terminate()
            except (Job.DoesNotExist, RuntimeError):
                raise CommandError(
                'Job "%s" does not exist or is not completed.' % job_id)

            log.info("Job " + str(job_id) + " complete")
            self.stdout.write('Successfully terminate job number "%s"' % job_id)
