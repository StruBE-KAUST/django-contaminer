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

"""Start the updating process for one or several jobs."""

import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from contaminer.models.contaminer import Job


class Command(BaseCommand):
    """Call update_thread on non archived jobs."""

    help = 'Start the updater process for the jobs with the given IDs. If no '\
            + 'ID is given, start a detached process to update all the non ' \
            + 'archived jobs.'

    def add_arguments(self, parser):
        """Add job_id as optional argument."""
        parser.add_argument('job_id', nargs='?', type=int)

    def handle(self, *args, **options):
        """Run one process per non archived job, or one process for job_id."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if not options['job_id']:
            jobs = Job.objects.filter(status_archived=False)
            for job in jobs:
                job.start_update_process()

        else:
            job_id = options['job_id']

            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                raise CommandError('Job "%s" does not exist.' % job_id)

            if job.status_archived:
                raise CommandError('Job "%s" is archived.' % job_id)

            self.stdout.write("Periodically update job with ID: " \
                    + str(job_id))
            self.stdout.write("Quit with CONTROL-C")

            job.update_process()
