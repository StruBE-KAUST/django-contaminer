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
import tempfile
import threading

from django.http import JsonResponse
from django.http import Http404
from django.views.generic import TemplateView
from django.core.exceptions import ObjectDoesNotExist

from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant
from .models.contaminer import Job


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

        # Check if a file is uploaded
        if not request.FILES.has_key('diffraction_data'):
            response_data = {
                    'error': True,
                    'message': 'Missing diffraction data file',
                    }
            return JsonResponse(response_data, status = 400)

        # Check the file extension (and save it)
        extension = os.path.splitext(request.FILES['diffraction_data'].name)[1]
        if extension not in ['.mtz', '.cif', '.MTZ', '.CIF']:
            response_data = {
                    'error': True,
                    'message': 'File format is not CIF or MTZ',
                    }
            return JsonResponse(response_data, status = 400)

        # Create Job
        if request.POST.has_key('name'):
            name = request.POST['name']
        else:
            name = request.FILES['diffraction_data'].name

        if request.POST.has_key('email_address'):
            email = request.POST['email_address']
        else:
            email = None

        job = Job.create(
                name = name,
                email = email,
                )

        # Locally save file
        filename = job.get_filename(suffix = extension)
        tmp_diff_data_file = os.path.join(tempfile.mkdtemp(), filename)

        with open(tmp_diff_data_file, 'wb') as destination:
            for chunk in request.FILES['diffraction_data']:
                destination.write(chunk)

        # Define list of contaminants
        try:
            contaminants = request.POST['contaminants']
        except KeyError:
            response_data = {
                    'error': True,
                    'message': 'Missing list of contaminants',
                    }

        contaminants = contaminants.replace(',', '\n')

        # Submit job
        threading.Thread(
                target = job.submit,
                args=(tmp_diff_data_file, contaminants)
                ).start()
        job.status_submitted = True
        job.save()
        log.info("New job submitted")

        response_data = {
                'error': False,
                'id': job.id,
                }
        print "asdfasdfasdf" + str(job.id)
        return JsonResponse(response_data)

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

        response_data = {
                'id': job.id,
                'status': job.get_status(),
                }

        log.debug("Exit")
        return JsonResponse(response_data)
