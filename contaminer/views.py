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
import threading

from django.views.generic import TemplateView
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

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

def newjob(request):
    """ Serve the form to submit a new job, or give the data to the handler """
    log = logging.getLogger(__name__)
    log.debug("Entering function")

    if request.method == 'POST':
        log.debug("POST request")

        form = UploadStructure(request.POST,
                request.FILES,
                user = request.user)

        if form.is_valid():
            log.debug("Valid form")
            try:
                newjob_handler(request)
            except ValueError as e:
                log.warning("Bad file submitted : " + str(e))
                messages.error(request,
                        "Bad input file. Please upload a valid cif or mtz\
                        file.")
            except Exception as e:
                log.error("Error when submitting new job : " + str(e))
                messages.error(request,
                        "Something went wrong. Please try again later.")
            else:
                log.info("New job submitted")
                messages.success(request, "File submitted")

            result = HttpResponseRedirect(reverse('ContaMiner:home'))

            log.debug("Exiting function")
            return result

        # if form is not valid, the form is updated, then used after
        # this else block

    else:
        log.debug("Give the form")
        form = UploadStructure(
                user = request.user
                )

    result = render(request, 'ContaMiner/newjob.html', {'form': form})

    log.debug("Exiting function")
    return result


def newjob_handler(request):
    """ Interface between the request and the Job model """
    log = logging.getLogger(__name__)
    log.debug("Entering function")

    # Define user and confidentiality
    user = None
    confidential = False
    if request.user is not None and request.user.is_authenticated():
        user = request.user

        # If choosen, define confidential
        if request.POST.has_key('confidential'):
            confidential = request.POST['confidential']

    log.debug("User : " + str(user))
    log.debug("Conf : " + str(confidential))

    # Define job name
    job_name = ""
    if request.POST.has_key('job_name') and request.POST['job_name'] :
        job_name = request.POST['job_name']
    else:
        for filename, file in request.FILES.iteritems():
            job_name = file.name
    log.debug("Job name : " + str(job_name))

    # Define the file extension
    suffix = ""
    if re.match(".*\.cif$", request.FILES['structure_file'].name):
        suffix = "cif"
    elif re.match(".*\.mtz", request.FILES['structure_file'].name):
        suffix = "mtz"
    else:
        raise ValueError
    log.debug("Suffix : " + str(suffix))

    # Define email
    email = ""
    if request.POST.has_key('email'):
        email = request.POST['email']
    log.debug("Email : " + str(email))

    # Create job
    newjob = Job()
    newjob.create(
            name = job_name,
            author = user,
            email = email,
            confidential = confidential
            )
    log.debug("Job created")

    # Save file in media path
    filename = newjob.get_filename(suffix = suffix)
    log.debug("Filename : " + str(filename))
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
    log.debug("Diffraction data file saved")

    # Define list of contaminants
    listname = newjob.get_filename(suffix='txt')
    list_path = os.path.join(settings.MEDIA_ROOT, listname)
    with open(list_path, 'wb') as destination:
        for cont in Contaminant.get_all():
            if request.POST.has_key(cont.uniprot_ID):
                destination.write(cont.uniprot_ID + '\n')
    log.debug("Contaminants list file saved")

    # Submit job
    threading.Thread(target=newjob.submit, args=(file_path, list_path)).start()
#    newjob.submit(file_path, list_path)
    log.debug("Job is submitted")

    log.debug("Exiting function")


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
