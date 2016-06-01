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
    Module for ContaMiner views
"""

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

import logging

from .forms import UploadStructure
from .models import Contaminant
from .apps import ContaminerConfig

def get_contaminants():
    contaminants = Contaminant.objects.all()
    return contaminants

def get_contaminants_by_category():
    contaminants = get_contaminants()
    if not contaminants:
        contaminants = []
    grouped_contaminants = {}
    for contaminant in contaminants:
        try:
            grouped_contaminants[contaminant.category].append(contaminant)
        except KeyError:
            grouped_contaminants[contaminant.category] = [contaminant]
    return grouped_contaminants

def newjob(request):
    """ Serve the form to submit a new job, or give the data to the handler """
    log = logging.getLogger(__name__)
    log.debug("Entering function with arg : \n\
            request : " + str(request))

    if request.method == 'POST':
        form = UploadStructure(request.POST,
                request.FILES,
                grouped_contaminants = get_contaminants_by_category())
        if form.is_valid():
            try:
                newjob_handler(request)
            except ValueError:
                messages.error(request,
                        "Bad input file. Please upload a valid cif or mtz\
                        file.")
            except RuntimeError:
                messages.error(request,
                        "Something went wrong. Please try again later.")
            else:
                messages.success(request, "File submitted")

            result = HttpResponseRedirect(reverse('ContaMiner:home'))
            log.debug("Exiting function with a valid form and result : \n\
                    result : " + str(result))
            return result
    else:
        form = UploadStructure(
                grouped_contaminants = get_contaminants_by_category())

    result = render(request, 'ContaMiner/newjob.html', {'form': form})
    log.debug("Exiting function with result : \n\
            result : " + str(result))
    return result

def newjob_handler(request):
    pass

def download(request):
    result = render(request, 'ContaMiner/download.html')
    return result
