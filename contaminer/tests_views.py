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
from django.test import Client
from django.urls import reverse
import mock

from .views import ContaBaseView
from .views import SubmitJobView
from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant
from .models.contabase import Pack
from .models.contabase import Model
from .models.contabase import Reference
from .models.contabase import Suggestion
from .models.contaminer import Job
from .models.contaminer import Task

import tempfile


class ContaBaseViewTestCase(TestCase):
    """
        Test the DetailedContaminantsView views
    """
    def setUp(self):
        self.client = Client()

    def test_get_returns_message_on_empty_contabase(self):
        response = self.client.get(
                reverse('ContaMiner:contabase')
                )
        messages = [str(m) for m in response.context['messages']]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(["empty" in e for e in messages]))

    def test_get_valid_categories_list(self):
        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        Category.objects.create(
                number = 1,
                name = "Test views",
                contabase = contabase,
                )
        category = Category.objects.get(
                name = "Test views",
                )
        Contaminant.objects.create(
                uniprot_id = "TESTVIEW",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        Contaminant.objects.create(
                uniprot_id = "TESTVIEW2",
                category = category,
                short_name = "TEST2",
                long_name = "View testing 2",
                sequence = "ABCDEFG",
                organism = "Luigi",
                )
        response = self.client.get(
                reverse('ContaMiner:contabase')
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['contabase']), 1)

    def test_get_gives_category_from_current_contabase(self):
        ContaBase.objects.create(obsolete = True)
        ContaBase.objects.create()
        contabase_obsolete = ContaBase.objects.filter(obsolete = True)[0]
        contabase = ContaBase.get_current()

        Category.objects.create(
                number = 1,
                name = "Not obsolete",
                contabase = contabase,
                )
        Category.objects.create(
                number = 1,
                name = "Obsolete",
                contabase = contabase_obsolete,
                )
        category = Category.objects.filter(
                contabase = contabase)[0]
        category_obsolete = Category.objects.filter(
                contabase = contabase_obsolete)[0]

        Contaminant.objects.create(
                uniprot_id = "TESTVIEW",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        Contaminant.objects.create(
                uniprot_id = "TESTVIEW",
                category = category_obsolete,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        response = self.client.get(
                reverse('ContaMiner:contabase')
                )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['contabase']), 1)
        self.assertEqual(response.context['contabase'][0]['name'],
                'Not obsolete')


class SubmitJobViewTestCase(TestCase):
    """
        Test the views related to the submit form
    """
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.test_file = tempfile.NamedTemporaryFile(suffix='.mtz')
        self.test_file.write("Foooo")
        self.test_file.seek(0)
        self.post_data = {
                'email_address': 'you@example.com',
                'name': 'Test',
                'P0ACJ8': 'on',
                'P0AA25': 'on',
                'diffraction_data': self.test_file,
                }
        self.mock_job_instance = mock.MagicMock()
        self.mock_job_instance.id = 666
        self.mock_job_instance.get_filename.return_value = "test_file.mtz"

    def test_get_returns_message_on_empty_contabase(self):
        response = self.client.get(
                reverse('ContaMiner:submit')
                )
        messages = response.context['messages']
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(["empty" in str(e) for e in messages]))

    def test_post_returns_message_fail_on_empty_data(self):
        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        response = self.client.post(
                reverse('ContaMiner:submit'),
                follow = True,
                )

        self.assertEqual(response.status_code, 200)
        messages = response.context['messages']
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(['form' in str(e) for e in messages]))

    @mock.patch('contaminer.views.Job')
    def test_post_returns_message_fail_on_missing_file(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance

        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        post_data = self.post_data
        del post_data['diffraction_data']
        response = self.client.post(
                reverse('ContaMiner:submit'),
                post_data,
                follow = True,
                )

        self.assertEqual(response.status_code, 200)
        messages = response.context['messages']
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(['form' in str(e) for e in messages]))

    @mock.patch('contaminer.views.Job')
    def test_post_returns_message_fail_on_missing_contaminants(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance

        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        post_data = self.post_data
        del post_data['P0ACJ8']
        del post_data['P0AA25']
        response = self.client.post(
                reverse('ContaMiner:submit'),
                post_data,
                follow = True,
                )

        self.assertEqual(response.status_code, 200)
        messages = response.context['messages']
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(['contaminants' in str(e) for e in messages]))

    @mock.patch('contaminer.views.Job')
    def test_post_returns_message_success_on_good_input(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance

        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        response = self.client.post(
                reverse('ContaMiner:submit'),
                self.post_data,
                follow = True,
                )

        self.assertEqual(response.status_code, 200)
        messages = response.context['messages']
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(['submitted' in str(e) for e in messages]))

    @mock.patch('contaminer.views.Job')
    def test_post_creates_correct_job(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance

        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        response = self.client.post(
                reverse('ContaMiner:submit'),
                self.post_data,
                follow = True,
                )

        args, kwargs = mock_Job.create.call_args
        self.assertEqual(kwargs['confidential'], False)
        self.assertEqual(kwargs['email'], "you@example.com")
        self.assertEqual(kwargs['name'], "Test")

    @mock.patch('contaminer.views.Job')
    def test_post_submit_good_parameters(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance

        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        response = self.client.post(
                reverse('ContaMiner:submit'),
                self.post_data,
                follow = True,
                )

        (data_f, cont), kwargs = self.mock_job_instance.submit.call_args
        self.assertEqual(cont, "P0ACJ8\nP0AA25")
        with open(data_f, 'r') as f:
            self.assertEqual(f.read(), "Foooo")

    @mock.patch('contaminer.views.Job')
    def test_post_submit_job(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance

        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        response = self.client.post(
                reverse('ContaMiner:submit'),
                self.post_data,
                follow = True,
                )

        self.assertTrue(self.mock_job_instance.submit.called)

    @mock.patch('contaminer.views.Job')
    def test_post_returns_redirect(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance

        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        category = Category.objects.create(
                number = 1,
                name = "Cat1",
                contabase = contabase,
                )
        contaminant1 = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "TEST",
                long_name = "View testing",
                sequence = "ABCDEF",
                organism = "Mario",
                )
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = category,
                short_name = "TESTOBS",
                long_name = "View testing obs",
                sequence = "ABCDEFOBS",
                organism = "Mario obs",
                )

        response = self.client.post(
                reverse('ContaMiner:submit'),
                self.post_data,
                )

        self.assertEqual(response.status_code, 302)
