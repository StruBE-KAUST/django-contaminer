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

"""Update the ContaBase."""

import logging

from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.core.exceptions import ValidationError

from contaminer.models.contabase import ContaBase

class Command(BaseCommand):
    """Update the ContaBase."""

    help = 'Synchronize the ContaBase with the remote ContaMiner installation'

    def handle(self, *args, **options):
        """Call ContaBase.update."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        self.stdout.write("Update ContaBase. Please wait a minute...")

        try:
            ContaBase.update()
        except ValidationError as excep:
            raise CommandError(
                'Update failed. Here is the reason: ' + str(excep))

        log.debug("Exit")
        self.stdout.write('The ContaBase has been updated.')
