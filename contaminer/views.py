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
    ContaMiner views
"""

import logging
import os
import re
import errno
import tempfile
import threading

from django.views.generic import TemplateView
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.datastructures import MultiValueDictKeyError

from .forms import SubmitJobForm

from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant
from .models.contaminer import Job
from .models.contaminer import Task


class SubmitJobView(TemplateView):
    """
        Views to process the submitting form
    """

    def get(self, request):
        """ Serve the form to submit a new job """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            Category.objects.filter(
                    contabase = ContaBase.get_current()
                    )
        except ObjectDoesNotExist:
            messages.warning(request, "The ContaBase is empty. You should" \
                    + " update the database before continuing by using" \
                    + " manage.py update")

        form = SubmitJobForm(
                user = request.user,
                )

        response_data = render(
                request,
                'ContaMiner/submit.html',
                {'form': form}
                )

        log.debug("Exit")
        return response_data

    def post(self, request):
        """ If the form is valid, submit the job. Return the form otherwise """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            user = request.user
        except AttributeError:
            user = None

        form = SubmitJobForm(
                request.POST,
                request.FILES,
                user = user
                )

        if form.is_valid():
            log.debug("Valid form")
            response_data = newjob_handler(request)
            if response_data['error'] :
                messages.error(request, response_data['message'])
                try:
                    Category.objects.filter(
                            contabase = ContaBase.get_current()
                            )
                except ObjectDoesNotExist:
                    messages.warning(request, "The ContaBase is empty. You should" \
                            + " update the database before continuing by using" \
                            + " manage.py update")
                response = render(
                        request,
                        'ContaMiner/submit.html',
                        {'form': form}
                        )

            else:
                log.info("New job submitted")
                messages.success(request, "File submitted")
                response = HttpResponseRedirect(reverse('ContaMiner:home'))
        else:
            log.debug("Invalid form")
            messages.error(request, "Please check the form")
            try:
                Category.objects.filter(
                        contabase = ContaBase.get_current()
                        )
            except ObjectDoesNotExist:
                messages.warning(request, "The ContaBase is empty. You should" \
                        + " update the database before continuing by using" \
                        + " manage.py update")

            response = render(
                    request,
                    'ContaMiner/submit.html',
                    {'form': form}
                    )

        log.debug("Exit")
        return response


def newjob_handler(request):
    """ Interface between the request and the Job model """
    log = logging.getLogger(__name__)
    log.debug("Entering function")

    # Check if file is uploaded
    if not request.FILES.has_key('diffraction_data'):
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
    if request.POST.has_key('name') and request.POST['name'] :
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


def result(request, jobid):
    """ Display the result of a job """
    log = logging.getLogger(__name__)
    log.debug("Entering function")

    job = get_object_or_404(Job, pk = jobid)

    if job.confidential and request.user != job.author:
        messages.error(request, "This job is confidential. You are not "\
                + "allowed to see the results.")
        result = HttpResponseRedirect(reverse('ContaMiner:home'))
        log.debug("Exiting function")
        return result

    if not job.finished:
        messages.warning(request, "This job is not yet complete.")
        result = HttpResponseRedirect(reverse('ContaMiner:home'))
        log.debug("Exiting function")
        return result

    # Retrieve all tasks for this job
    tasks = job.task_set.all()

    # Keep only the best pack for each contaminant
    best_tasks = []
    for task in tasks:
        # co_tasks are tasks for the same contaminant and same job
        # (different pack and different space group)
        co_tasks = [e_task
                for e_task in best_tasks
                if e_task.pack.contaminant == task.pack.contaminant]
        if co_tasks:
            # Can only be one pack
            co_task = co_tasks[0]
            if co_task.error or co_task.q_factor < task.q_factor:
                task_index = best_tasks.index(co_task)
                best_tasks[task_index] = task

        else:
            best_tasks.append(task)

    log.debug("Selected tasks : " + str(best_tasks))

    # If a positive result is found for a pack with low coverage or low identity
    # display a message to encourage publication
    for task in best_tasks:
        if task.percent > 97:
            coverage = task.pack.coverage

            models = task.pack.model_set.all()
            identity = sum([model.identity for model in models]) / len(models)

            if coverage < 85 or identity < 90:
                messages.info(request, "Your dataset gives a positive result "\
                        + "for a contaminant for which no identical "\
                        + "model is available in the PDB.\nYou could deposit "\
                        + "or publish this structure.")

    result = render(request, 'ContaMiner/result.html',
            {'job': job, 'tasks': best_tasks})
    log.debug("Exiting function")
    return result


class ContaBaseView(TemplateView):
    """
        Views accessible through contabase
    """
    def get(self, request):
        """ Display the list of registered contaminants """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            context = {'contabase':
                    ContaBase.get_current().to_detailed_dict()['categories']
                }
        except ObjectDoesNotExist:
            messages.warning(request, "The ContaBase is empty. You should" \
                    + " update the database before continuing by using" \
                    + " manage.py update")
            context = {}

        result = render(request, 'ContaMiner/contabase.html', context = context)

        log.debug("Exit")
        return result


class ContaBaseXMLView(TemplateView):
    """
        Views accessible through contabase.xml
    """
    def get(self, request):
        pass


def download(request):
    """ Show how to download the ContaMiner application """
    result = render(request, 'ContaMiner/download.html')
    return result
