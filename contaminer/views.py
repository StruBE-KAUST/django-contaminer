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
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings

import logging
import os
import re
import errno

from .forms import UploadStructure
from .models import Contaminant
from .models import Job
from .models import Task

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
    log = logging.getLogger(__name__)
    log.debug("Entering function with arg : \n\
            request : " + str(request))

    # Define user
    user = None
    if request.user is not None and request.user.is_authenticated():
        user = request.user

    # Define job name
    name = ""
    if request.POST.has_key('name') and request.POST['name'] :
        name = request.POST['name']
    else:
        for filename, file in request.FILES.iteritems():
            name = file.name

    # Define the file extension
    suffix = ""
    if re.match(".*\.cif$", request.FILES['structure_file'].name):
        suffix = "cif"
    elif re.match(".*\.mtz", request.FILES['structure_file'].name):
        suffix = "mtz"
    else:
        log.warning("Submit an incorrect file")
        # TODO : add messages
        raise ValueError

    # Define email
    email = ""
    if request.POST.has_key('email'):
        email = request.POST['email']

    # Create job
    newjob = Job()
    newjob.create(name = name, author = user, email = email)

    # Save file in media path
    filename = newjob.get_filename(suffix = suffix)
    log.debug("filename : " + str(filename))
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    try:
        os.makedirs(settings.MEDIA_ROOT)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(settings.MEDIA_ROOT):
            pass
        else:
            raise

    with open(file_path, 'wb') as destination:
        for chunk in request.FILES['structure_file']:
            destination.write(chunk)

    # Define list of contaminants
    listname = newjob.get_filename(suffix='txt')
    list_path = os.path.join(settings.MEDIA_ROOT, listname)
    with open(list_path, 'wb') as destination:
        for cont in get_contaminants():
            if request.POST.has_key(cont.uniprot_ID):
                destination.write(cont.uniprot_ID + '\n')

    # Submit job
    newjob.submit(file_path, list_path)

    log.debug("Exiting function")

def result(request, jobid):
    log = logging.getLogger(__name__)
    job = get_object_or_404(Job, pk = jobid)
    if not job.finished:
        messages.warning(request, "This job is not yet complete.")
        result = HttpResponseRedirect(reverse('ContaMiner:home'))
        log.debug("Exiting function")
        return result


def list_contaminants(request):
    context = {'list_contaminants': get_contaminants_by_category()}
    result = render(request, 'ContaMiner/list.html', context = context)
    return result

def download(request):
    result = render(request, 'ContaMiner/download.html')
    return result
