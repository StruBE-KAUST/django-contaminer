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
    Testing module for API views
    ============================

    This module contains unitary tests for the ContaMiner application.
"""

from django.test import TestCase
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from unittest import expectedFailure

from .forms import SubmitJobForm
from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant

from collections import Iterable


class SubmitFormTestCase(TestCase):
    """
        Test the SubmitForm form
    """
    def setUp(self):
        ContaBase.objects.create(obsolete = True)
        ContaBase.objects.create()
        contabase_obsolete = ContaBase.objects.filter(obsolete = True)[0]
        contabase = ContaBase.get_current()

        category1 = Category.objects.create(
                number = 1,
                name = "Not obsolete",
                contabase = contabase,
                )
        category2 = Category.objects.create(
                number = 2,
                name = "Checked",
                contabase = contabase,
                selected_by_default = True,
                )
        category_obsolete = Category.objects.create(
                number = 1,
                name = "Obsolete",
                contabase = contabase_obsolete,
                )

        Contaminant.objects.create(
                uniprot_id = "CONT",
                category = category1,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        Contaminant.objects.create(
                uniprot_id = "CHECKED",
                category = category2,
                short_name = "CHK",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        Contaminant.objects.create(
                uniprot_id = "CONT2",
                category = category_obsolete,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        self.factory = RequestFactory()
        self.request = self.factory.post(
                reverse('ContaMiner:submit')
                )
        self.user = User.objects.create_user(
                username = "Bob",
                email = "bob@squarepants.sea",
                password = "qwerty"
                )

    def test_confidential_is_available_if_logged_in(self):
        form = SubmitJobForm(
                self.request.POST,
                self.request.FILES,
                user = self.user,
                )
        fields = form.helper.layout[0][0]
        self.assertTrue('confidential' in fields)

    def test_confidential_hidden_if_logged_out(self):
        form = SubmitJobForm(
                self.request.POST,
                self.request.FILES,
                )
        fields = form.helper.layout[0][0]
        self.assertFalse('confidential' in fields)

    def test_confidential_hidden_if_anonymous(self):
        anon = AnonymousUser()
        form = SubmitJobForm(
                self.request.POST,
                self.request.FILES,
                )
        fields = form.helper.layout[0][0]
        self.assertFalse('confidential' in fields)

    def test_contaminants_listed(self):
        form = SubmitJobForm(
                self.request.POST,
                self.request.FILES,
                )
        fields = form.helper.layout[0][1]
        self.assertTrue('CONT' in fields[0].fields)
        self.assertTrue('CHECKED' in fields[1].fields)

    def test_contaminants_stay_checked(self):
        post_data = self.request.POST
        post_data['CONT'] = 'on'
        form = SubmitJobForm(
                post_data,
                self.request.FILES,
                )

        form.is_valid()

        self.assertTrue(form.cleaned_data['CONT'])
        self.assertFalse(form.cleaned_data['CHECKED'])

    def test_default_selected_contaminants_are_selected(self):
        form = SubmitJobForm(
                self.request.POST,
                self.request.FILES,
                )
        fields = form.helper.layout[0][1]
        self.assertTrue(form.fields['CHECKED'].initial)
        self.assertFalse(form.fields['CONT'].initial)

    def test_get_gives_category_from_current_contabase(self):
        form = SubmitJobForm(
                self.request.POST,
                self.request.FILES,
                )
        fields = form.helper.layout[0][1]
        self.assertFalse('CONT2' in fields[0].fields)
