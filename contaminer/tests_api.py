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
from django.urls import reverse
from django.http import Http404
import mock

from .views_api import ContaminantView
from .views_api import ContaminantsView
from .views_api import CategoryView
from .views_api import CategoriesView
from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant

import json

class CategoriesViewTestCase(TestCase):
    """
        Test the ContaminantsView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_empty_contabase(self):
        request = self.factory.get(
                reverse('ContaMiner:API:categories')
                )
        with self.assertRaises(Http404):
            response = CategoriesView.as_view()(request)

    def test_get_valid_contaminants_list(self):
        ContaBase.objects.create()
        contabase = ContaBase.get_current()
        Category.objects.create(
                number = 1,
                name = "Test views",
                contabase = contabase,
                )
        Category.objects.create(
                number = 2,
                name = "Test views 2",
                contabase = contabase,
                selected_by_default = True,
                )
        request = self.factory.get(
                reverse('ContaMiner:API:categories')
                )
        response = CategoriesView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'categories': [
                            {
                                'id': 1,
                                'name': 'Test views',
                                'selected_by_default': False,
                            }, {
                                'id': 2,
                                'name': 'Test views 2',
                                'selected_by_default': True,
                            }
                        ]
                    }
                )

    def test_get_gives_contaminant_from_current_contabase(self):
        ContaBase.objects.create(obsolete = True)
        ContaBase.objects.create()
        contabase_obsolete = ContaBase.objects.filter(obsolete = True)[0]
        contabase = ContaBase.get_current()

        Category.objects.create(
                number = 1,
                name = "Test views",
                contabase = contabase,
                )
        Category.objects.create(
                number = 1,
                name = "Test views obsolete",
                contabase = contabase_obsolete,
                )
        request = self.factory.get(
                reverse('ContaMiner:API:categories')
                )
        response = CategoriesView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'categories': [
                            {
                                'id': 1,
                                'name': 'Test views',
                                'selected_by_default': False,
                            }
                        ]
                    }
                )


class CategoryViewTestCase(TestCase):
    """
        Test the CategoryView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_wrong_id(self):
        request = self.factory.get(
                reverse('ContaMiner:API:category', args = [25])
                )
        with self.assertRaises(Http404):
            response = CategoryView.as_view()(request, 25)

    def test_get_valid_category(self):
        ContaBase.objects.create()
        contabase = ContaBase.objects.all()[0]
        Category.objects.create(
                number = 1,
                name = "Test views",
                contabase = contabase,
                )
        request = self.factory.get(
                reverse('ContaMiner:API:category', args = [1])
                )
        response = CategoryView.as_view()(request, 1)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'id': 1,
                        'name': 'Test views',
                        'selected_by_default': False,
                    }
                )

    def test_get_gives_category_from_current_contabase(self):
        ContaBase.objects.create(obsolete = True)
        ContaBase.objects.create()
        contabase_obsolete = ContaBase.objects.filter(obsolete = True)[0]
        contabase = ContaBase.get_current()

        Category.objects.create(
                number = 1,
                name = "Test views",
                contabase = contabase,
                )
        Category.objects.create(
                number = 1,
                name = "Test views obsolete",
                contabase = contabase_obsolete,
                )

        request = self.factory.get(
                reverse('ContaMiner:API:category', args = [1])
                )
        response = CategoryView.as_view()(request, 1)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'id': 1,
                        'name': 'Test views',
                        'selected_by_default': False,
                    }
                )


class ContaminantsViewTestCase(TestCase):
    """
        Test the ContaminantsView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_empty_contabase(self):
        request = self.factory.get(
                reverse('ContaMiner:API:contaminants')
                )
        with self.assertRaises(Http404):
            response = ContaminantsView.as_view()(request)

    def test_get_valid_contaminants_list(self):
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
        request = self.factory.get(
                reverse('ContaMiner:API:contaminants')
                )
        response = ContaminantsView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'contaminants': [
                            {
                                'uniprot_id': 'TESTVIEW',
                                'short_name': 'TEST',
                                'long_name': 'View testing',
                                'sequence': 'ABCDEF',
                                'organism': 'Mario',
                            }, {
                                'uniprot_id': 'TESTVIEW2',
                                'short_name': 'TEST2',
                                'long_name': 'View testing 2',
                                'sequence': 'ABCDEFG',
                                'organism': 'Luigi',
                            }
                        ]
                    }
                )

    def test_get_gives_contaminant_from_current_contabase(self):
        ContaBase.objects.create(obsolete = True)
        ContaBase.objects.create()
        contabase_obsolete = ContaBase.objects.filter(obsolete = True)[0]
        contabase = ContaBase.get_current()

        Category.objects.create(
                number = 1,
                name = "Test views",
                contabase = contabase,
                )
        Category.objects.create(
                number = 1,
                name = "Test views",
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

        request = self.factory.get(
                reverse('ContaMiner:API:contaminants')
                )
        response = ContaminantsView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'contaminants': [
                            {
                                'uniprot_id': 'TESTVIEW',
                                'short_name': 'TEST',
                                'long_name': 'View testing',
                                'sequence': 'ABCDEF',
                                'organism': 'Mario',
                            }
                        ]
                    }
                )


class ContaminantViewTestCase(TestCase):
    """
        Test the ContaminantView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_wrong_uniprot_id(self):
        request = self.factory.get(
                reverse('ContaMiner:API:contaminant', args = [25])
                )
        with self.assertRaises(Http404):
            response = ContaminantView.as_view()(request, 25)

    def test_get_valid_contaminant(self):
        ContaBase.objects.create()
        contabase = ContaBase.objects.all()[0]
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
        request = self.factory.get(
                reverse('ContaMiner:API:contaminant', args = ["TESTVIEW"])
                )
        response = ContaminantView.as_view()(request, "TESTVIEW")
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'uniprot_id': 'TESTVIEW',
                        'short_name': 'TEST',
                        'long_name': 'View testing',
                        'sequence': 'ABCDEF',
                        'organism': 'Mario',
                    }
                )

    def test_get_gives_contaminant_from_current_contabase(self):
        ContaBase.objects.create(obsolete = True)
        ContaBase.objects.create()
        contabase_obsolete = ContaBase.objects.filter(obsolete = True)[0]
        contabase = ContaBase.get_current()

        Category.objects.create(
                number = 1,
                name = "Test views",
                contabase = contabase,
                )
        Category.objects.create(
                number = 1,
                name = "Test views",
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

        request = self.factory.get(
                reverse('ContaMiner:API:contaminant', args = ["TESTVIEW"])
                )
        response = ContaminantView.as_view()(request, "TESTVIEW")
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'uniprot_id': 'TESTVIEW',
                        'short_name': 'TEST',
                        'long_name': 'View testing',
                        'sequence': 'ABCDEF',
                        'organism': 'Mario',
                    }
                )
