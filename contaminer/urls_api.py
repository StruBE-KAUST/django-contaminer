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
    URL configuration for contaminer API
"""

from django.conf.urls import url
from . import views_api

urlpatterns = [
        url(r'^contabase',
            views_api.ContaBaseView.as_view(),
            name='contabase'),
        url(r'^categories',
            views_api.CategoriesView.as_view(),
            name='categories'),
        url(r'^detailed_categories',
            views_api.DetailedCategoriesView.as_view(),
            name='categories'),
        url(r'^category/(?P<category_id>.*)$',
            views_api.CategoryView.as_view(),
            name='category'),
        url(r'^detailed_category/(?P<category_id>.*)$',
            views_api.DetailedCategoryView.as_view(),
            name='detailed_category'),
        url(r'^contaminants',
            views_api.ContaminantsView.as_view(),
            name='contaminants'),
        url(r'^detailed_contaminants',
            views_api.DetailedContaminantsView.as_view(),
            name='detailed_contaminants'),
        url(r'^contaminant/(?P<uniprot_id>.*)$',
            views_api.ContaminantView.as_view(),
            name='contaminant'),
        url(r'^detailed_contaminant/(?P<uniprot_id>.*)$',
            views_api.DetailedContaminantView.as_view(),
            name='detailed_contaminant'),
        url(r'^job',
            views_api.JobView.as_view(),
            name='job'),
        url(r'^job/status/(?P<job_id>[0-9]*)$',
            views_api.JobStatusView.as_view(),
            name='job_status'),
        url(r'^job/result/(?P<job_id>[0-9]*)$',
            views_api.SimpleResultsView.as_view(),
            name='result'),
        url(r'^job/detailed_result/(?P<job_id>[0-9]*)$',
            views_api.DetailedResultsView.as_view(),
            name='detailed_result'),
        url(r'^job/final_(?P<format_file>\w+)$',
            views_api.GetFinalFilesView.as_view(),
            name='get_final'),
]
