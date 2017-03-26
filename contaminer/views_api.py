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
import os
import json

from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant
from .models.contaminer import Job
from .models.contaminer import Task

from .views_tools import newjob_handler


class ContaBaseView(TemplateView):
    """
        Views accessible through api/contabase
    """
    def get(self, request):
        """ Return the full ContaBase """

        return DetailedCategoriesView().get(request)


class CategoriesView(TemplateView):
    """
        Views accessible through api/categories
    """
    def get(self, request):
        """ Return the list of all contaminants in current contabase """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            categories = Category.objects.filter(
                    contabase = ContaBase.get_current()
                    )
        except ObjectDoesNotExist: #happens if no ContaBase is available
            raise Http404()

        categories_data = [cat.to_simple_dict() for cat in categories]

        response_data = {}
        response_data['categories'] = categories_data

        log.debug("Exit")
        return JsonResponse(response_data)


class DetailedCategoriesView(TemplateView):
    """
        Views accessible through api/categories
    """
    def get(self, request):
        """ Return the list of all contaminants in current contabase """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            categories = Category.objects.filter(
                    contabase = ContaBase.get_current()
                    )
        except ObjectDoesNotExist: #happens if no ContaBase is available
            raise Http404()

        categories_data = [cat.to_detailed_dict() for cat in categories]

        response_data = {}
        response_data['categories'] = categories_data

        log.debug("Exit")
        return JsonResponse(response_data)


class CategoryView(TemplateView):
    """
        Views accessible thourgh api/category
    """
    def get(self, request, id):
        """ Return the fileds of the category with the given id """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            category = Category.objects.get(
                    number = id,
                    contabase = ContaBase.get_current()
                    )
        except ObjectDoesNotExist:
            raise Http404()

        response_data = category.to_simple_dict()

        log.debug("Exit")
        return JsonResponse(response_data)


class DetailedCategoryView(TemplateView):
    """
        Views accessible thourgh api/category
    """
    def get(self, request, id):
        """ Return the fileds of the category with the given id """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            category = Category.objects.get(
                    number = id,
                    contabase = ContaBase.get_current()
                    )
        except ObjectDoesNotExist:
            raise Http404()

        response_data = category.to_detailed_dict()

        log.debug("Exit")
        return JsonResponse(response_data)


class ContaminantsView(TemplateView):
    """
        Views accessible through api/contaminants
    """
    def get(self, request):
        """ Return the list of all contaminants in current contabase """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contaminants = Contaminant.objects.filter(
                    category__contabase = ContaBase.get_current()
                    )
        except ObjectDoesNotExist: #happens if no ContaBase is available
            raise Http404()

        contaminants_data = [cont.to_simple_dict() for cont in contaminants]

        response_data = {}
        response_data['contaminants'] = contaminants_data

        log.debug("Exit")
        return JsonResponse(response_data)


class DetailedContaminantsView(TemplateView):
    """
        Views accessible through api/contaminants
    """
    def get(self, request):
        """ Return the list of all contaminants in current contabase """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contaminants = Contaminant.objects.filter(
                    category__contabase = ContaBase.get_current()
                    )
        except ObjectDoesNotExist: #happens if no ContaBase is available
            raise Http404()

        contaminants_data = [cont.to_detailed_dict() for cont in contaminants]

        response_data = {}
        response_data['contaminants'] = contaminants_data

        log.debug("Exit")
        return JsonResponse(response_data)


class ContaminantView(TemplateView):
    """
        Views accessible through api/contaminant
    """
    def get(self, request, uniprot_id):
        """ Return the fields of the contaminant with the given uniprot_id """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contaminant = Contaminant.objects.get(
                    uniprot_id = uniprot_id,
                    category__contabase = ContaBase.get_current(),
                    )
        except ObjectDoesNotExist:
            raise Http404()

        response_data = contaminant.to_simple_dict()

        log.debug("Exit")
        return JsonResponse(response_data)


class DetailedContaminantView(TemplateView):
    """
        Views accessible through api/detailed_contaminant
    """
    def get(self, request, uniprot_id):
        """ Return the fields and packs of the given contaminant """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            contaminant = Contaminant.objects.get(
                    uniprot_id = uniprot_id,
                    category__contabase = ContaBase.get_current(),
                    )
        except ObjectDoesNotExist:
            raise Http404()

        response_data = contaminant.to_detailed_dict()

        log.debug("Exit")
        return JsonResponse(response_data)


class JobView(TemplateView):
    """
        Views accessible through api/job
    """
    def post(self, request):
        """ Create new job, submit it to the cluster and return job.id """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        response_data = newjob_handler(request)

        if response_data['error']:
            status = 400
        else:
            status = 200

        return JsonResponse(response_data, status = status)

        log.debug("Exit")


class JobStatusView(TemplateView):
    """
        Views accessbiel through api/job/status
    """
    def get(self, request, job_id):
        """ Return the status of the job with the given job ID """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            job = Job.objects.get(id = job_id)
        except ObjectDoesNotExist:
            raise Http404()

        if job.confidential:
            response_data = {
                    'error': True,
                    'message': 'You are not allowed to see this job',
                    }
            return JsonResponse(response_data, status = 403)

        response_data = {
                'id': job.id,
                'status': job.get_status(),
                }

        log.debug("Exit")
        return JsonResponse(response_data)


class SimpleResultsView(TemplateView):
    """
        Views accessible through api/job/result
    """
    def get(self, request, job_id):
        """ Return the results of the job grouped by contaminant """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            job = Job.objects.get(id = job_id)
        except ObjectDoesNotExist:
            raise Http404()

        if job.confidential:
            response_data = {
                    'error': True,
                    'message': 'You are not allowed to see this job',
                    }
            return JsonResponse(response_data, status = 403)

        response_data = job.to_simple_dict()

        log.debug("Exit")
        return JsonResponse(response_data)


class DetailedResultsView(TemplateView):
    """
        Views accessible through api/job/detailed_result
    """
    def get(self, request, job_id):
        """ Return the results of the job for each single task """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        try:
            job = Job.objects.get(id = job_id)
        except ObjectDoesNotExist:
            raise Http404()

        if job.confidential:
            response_data = {
                    'error': True,
                    'message': 'You are not allowed to see this job',
                    }
            return JsonResponse(response_data, status = 403)

        response_data = job.to_detailed_dict()

        log.debug("Exit")
        return JsonResponse(response_data)


class GetFinalFilesView(TemplateView):
    """
        Views accessible through api/job/final{pdb,mtz}
    """
    def get(self, request, file_format):
        """ Return the final file with the specified format """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        file_format = file_format.lower()
        if file_format not in ['pdb', 'mtz']:
            response_data = {
                    'error': True,
                    'message': 'Format file is not available',
                    }
            return JsonResponse(response_data, status = 404)

        if not all(k in request.GET for k in
                ["id", "uniprot_id", "space_group", "pack_nb"]):
            log.warning("Bad request: " + str(request))
            response_data = {
                    'error': True,
                    'message': 'Bad request',
                    }
            return JsonResponse(response_data, status = 400)

        try:
            job = Job.objects.get(id = request.GET['id'])
        except ObjectDoesNotExist:
            response_data = {
                    'error': True,
                    'message': 'Job does not exist',
                    }
            return JsonResponse(response_data, status = 404)

        if job.confidential:
            response_data = {
                    'error': True,
                    'message': 'You are not allowed to see this job',
                    }
            return JsonResponse(response_data, status = 403)

        try:
            task = Task.objects.get(
                    job = job,
                    pack__contaminant__uniprot_id = request.GET['uniprot_id'],
                    pack__number = request.GET['pack_nb'],
                    space_group = request.GET['space_group']
                    )
        except ObjectDoesNotExist:
            response_data = {
                    'error': True,
                    'message': 'Task does not exist',
                    }
            return JsonResponse(response_data, status = 404)

        if not task.status_complete or task.percent < 90:
            response_data = {
                    'error': True,
                    'message': 'File is not available',
                    }
            return JsonResponse(response_data, status = 404)

        filename = task.get_final_filename(suffix = file_format)
        url = settings.STATIC_URL + filename

        log.debug("Exit with: " + str(url))
        return HttpResponseRedirect(url)
