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

from .views_tools import newjob_handler
from . import views_api


class SubmitJobView(TemplateView):
    """
        Views to process the submitting form
    """

    def render_page(self, request, form = None):
        """ Render the page with the form """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contabase = ContaBase.get_current()
            categories = Category.objects.filter(
                    contabase = contabase
                    )
        except ObjectDoesNotExist:
            messages.warning(request, "The ContaBase is empty. You should" \
                    + " update the database before continuing by using" \
                    + " manage.py update")
            categories = {}

        if form is None:
            form = SubmitJobForm(
                    user = request.user,
                    )

        response_data = render(
                request,
                'ContaMiner/submit.html',
                {
                    'form': form,
                    'categories': categories,
                })

        log.debug("Exit")
        return response_data

    def get(self, request):
        """ Serve the form to submit a new job """
        return self.render_page(request)

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
                response = self.render_page(request, form)
            else:
                log.info("New job submitted")
                messages.success(request, "File submitted")
                response = HttpResponseRedirect(reverse('ContaMiner:home'))
        else:
            log.debug("Invalid form")
            messages.error(request, "Please check the form")
            response = self.render_page(request, form)

        log.debug("Exit")
        return response


class DisplayJobView(TemplateView):
    def get(self, request, jobid):
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

        if not job.status_complete:
            messages.warning(request, "This job is not yet complete.")
            result = HttpResponseRedirect(reverse('ContaMiner:home'))
            log.debug("Exiting function")
            return result

        # Retrieve best tasks for this
        best_tasks = job.get_best_tasks()

        # If a positive result is found for a pack with low coverage or low identity
        # display a message to encourage publication
        for task in best_tasks:
            if task.percent > 97:
                coverage = task.pack.coverage
                identity = task.pack.identity

                if coverage < 85 or identity < 80:
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


class ContaBaseJSONView(TemplateView):
    """
        Views accessible through contabase.json
    """
    def get(self, request):
        return views_api.ContaBaseView.as_view()(request)
