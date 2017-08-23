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
from django.contrib.auth.models import User
from django.urls import reverse
import mock


from .views import ContaBaseView
from .views import SubmitJobView
from .views import DisplayJobView
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
import shutil
import os


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
    def clean_tmp_dir(self):
        try:
            shutil.rmtree(self.test_file.name.split('.')[0])
        except OSError:
            pass

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
        self.mock_job_instance.submit.side_effect = self.rm_dir
        self.addCleanup(self.clean_tmp_dir)

    def rm_dir(self, filename, _):
        try:
            shutil.rmtree(os.path.dirname(filename))
        except OSError:
            pass

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

    @mock.patch('contaminer.views_tools.Job')
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

    @mock.patch('contaminer.views_tools.Job')
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

    @mock.patch('contaminer.views_tools.Job')
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

    @mock.patch('contaminer.views_tools.Job')
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

    @mock.patch('contaminer.views_tools.Job')
    def test_post_submit_good_parameters(self, mock_Job):
        self.mock_job_instance.submit.side_effect = None
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

        dir_to_rm = os.path.dirname(
                self.mock_job_instance.submit.call_args[0][0]
                )
        shutil.rmtree(dir_to_rm)

    @mock.patch('contaminer.views_tools.Job')
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

    @mock.patch('contaminer.views_tools.Job')
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

    @mock.patch('contaminer.views_tools.Job.submit')
    def test_post_accept_AnonymousUser(self, mock_submit):
        mock_submit.side_effect = self.rm_dir
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

        try:
            response = self.client.post(
                    reverse('ContaMiner:submit'),
                    self.post_data,
                    )
        except ValueError as e:
            self.fail("ValueError raised: " + str(e))


class DisplayJobViewTestCase(TestCase):
    """
        Test the DisplayJobView
    """
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self.contabase = ContaBase.objects.create()
        self.category = Category.objects.create(
            contabase = self.contabase,
            number = 1,
            name = "Protein in E.Coli",
            )
        self.contaminant = Contaminant.objects.create(
            uniprot_id = "P0ACJ8",
            category = self.category,
            short_name = "CRP_ECOLI",
            long_name = "cAMP-activated global transcriptional regulator",
            sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
            organism = "Escherichia coli",
            )
        self.pack = Pack.objects.create(
            contaminant = self.contaminant,
            number = 5,
            structure= '5-mer',
            )
        self.model = Model.objects.create(
            pdb_code = "ACBD",
            chain = "A",
            domain = "1",
            nb_residues = 1,
            identity = 2,
            pack = self.pack,
            )
        self.job = Job.create(
            name = "test",
            email = "me@example.com",
            )
        self.task = Task.objects.create(
            job = self.job,
            pack = self.pack,
            space_group = "P-1-2-1",
            status_complete = True,
            percent = 40,
            q_factor = 0.53,
            )

    def test_smoke(self):
        self.job.status_complete = True
        self.job.save()
        response = self.client.get(
                reverse('ContaMiner:display', args = [self.job.id]),
                )
        self.assertEqual(response.status_code, 200)

    def test_do_not_show_confidential_job(self):
        self.job.confidential = True
        user = User.objects.create_user(
                username = 'SpongeBob',
                email = 'bob@sea.com',
                password = 'squarepants',
                )
        self.job.author = user
        self.job.save()

        response = self.client.get(
                reverse('ContaMiner:display', args = [self.job.id]),
                follow = True,
                )
        messages = response.context['messages']
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(['confidential' in str(e) for e in messages]))

    def test_show_confidential_if_logged_in_good_user(self):
        self.job.confidential = True
        user = User.objects.create_user(
                username = 'SpongeBob',
                email = 'bob@sea.com',
                password = 'squarepants',
                )
        self.job.author = user
        self.job.save()

        self.client.login(username = 'SpongeBob', password = 'squarepants')
        response = self.client.get(
                reverse('ContaMiner:display', args = [self.job.id]),
                follow = True,
                )
        messages = response.context['messages']
        self.assertTrue(all(['confidential' not in str(e) for e in messages]))

    def test_no_show_confidential_if_logged_in_wrong_user(self):
        self.job.confidential = True
        user = User.objects.create_user(
                username = 'SpongeBob',
                email = 'bob@sea.com',
                password = 'squarepants',
                )
        user2 = User.objects.create_user(
                username = 'Alice',
                email = 'alice@example.com',
                password = 'password',
                )
        self.job.author = user
        self.job.save()

        self.client.login(username = 'Alice', password = 'password')
        response= self.client.get(
                reverse('ContaMiner:display', args = [self.job.id]),
                follow = True,
                )

        messages = response.context['messages']
        self.assertTrue(len(messages) >= 1)
        self.assertTrue(any(['confidential' in str(e) for e in messages]))

    def test_404_on_non_existing_job(self):
        response = self.client.get(
                reverse('ContaMiner:display', args = [200]),
                )
        self.assertEqual(response.status_code, 404)

    def test_display_even_if_non_complete(self):
        self.job.status_complete = False
        self.job.save()
        response = self.client.get(
                reverse('ContaMiner:display', args = [self.job.id]),
                follow = True,
                )
        self.assertEqual(response.status_code, 200)


class UglymolViewTestCase(TestCase):
    """Test the Uglymol view"""
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        self.contabase = ContaBase.objects.create()
        self.category = Category.objects.create(
                contabase = self.contabase,
                number = 1,
                name = "Protein in E.Coli",
                )
        self.contaminant = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = self.category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        self.pack = Pack.objects.create(
                contaminant = self.contaminant,
                number = 5,
                structure= '5-mer',
                )
        self.model = Model.objects.create(
                pdb_code = "ACBD",
                chain = "A",
                domain = "1",
                nb_residues = 1,
                identity = 2,
                pack = self.pack,
                )
        self.job = Job.create(
                name = "test",
                email = "me@example.com",
                )
        self.task = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-1-2-1",
                status_complete = True,
                percent = 40,
                q_factor = 0.53,
                )

    def test_smoke(self):
        self.job.status_complete = True
        self.job.save()
        response = self.client.get(
                reverse('ContaMiner:uglymol',
                    args = [self.job.id, self.task.name()]))
        self.assertEqual(response.status_code, 200)

    def test_return_404_if_task_not_found(self):
        self.job.status_complete = True
        self.job.save()
        response = self.client.get(
                reverse('ContaMiner:uglymol',
                    args = [self.job.id, self.task.name() + '1']))
        self.assertEqual(response.status_code, 404)
