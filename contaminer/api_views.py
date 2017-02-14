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
    ContaMiner views to access the API
"""

import logging
import json

from django.http import JsonResponse
from django.http import Http404
from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist

from .models.contabase import Contaminant
from .models.contabase import ContaBase

class ContaminantView(TemplateView):
    """
        Views accessible through api/contaminant
    """
    def get(self, request, uniprot_id):
        """ Return the fields of the contaminant with the given uniprot)id """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contaminant = Contaminant.objects.get(
                    uniprot_id = uniprot_id,
                    category__contabase = ContaBase.get_current(),
                    )
        except ObjectDoesNotExist:
            raise Http404()

        response_data = {}
        response_data['uniprot_id'] = uniprot_id
        response_data['short_name'] = contaminant.short_name
        response_data['long_name'] = contaminant.long_name
        response_data['sequence'] = contaminant.sequence
        response_data['organism'] = contaminant.organism

        log.debug("Exit")
        return JsonResponse(response_data)
