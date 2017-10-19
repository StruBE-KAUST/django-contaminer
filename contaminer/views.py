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

"""ContaMiner views."""

import logging
import os

from django.views.generic import View
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.http import Http404
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.conf import settings
from django.urls import reverse

from .forms import SubmitJobForm

from .models.contabase import ContaBase
from .models.contabase import Contaminant
from .models.contabase import Category
from .models.contaminer import Job
from .models.contaminer import Task

from .views_tools import newjob_handler
from . import views_api


class SubmitJobView(View):
    """Views to process the submitting form."""

    @staticmethod
    def render_page(request, form=None):
        """Render the page with the form."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contabase = ContaBase.get_current()
            categories = Category.objects.filter(
                contabase=contabase,
            ).exclude(
                name="User provided models"
            )
        except ObjectDoesNotExist:
            messages.warning(request, "The ContaBase is empty. You should" \
                    + " update the database before continuing by using" \
                    + " manage.py update")
            categories = {}

        if form is None:
            form = SubmitJobForm(user=getattr(request, 'user', None))

        response_data = render(
            request,
            'ContaMiner/submit.html',
            {
                'form': form,
                'categories': categories})

        log.debug("Exit")
        return response_data

    def get(self, request):
        """Serve the form to submit a new job."""
        return self.render_page(request)

    def post(self, request):
        """If the form is valid, submit the job. Return the form otherwise."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            user = request.user
        except AttributeError:
            user = None

        form = SubmitJobForm(
            request.POST,
            request.FILES,
            user=user)

        if form.is_valid():
            log.debug("Valid form")
            response_data = newjob_handler(request)
            if response_data['error']:
                messages.error(request, response_data['message'])
                response = self.render_page(request, form)
            else:
                log.info("New job submitted")
                messages.success(request, "File submitted")
                # pylint: disable=redefined-variable-type
                response = HttpResponseRedirect(
                    reverse('ContaMiner:display', args=[response_data['id']]))
        else:
            log.debug("Invalid form")
            messages.error(request, "Please check the form")
            response = self.render_page(request, form)

        log.debug("Exit")
        return response


class DisplayJobView(View):
    """Views to see the results of a job."""

    def get(self, request, job_id):
        """Display the result of a job."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            job = Job.objects.get(pk=job_id)
        except ObjectDoesNotExist:
            messages.error(request, "This job does not exist.")
            result = SubmitJobView().get(request)
            result.status_code = 404
            log.debug("Job not found")
            return result

        if job.confidential and request.user != job.author:
            messages.error(request, "This job is confidential. You are not "\
                + "allowed to see the results.")
            result = SubmitJobView().get(request)
            result.status_code = 403
            log.debug("Permission denied")
            return result

        if job.status_running or job.status_complete:
            # Provide skeleton page. Population will be done by javascript
            contaminants = \
                Contaminant.objects.filter(pack__task__job=job).distinct()
            categories = set([c.category for c in contaminants])

            for category in categories:
                category.contaminants = \
                    [c for c in contaminants if c.category == category]

            app_config = apps.get_app_config('contaminer')

            result = render(
                request,
                'ContaMiner/result.html',
                {
                    'job': job,
                    'categories': categories,
                    'threshold': app_config.threshold,
                    'api_url': reverse('ContaMiner:API:job'),
                    'uglymol_url': reverse('ContaMiner:uglymol', args=(job.id, "")),
                })
        else:
            # Provide buffering page, waiting for the job to be running
            messages.info(request, "This job is not yet running. Please "\
                + "wait, this page will automatically reload.")
            result = render(
                request,
                'ContaMiner/buffer.html',
                {
                    'job': job,
                    'api_url_status': reverse(
                        'ContaMiner:API:job_status', args=[job.id]),
                })

        log.debug("Exit")
        return result


class UglymolView(View):
    """Views to display the morda output in Uglymol"""

    def get(self, request, job_id, task_desc):
        # Find corresponding task
        job = Job.objects.get(pk = job_id)
        try:
            task = Task.from_name(job, task_desc)
        except ObjectDoesNotExist:
            raise Http404()

        task.pdb_filename = settings.MEDIA_URL \
            + task.get_final_filename(suffix='pdb')
        task.map_filename = settings.MEDIA_URL \
            + task.get_final_filename(suffix='map')
        task.diff_map_filename = settings.MEDIA_URL \
            + task.get_final_filename(suffix='diff.map')

        context = {
            'job_id': job_id,
            'task': task
            }
        result = render(
            request,
            'ContaMiner/uglymol.html',
            context=context,
            )
        return result


class ContaBaseView(View):
    """Views accessible through contabase."""

    def get(self, request):
        """Display the list of registered contaminants."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contabase = ContaBase.get_current()
            context = {'contabase': contabase.to_detailed_dict()['categories']}
        except ObjectDoesNotExist:
            messages.warning(request, "The ContaBase is empty. You should" \
                    + " update the database before continuing by using" \
                    + " manage.py update")
            context = {'contabase': {}}

        result = render(request, 'ContaMiner/contabase.html', context=context)

        log.debug("Exit")
        return result


class ContaBaseJSONView(View):
    """Views accessible through contabase.json."""

    def get(self, request):
        """Return the contabase in JSON format."""
        return views_api.ContaBaseView.as_view()(request)
