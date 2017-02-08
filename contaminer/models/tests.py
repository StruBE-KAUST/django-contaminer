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
    Testing module for ContaMiner application
    =========================================

    This module contains unitary tests for the ContaMiner application.
"""

from django.test import TestCase

from .contabase import Category
from .contabase import Contaminant
from .contabase import Pack
from .contabase import Model
from .contabase import Reference
from .contabase import Suggestion

from .contaminer import Job


# TODO: UpperCaseCharField testing
# Difficult to test a custom field. Good behavior is tested through
# ContaminantTestCase


class CategoryTestCase(TestCase):
    """
        Test the Category model
    """
    def setUp(self):
        Category.objects.create(
                name = "Protein in E.Coli",
                )
        Category.objects.create(
                name = "Protein in yeast",
                selected_by_default = True,
                )

    def test_Category_is_well_displayed(self):
        category1 = Category.objects.get(
                name = "Protein in E.Coli",
                )
        category2 = Category.objects.get(
                name = "Protein in yeast",
                )
        self.assertEqual(str(category1), 'Protein in E.Coli - False')
        self.assertEqual(str(category2), 'Protein in yeast - True')

    def test_Category_id_is_different(self):
        category1 = Category.objects.get(
                name = "Protein in E.Coli",
                )
        category2 = Category.objects.get(
                name = "Protein in yeast",
                )
        self.assertNotEqual(category1.id, category2.id)


class ContaminantTestCase(TestCase):
    """
        Test the Contaminant model
    """
    def setUp(self):
        Category.objects.create(
                name = "Protein in E.Coli",
                )
        category = Category.objects.get(
                name = "Protein in E.Coli",
                )
        Contaminant.objects.create(
                uniprot_id = "P0acj8",
                category = category,
                short_name = "CRP_ecoli",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )

    def test_Contaminant_is_well_displayed(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        self.assertEqual(str(contaminant), 'P0ACJ8 - CRP_ECOLI')

    def test_Contaminant_uniprot_id_is_uppercase(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        self.assertEqual(contaminant.uniprot_id, 'P0ACJ8')

    def test_Contaminant_short_name_is_uppercase(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        self.assertEqual(contaminant.short_name, 'CRP_ECOLI')


class PackTestCase(TestCase):
    """
        Test the Pack model
    """
    def setUp(self):
        Category.objects.create(
                name="Protein in E.Coli",
                )
        category = Category.objects.get(
                name="Protein in E.Coli",
                )
        Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        Pack.objects.create(
                contaminant = contaminant,
                number = 1,
                structure = "dimer",
                )

    def test_Pack_is_well_displayed(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 1
                )
        self.assertEqual(str(pack), 'P0ACJ8 - CRP_ECOLI - 1 (dimer)')

    def test_Pack_number_is_unique_per_contaminant(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        with self.assertRaises(ValueError):
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "monomer",
                    )

    def test_Pack_structure_is_valid_structure(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        with self.assertRaises(ValueError):
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "other_struct",
                    )

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "1-mer",
                    )
        except ValueError:
            self.fail("Pack creation raised ValueError.")

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "2-mer",
                    )
        except ValueError:
            self.fail("Pack creation raised ValueError.")

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "domain",
                    )
        except ValueError:
            self.fail("Pack creation raised ValueError.")

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "domains",
                    )
        except ValueError:
            self.fail("Pack creation raised ValueError.")


class ModelTestCase(TestCase):
    """
        Test the Model model
    """
    def setUp(self):
        Category.objects.create(
                name="Protein in E.Coli",
                )
        category = Category.objects.get(
                name="Protein in E.Coli",
                )
        Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        Pack.objects.create(
                contaminant = contaminant,
                number = 1,
                structure = "2-mer",
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 1,
                )
        Model.objects.create(
                pdb_code = '1o3t',
                chain = 'B',
                domain = 1,
                nb_residues = 20,
                identity = 100,
                pack = pack,
                )

    def test_Model_is_well_displayed(self):
        model = Model.objects.get(
                pdb_code = '1O3T',
                )
        self.assertEqual(str(model), 'P0ACJ8 - CRP_ECOLI - 1 (dimer) - 1O3T')

    def test_Model_has_less_residues_than_contaminant(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 1,
                )
        with self.assertRaises(ValueError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 200,
                    identity = 100,
                    pack = pack,
                    )

    def test_Model_identity_is_valid_percentage(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 1,
                )
        with self.assertRaises(ValueError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 20,
                    identity = 101,
                    pack = pack,
                    )
        with self.assertRaises(ValueError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 20,
                    identity = 99,
                    pack = pack,
                    )


class ReferenceTestCase(TestCase):
    """
        Test the Reference model
    """
    def setUp(self):
        Category.objects.create(
                name = "Protein in E.Coli",
                )
        category = Category.objects.get(
                name = "Protein in E.Coli",
                )
        Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )


class SuggestionTestCase(TestCase):
    """
        Test the Suggestion model
    """
    def setUp(self):
        Category.objects.create(
                name = "Protein in E.Coli",
                )
        category = Category.objects.get(
                name = "Protein in E.Coli",
                )
        Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )


class JobTestCase(TestCase):
    """
        Test the Job model
    """
    def setUp(self):
        pass
