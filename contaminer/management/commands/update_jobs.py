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

from contaminer.models.contaminer import Job


class Command(BaseCommand):
    """Call update_thread on non archived jobs."""

    help = 'Start the updater process for the jobs with the given IDs. If no '\
            + 'ID is given, start a detached process to update all the non ' \
            + 'archived jobs.'

    def handle(self, *args, **options):
        """Update all the non-archived and submitted jobs."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        Job.update_all()

        log.debug("Exit")
