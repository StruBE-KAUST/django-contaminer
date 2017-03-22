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
    URL configuration for contaminer
"""

from django.conf.urls import url
from django.conf.urls import include
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
        url(r'^download$', views.download, name='download'),
        url(r'^api/', include('contaminer.urls_api', namespace="API")),
        url(r'^contabase$', views.ContaBaseView.as_view(),
            name='contabase'),
        url(r'^contabase.xml$', views.ContaBaseXMLView.as_view(),
            name='contabase.xml'),
        url(r'^submit$', views.SubmitJobView.as_view(),
            name='submit'),
        url(r'^$', RedirectView.as_view(
            pattern_name = 'ContaMiner:submit',
            permanent = False,
            ),
            name='home'),
        url(r'^display/(?P<jobid>\d+)$', views.DisplayJobView.as_view(),
            name='display'),
]
