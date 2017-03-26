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
    Tools for API and browser views
"""

import logging
import os
import errno
import tempfile
import threading

from .models.contabase import ContaBase
from .models.contabase import Contaminant
from .models.contaminer import Job

from django.utils.datastructures import MultiValueDictKeyError

def newjob_handler(request):
    """ Interface between the request and the Job model """
    log = logging.getLogger(__name__)
    log.debug("Entering function")

    # Check if file is uploaded
    if not "diffraction_data" in request.FILES:
        response_data = {
                'error': True,
                'message': 'Missing diffraction data file',
                }
        return response_data

    # Check the file extension
    extension = os.path.splitext(request.FILES['diffraction_data'].name)[1]
    if extension.lower() not in ['.mtz', '.cif']:
        response_data = {
                'error': True,
                'message': 'File format is not CIF or MTZ',
                }
        return response_data

    # Define user and confidentiality
    try:
        user = request.user
        if not user.is_authenticated():
            user = None
    except AttributeError:
        user = None
    # If choosen, define confidential
    try:
        confidential = request.POST['confidential']
    except MultiValueDictKeyError:
        confidential = False
    log.debug("User : " + str(user))
    log.debug("Conf : " + str(confidential))

    # Define job name
    if "name" in request.POST and request.POST['name'] :
        name = request.POST['name']
    else:
        name = request.FILES['diffraction_data'].name
    log.debug("Job name : " + str(name))

    # Define email
    try:
        email = request.POST['email_address']
    except AttributeError:
        email = None
    log.debug("Email : " + str(email))

    # Define list of contaminants
    try:
        contaminants = request.POST['contaminants']
    except KeyError:
        # contaminants could be a result of the checkbox list
        contaminants = ""
        for contaminant in Contaminant.objects.filter(
                category__contabase = ContaBase.get_current()
                ):
            if contaminant.uniprot_id in request.POST:
                contaminants += contaminant.uniprot_id
                contaminants += ","

        if not contaminants:
            response_data = {
                    'error': True,
                    'message': 'Missing list of contaminants',
                    }
            return response_data
        else:
            # Remove trailing comma
            contaminants = contaminants[:-1]

    contaminants = contaminants.replace(',', '\n')

    # Create job
    job = Job.create(
            name = name,
            author = user,
            email = email,
            confidential = confidential
            )
    log.debug("Job created")

    # Locally save file
    filename = job.get_filename(suffix = extension)
    tmp_diff_data_file = os.path.join(tempfile.mkdtemp(), filename)

    with open(tmp_diff_data_file, 'wb') as destination:
        for chunk in request.FILES['diffraction_data']:
            destination.write(chunk)
    log.debug("Diffraction data file saved")

    # Submit job
    threading.Thread(
            target = job.submit,
            args = (tmp_diff_data_file, contaminants)
            ).start()
    job.status_submitted = True
    job.save()
    log.info("New job submitted")

    response_data = {
            'error': False,
            'id': job.id,
            }
    return response_data
