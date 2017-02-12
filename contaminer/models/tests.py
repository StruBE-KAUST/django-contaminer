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
from django.core.exceptions import ValidationError
from django.core.exceptions import MultipleObjectsReturned
import mock

from .contabase import ContaBase
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


class ContaBaseTestCase(TestCase):
    """
        Test the ContaBase model
    """
    def test_ContaBase_is_well_displayed(self):
        contabase = ContaBase.objects.create()
        id = contabase.id
        self.assertEqual(str(contabase), str(id) + ' - current')

    def test_ContaBase_get_current_gives_result(self):
        contabase = ContaBase.objects.create()
        id_current = ContaBase.objects.all()[0].id
        ContaBase.objects.create(obsolete = True)
        id_result = ContaBase.get_current().id
        self.assertEqual(id_current, id_result)

    def test_ContaBase_get_current_raises_exception_if_two_current(self):
        ContaBase.objects.create()
        ContaBase.objects.create()
        with self.assertRaises(MultipleObjectsReturned):
            ContaBase.get_current()

    def test_make_obsolete(self):
        contabase = ContaBase.objects.create()
        contabase.make_obsolete()
        self.assertTrue(contabase.obsolete)

    def test_make_all_obsolete(self):
        contabase_list = [ContaBase.objects.create() for i in range(3)]
        ContaBase.make_all_obsolete()
        map(lambda x: self.assertFalse(x.obsolete), contabase_list)

    def test_make_all_obsolete_raise_nothing_on_empty_db(self):
        try:
            ContaBase.make_all_obsolete()
        except Exception as e:
            self.fail(e)


class CategoryTestCase(TestCase):
    """
        Test the Category model
    """
    def setUp(self):
        ContaBase.objects.create()
        self.contabase = ContaBase.objects.all()[0]
        ContaBase.objects.create(obsolete = True)
        self.contabase_obsolete = ContaBase.objects.filter(
                obsolete = True,
                )[0]
        Category.objects.create(
                number = 1,
                name = "Protein in E.Coli",
                contabase = self.contabase,
                )
        Category.objects.create(
                number = 2,
                name = "Protein in yeast",
                contabase = self.contabase,
                selected_by_default = True,
                )
        Category.objects.create(
                number = 3,
                name = "Obsolete protein",
                contabase = self.contabase_obsolete,
                )

    def test_Category_is_well_displayed(self):
        category1 = Category.objects.get(
                name = "Protein in E.Coli",
                )
        category2 = Category.objects.get(
                name = "Protein in yeast",
                )
        category3 = Category.objects.get(
                name = "Obsolete protein",
                )
        self.assertEqual(str(category1), 'Protein in E.Coli - False')
        self.assertEqual(str(category2), 'Protein in yeast - True')
        self.assertEqual(str(category3), 'Obsolete protein - False (obsolete)')

    def test_Category_number_is_unique_per_contabase(self):
        category1 = Category.objects.get(
                name = "Protein in E.Coli",
                )
        with self.assertRaises(ValidationError):
            Category.objects.create(
                    number = 1,
                    name = "Another name",
                    contabase = self.contabase,
                    )

    def test_Category_can_be_same_in_different_contabase(self):
        try:
            Category.objects.create(
                    number = 1,
                    name = "Protein in E.Coli",
                    contabase = self.contabase_obsolete,
                    )
        except ValidationError:
            self.fail("Same number should be possible in different contabases")


class ContaminantTestCase(TestCase):
    """
        Test the Contaminant model
    """
    def setUp(self):
        ContaBase.objects.create()
        contabase = ContaBase.objects.all()[0]
        Category.objects.create(
                number = 1,
                name = "Protein in E.Coli",
                contabase = contabase,
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
        ContaBase.objects.create()
        contabase = ContaBase.objects.all()[0]
        Category.objects.create(
                number = 1,
                name="Protein in E.Coli",
                contabase = contabase,
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

    def test_Pack_is_well_displayed(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 1
                )
        self.assertEqual(str(pack), 'P0ACJ8 - CRP_ECOLI - 1 (2-mer)')

    def test_Pack_number_is_unique_per_contaminant(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        with self.assertRaises(ValidationError):
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "2-mer",
                    )

    def test_Pack_structure_is_valid_structure(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        with self.assertRaises(ValidationError):
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 1,
                    structure = "other_struct",
                    )

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 2,
                    structure = "1-mer",
                    )
        except ValidationError:
            self.fail("Pack creation raised ValidationError.")

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 3,
                    structure = "2-mer",
                    )
        except ValidationError:
            self.fail("Pack creation raised ValidationError.")

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 4,
                    structure = "domain",
                    )
        except ValidationError:
            self.fail("Pack creation raised ValidationError.")

        try:
            Pack.objects.create(
                    contaminant = contaminant,
                    number = 5,
                    structure = "domains",
                    )
        except ValidationError:
            self.fail("Pack creation raised ValidationError.")


class ModelTestCase(TestCase):
    """
        Test the Model model
    """
    def setUp(self):
        ContaBase.objects.create()
        contabase = ContaBase.objects.all()[0]
        Category.objects.create(
                number = 1,
                name="Protein in E.Coli",
                contabase = contabase,
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
        self.assertEqual(str(model), 'P0ACJ8 - CRP_ECOLI - 1 (2-mer) - 1O3T')

    def test_Model_has_less_residues_than_contaminant(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 1,
                )
        with self.assertRaises(ValidationError):
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
        with self.assertRaises(ValidationError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 20,
                    identity = 101,
                    pack = pack,
                    )
        with self.assertRaises(ValidationError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 20,
                    identity = -1,
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
