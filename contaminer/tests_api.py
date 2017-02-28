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

from .views_api import ContaBaseView
from .views_api import CategoriesView
from .views_api import DetailedCategoriesView
from .views_api import CategoryView
from .views_api import DetailedCategoryView
from .views_api import ContaminantsView
from .views_api import DetailedContaminantsView
from .views_api import ContaminantView
from .views_api import DetailedContaminantView
from .views_api import JobView
from .views_api import JobStatusView
from .models.contabase import ContaBase
from .models.contabase import Category
from .models.contabase import Contaminant
from .models.contabase import Pack
from .models.contabase import Model
from .models.contabase import Reference
from .models.contabase import Suggestion
from .models.contaminer import Job

import json
import tempfile
import time

class ContaBaseViewTestCase(TestCase):
    """
        Test the DetailedContaminantsView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_empty_contabase(self):
        request = self.factory.get(
                reverse('ContaMiner:API:contabase')
                )
        with self.assertRaises(Http404):
            response = ContaBaseView.as_view()(request)

    def test_get_valid_categoriess_list(self):
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
                reverse('ContaMiner:API:contabase')
                )
        response = ContaBaseView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'categories': [
                            {
                                'id': 1,
                                'name': 'Test views',
                                'selected_by_default': False,
                                'contaminants': [
                                    {
                                        'uniprot_id': 'TESTVIEW',
                                        'short_name': 'TEST',
                                        'long_name': 'View testing',
                                        'sequence': 'ABCDEF',
                                        'organism': 'Mario',
                                        'packs': [],
                                    }, {
                                        'uniprot_id': 'TESTVIEW2',
                                        'short_name': 'TEST2',
                                        'long_name': 'View testing 2',
                                        'sequence': 'ABCDEFG',
                                        'organism': 'Luigi',
                                        'packs': [],
                                    }
                                ]
                            },
                        ]
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
                reverse('ContaMiner:API:contabase')
                )
        response = ContaBaseView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'categories': [
                            {
                                'id': 1,
                                'name': 'Test views',
                                'selected_by_default': False,
                                'contaminants': [
                                    {
                                        'uniprot_id': 'TESTVIEW',
                                        'short_name': 'TEST',
                                        'long_name': 'View testing',
                                        'sequence': 'ABCDEF',
                                        'organism': 'Mario',
                                        'packs': [],
                                    },
                                ]
                            },
                        ]
                    }
                )


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


class DetailedContaminantsViewTestCase(TestCase):
    """
        Test the DetailedContaminantsView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_empty_contabase(self):
        request = self.factory.get(
                reverse('ContaMiner:API:detailed_categories')
                )
        with self.assertRaises(Http404):
            response = DetailedCategoriesView.as_view()(request)

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
                reverse('ContaMiner:API:detailed_categories')
                )
        response = DetailedCategoriesView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'categories': [
                            {
                                'id': 1,
                                'name': 'Test views',
                                'selected_by_default': False,
                                'contaminants': [
                                    {
                                        'uniprot_id': 'TESTVIEW',
                                        'short_name': 'TEST',
                                        'long_name': 'View testing',
                                        'sequence': 'ABCDEF',
                                        'organism': 'Mario',
                                        'packs': [],
                                    }, {
                                        'uniprot_id': 'TESTVIEW2',
                                        'short_name': 'TEST2',
                                        'long_name': 'View testing 2',
                                        'sequence': 'ABCDEFG',
                                        'organism': 'Luigi',
                                        'packs': [],
                                    }
                                ]
                            },
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
                        'categories': [
                            {
                                'id': 1,
                                'name': 'Test views',
                                'selected_by_default': False,
                                'contaminants': [
                                    {
                                        'uniprot_id': 'TESTVIEW',
                                        'short_name': 'TEST',
                                        'long_name': 'View testing',
                                        'sequence': 'ABCDEF',
                                        'organism': 'Mario',
                                    },
                                ]
                            },
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


class DetailedCategoryViewTestCase(TestCase):
    """
        Test the DetailedCategoryView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_empty_contabase(self):
        request = self.factory.get(
                reverse('ContaMiner:API:detailed_category', args = [25])
                )
        with self.assertRaises(Http404):
            response = DetailedCategoryView.as_view()(request, 25)

    def test_get_valid_category(self):
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
        contaminant = Contaminant.objects.get(
                uniprot_id = "TESTVIEW",
                )
        Pack.objects.create(
                number = 1,
                contaminant = contaminant,
                structure = '1-mer',
                )
        pack = Pack.objects.get(
                number = 1,
                contaminant = contaminant,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = "3RYT",
                chain = 'A',
                domain = 1,
                identity = 95,
                nb_residues = 56,
                )
        Suggestion.objects.create(
                name = "Gros chat",
                contaminant = contaminant,
                )
        Reference.objects.create(
                pubmed_id = "12345",
                contaminant = contaminant,
                )

        request = self.factory.get(
                reverse('ContaMiner:API:detailed_category',
                    args = [1])
                )
        response = DetailedCategoryView.as_view()(request, 1)
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'id': 1,
                        'name': 'Test views',
                        'selected_by_default': False,
                        'contaminants': [
                            {
                                'uniprot_id': 'TESTVIEW',
                                'short_name': 'TEST',
                                'long_name': 'View testing',
                                'sequence': 'ABCDEF',
                                'organism': 'Mario',
                                'packs': [
                                    {
                                        'number': 1,
                                        'structure': '1-mer',
                                        'models': [
                                            {
                                                'template': '3RYT',
                                                'chain': 'A',
                                                'domain': 1,
                                                'identity': 95,
                                                'residues': 56,
                                            },
                                        ]
                                    },
                                ],
                                'references': [
                                    {
                                        'pubmed_id': 12345,
                                    },
                                ],
                                'suggestions': [
                                    {
                                        'name': 'Gros chat',
                                    },
                                ],
                            },
                        ]
                    }
                )

    def test_get_gives_contaminants_from_current_contabase(self):
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
        response = DetailedContaminantsView.as_view()(request)
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
                                'packs': [],
                            },
                        ]
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


class DetailedContaminantsViewTestCase(TestCase):
    """
        Test the DetailedContaminantView views
    """
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_returns_404_on_empty_contabase(self):
        request = self.factory.get(
                reverse('ContaMiner:API:detailed_contaminants')
                )
        with self.assertRaises(Http404):
            response = DetailedContaminantsView.as_view()(request)

    def test_get_valid_contaminants(self):
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
        contaminant = Contaminant.objects.get(
                uniprot_id = "TESTVIEW",
                )
        Pack.objects.create(
                number = 1,
                contaminant = contaminant,
                structure = '1-mer',
                )
        pack = Pack.objects.get(
                number = 1,
                contaminant = contaminant,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = "3RYT",
                chain = 'A',
                domain = 1,
                identity = 95,
                nb_residues = 56,
                )
        Suggestion.objects.create(
                name = "Gros chat",
                contaminant = contaminant,
                )
        Reference.objects.create(
                pubmed_id = "12345",
                contaminant = contaminant,
                )

        request = self.factory.get(
                reverse('ContaMiner:API:detailed_contaminant',
                    args = ["TESTVIEW"])
                )
        response = DetailedContaminantsView.as_view()(request)
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
                                'packs': [
                                    {
                                        'number': 1,
                                        'structure': '1-mer',
                                        'models': [
                                            {
                                                'template': '3RYT',
                                                'chain': 'A',
                                                'domain': 1,
                                                'identity': 95,
                                                'residues': 56,
                                            },
                                        ]
                                    },
                                ],
                                'references': [
                                    {
                                        'pubmed_id': 12345,
                                    },
                                ],
                                'suggestions': [
                                    {
                                        'name': 'Gros chat',
                                    },
                                ],
                            },
                        ]
                    }
                )

    def test_get_gives_contaminants_from_current_contabase(self):
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
        response = DetailedContaminantsView.as_view()(request)
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
                                'packs': [],
                            },
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


class DetailedContaminantViewTestCase(TestCase):
    """
        Test the DetailedContaminantView views
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
        contaminant = Contaminant.objects.get(
                uniprot_id = "TESTVIEW",
                )
        Pack.objects.create(
                number = 1,
                contaminant = contaminant,
                structure = '1-mer',
                )
        pack = Pack.objects.get(
                number = 1,
                contaminant = contaminant,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = "3RYT",
                chain = 'A',
                domain = 1,
                identity = 95,
                nb_residues = 56,
                )
        Suggestion.objects.create(
                name = "Gros chat",
                contaminant = contaminant,
                )
        Reference.objects.create(
                pubmed_id = "12345",
                contaminant = contaminant,
                )

        request = self.factory.get(
                reverse('ContaMiner:API:detailed_contaminant',
                    args = ["TESTVIEW"])
                )
        response = DetailedContaminantView.as_view()(request, "TESTVIEW")
        self.assertEqual(response.status_code, 200)

        response_data = response.content
        self.assertJSONEqual(response_data,
                    {
                        'uniprot_id': 'TESTVIEW',
                        'short_name': 'TEST',
                        'long_name': 'View testing',
                        'sequence': 'ABCDEF',
                        'organism': 'Mario',
                        'packs': [
                            {
                                'number': 1,
                                'structure': '1-mer',
                                'models': [
                                    {
                                        'template': '3RYT',
                                        'chain': 'A',
                                        'domain': 1,
                                        'identity': 95,
                                        'residues': 56,
                                    },
                                ]
                            },
                        ],
                        'references': [
                            {
                                'pubmed_id': 12345,
                            },
                        ],
                        'suggestions': [
                            {
                                'name': 'Gros chat',
                            },
                        ],
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


class JobViewTestCase(TestCase):
    """
        Test the JobView views
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.test_file = tempfile.NamedTemporaryFile(suffix='.mtz')
        self.post_data = {
                'email_address': 'you@example.com',
                'name': 'Test',
                'contaminants': 'P0ACJ8,P0AA25',
                }
        self.mock_job_instance = mock.MagicMock()
        self.mock_job_instance.id = 666
        self.mock_job_instance.get_filename.return_value = "test_file.mtz"

    def test_post_returns_400_on_empty_data(self):
        request = self.factory.post(
                reverse('ContaMiner:API:job')
                )
        response = JobView.as_view()(request)
        self.assertEqual(response.status_code, 400)

    def test_post_returns_400_on_missing_file(self):
        request = self.factory.post(
                reverse('ContaMiner:API:job'),
                self.post_data,
                )
        response = JobView.as_view()(request)
        self.assertEqual(response.status_code, 400)

    @mock.patch('contaminer.views_api.Job')
    def test_post_returns_200_on_good_input(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance
        request = self.factory.post(
                reverse('ContaMiner:API:job'),
                self.post_data,
                )
        request.FILES['diffraction_data'] = self.test_file

        response = JobView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    @mock.patch('contaminer.views_api.Job')
    def test_post_creates_correct_job(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance
        request = self.factory.post(
                reverse('ContaMiner:API:job'),
                self.post_data,
                )
        request.FILES['diffraction_data'] = self.test_file

        response = JobView.as_view()(request)
        mock_Job.create.assert_called_once_with(
                email = 'you@example.com',
                name = 'Test',
                )

    @mock.patch('contaminer.views_api.Job')
    def test_post_submit_job(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance
        request = self.factory.post(
                reverse('ContaMiner:API:job'),
                self.post_data,
                )
        request.FILES['diffraction_data'] = self.test_file

        response = JobView.as_view()(request)
        self.mock_job_instance.submit.assert_called_once()
        args, kwargs = self.mock_job_instance.submit.call_args
        self.assertEqual(args[1], "P0ACJ8\nP0AA25")

    @mock.patch('contaminer.views_api.Job')
    def test_post_returns_job_id(self, mock_Job):
        mock_Job.create.return_value = self.mock_job_instance
        request = self.factory.post(
                reverse('ContaMiner:API:job'),
                self.post_data,
                )
        request.FILES['diffraction_data'] = self.test_file

        response = JobView.as_view()(request)
        self.assertJSONEqual(response.content,
                {
                    'error': False,
                    'id': 666,
                }
                )


class JobStatusTestCase(TestCase):
    """
        Test the JobStatusView views
    """
    def setUp(self):
        self.factory = RequestFactory()
        self.job = Job.objects.create(name = "Test")

    def test_jobstatus_returns_404_on_wrong_id(self):
        request = self.factory.get(
                reverse('ContaMiner:API:job_status', args = [25])
                )
        with self.assertRaises(Http404):
            response = JobStatusView.as_view()(request, 25)

    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_job_status_returns_good_status(self, mock__):
        request = self.factory.get(
                reverse('ContaMiner:API:job_status', args = [self.job.id])
                )
        response = JobStatusView.as_view()(request, self.job.id)
        self.assertJSONEqual(response.content,
                {
                    'id': self.job.id,
                    'status': 'New',
                })

        self.job.status_submitted = True
        self.job.save()
        response = JobStatusView.as_view()(request, self.job.id)
        self.assertJSONEqual(response.content,
                {
                    'id': self.job.id,
                    'status': 'Submitted',
                })

        self.job.status_running = True
        self.job.save()
        response = JobStatusView.as_view()(request, self.job.id)
        self.assertJSONEqual(response.content,
                {
                    'id': self.job.id,
                    'status': 'Running',
                })

        self.job.status_complete = True
        self.job.save()
        response = JobStatusView.as_view()(request, self.job.id)
        self.assertJSONEqual(response.content,
                {
                    'id': self.job.id,
                    'status': 'Complete',
                })

        self.job.status_error = True
        self.job.save()
        response = JobStatusView.as_view()(request, self.job.id)
        self.assertJSONEqual(response.content,
                {
                    'id': self.job.id,
                    'status': 'Error',
                })
