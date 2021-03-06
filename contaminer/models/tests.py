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
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import mock
import timeout_decorator

import lxml.etree as ET
import datetime

from .contabase import ContaBase
from .contabase import Category
from .contabase import Contaminant
from .contabase import Pack
from .contabase import Model
from .contabase import Reference
from .contabase import Suggestion

from .contaminer import Job
from .contaminer import Task


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

    @mock.patch('contaminer.models.contabase.Category')
    @mock.patch('contaminer.models.contabase.SSHChannel.get_contabase')
    def test_update_makes_only_one_none_obsolete(self, mock_get_contabase,
            mock_category):
        mock_get_contabase.return_value = "<contabase></contabase>"
        new_contabase = ContaBase.update()
        try:
            ContaBase.objects.get(obsolete = False)
        except Exception as e:
            self.fail(e)

    @mock.patch('contaminer.models.contabase.Category')
    @mock.patch('contaminer.models.contabase.SSHChannel.get_contabase')
    def test_update_creates_new_contabase(self, mock_get_contabase,
            mock_category):
        old_contabase_count = len(ContaBase.objects.all())
        mock_get_contabase.return_value = "<contabase></contabase>"
        new_contabase = ContaBase.update()
        new_contabase_count = len(ContaBase.objects.all())
        self.assertEqual(new_contabase_count, old_contabase_count + 1)

    @mock.patch('contaminer.models.contabase.Category.update')
    @mock.patch('contaminer.models.contabase.SSHChannel.get_contabase')
    def test_update_updates_good_parameters_category(self, mock_get_contabase,
            mock_category_update):
        xml_example = "" \
            + "<contabase>\n" \
            + "    <category>\n" \
            + "        <id>1</id>\n" \
            + "    </category>\n" \
            + "</contabase>"
        mock_get_contabase.return_value = xml_example
        ContaBase.update()
        contabase = ContaBase.get_current()
        _, args, _ = mock_category_update.mock_calls[0]
        self.assertEqual(contabase, args[0])

        category_dict = ET.Element('category')
        category_id = ET.SubElement(category_dict, 'id')
        category_id.text = '1'
        self.assertEqual(ET.tostring(category_dict), ET.tostring(args[1]))

    @mock.patch('contaminer.models.contabase.Category.update')
    @mock.patch('contaminer.models.contabase.SSHChannel.get_contabase')
    def test_update_updates_good_number_categories(self, mock_get_contabase,
            mock_category_update):
        xml_example = "" \
            + "<contabase>\n" \
            + "    <category>\n" \
            + "    </category>\n" \
            + "    <category>\n" \
            + "    </category>\n" \
            + "</contabase>"
        mock_get_contabase.return_value = xml_example
        ContaBase.update()
        self.assertEqual(len(mock_category_update.mock_calls), 2)

    @mock.patch('contaminer.models.contabase.Category.update')
    @mock.patch('contaminer.models.contabase.SSHChannel.get_contabase')
    def test_update_updates_raises_error_on_not_ready_CB(self,
            mock_get_contabase, mock_category_update):
        get_response = 'ContaBase is not ready\n'
        mock_get_contabase.return_value = get_response
        with self.assertRaises(RuntimeError):
            ContaBase.update()

    @mock.patch('contaminer.models.contabase.Category.update')
    @mock.patch('contaminer.models.contabase.SSHChannel.get_contabase')
    def test_update_updates_does_not_make_obsolete_on_not_ready_CB(self,
            mock_get_contabase, mock_category_update):
        get_response = 'ContaBase is not ready\n'
        ContaBase.objects.create()
        mock_get_contabase.return_value = get_response
        try:
            ContaBase.objects.get(obsolete=False)
        except Exception as e:
            self.fail(e)

    def test_to_detailed_dict_gives_correct_result(self):
        ContaBase.objects.create()
        contabase = ContaBase.get_current()

        Category.objects.create(
                number = 1,
                name = 'Test category',
                contabase = contabase,
                )
        category = Category.objects.get(
                number = 1,
                contabase = contabase,
                )
        Contaminant.objects.create(
                category = category,
                uniprot_id = 'P0ACJ8',
                short_name = 'CRP_ECOLI',
                long_name = 'regulator',
                sequence = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                organism= 'Mario',
                )
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                category = category,
                )
        Pack.objects.create(
                contaminant = contaminant,
                number = 5,
                structure= '5-mer',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 5,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 1,
                identity = 100,
                nb_residues = 112,
                )

        response_dict = contabase.to_detailed_dict()
        response_expected = {
                'categories': [
                    {
                        'id': 1,
                        'name': 'Test category',
                        'selected_by_default': False,
                        'contaminants': [
                            {
                                'uniprot_id': 'P0ACJ8',
                                'short_name': 'CRP_ECOLI',
                                'long_name': 'regulator',
                                'sequence': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                                'organism': 'Mario',
                                'packs': [
                                    {
                                        'number': 5,
                                        'structure': '5-mer',
                                        'models': [
                                            {
                                                'template': '3RYP',
                                                'chain': 'A',
                                                'domain': 1,
                                                'identity': 100,
                                                'residues': 112,
                                            },
                                        ]
                                    },
                                ]
                            },
                        ]
                    },
                ]
            }

        self.assertEqual(response_dict, response_expected)


class CategoryTestCase(TestCase):
    """
        Test the Category model
    """
    def setUp(self):
        self.contabase = ContaBase.objects.create()
        self.contabase_obsolete = ContaBase.objects.create(obsolete = True)
        self.category1 = Category.objects.create(
                number = 1,
                name = "Protein in E.Coli",
                contabase = self.contabase,
                )
        self.category2 = Category.objects.create(
                number = 2,
                name = "Protein in yeast",
                contabase = self.contabase,
                selected_by_default = True,
                )
        self.category3 = Category.objects.create(
                number = 3,
                name = "Obsolete protein",
                contabase = self.contabase_obsolete,
                )

    def test_Category_is_well_displayed(self):
        self.assertEqual(str(self.category1), 'Protein in E.Coli - False')
        self.assertEqual(str(self.category2), 'Protein in yeast - True')
        self.assertEqual(str(self.category3), 'Obsolete protein - False (obsolete)')

    def test_Category_number_is_unique_per_contabase(self):
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

    @mock.patch('contaminer.models.contabase.Contaminant.update')
    def test_update_updates_good_parameters_contaminant(self,
            mock_contaminant_update):
        contabase = ContaBase.get_current()
        xml_example = "" \
            + "<category>\n" \
            + "    <id>5</id>\n" \
            + "    <name>Protein test good params</name>\n" \
            + "    <default>true</default>\n" \
            + "    <contaminant>\n" \
            + "        <uniprot_id>P0ACJ8</uniprot_id>\n" \
            + "    </contaminant>\n" \
            + "</category>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        category_dict = ET.XML(xml_example, parser)

        Category.update(contabase, category_dict)

        category = Category.objects.get(
                number = 5,
                contabase = contabase,
                )
        _, args, _ = mock_contaminant_update.mock_calls[0]
        self.assertEqual(category, args[0])

        contaminant_dict = ET.Element('contaminant')
        contaminant_id = ET.SubElement(contaminant_dict, 'uniprot_id')
        contaminant_id.text = 'P0ACJ8'
        self.assertEqual(ET.tostring(contaminant_dict), ET.tostring(args[1]))

    @mock.patch('contaminer.models.contabase.Contaminant.update')
    def test_update_updates_good_number_contaminant(self,
            mock_contaminant_update):
        contabase = ContaBase.get_current()
        xml_example = "" \
            + "<category>\n" \
            + "    <id>6</id>\n" \
            + "    <name>Protein test good nb calls</name>\n" \
            + "    <default>true</default>\n" \
            + "    <contaminant>\n" \
            + "    </contaminant>\n" \
            + "    <contaminant>\n" \
            + "    </contaminant>\n" \
            + "</category>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        category_dict = ET.XML(xml_example, parser)

        Category.update(contabase, category_dict)

        self.assertEqual(len(mock_contaminant_update.mock_calls), 2)

    @mock.patch('contaminer.models.contabase.Contaminant.update')
    def test_update_creates_good_category(self,
            mock_contaminant_update):
        contabase = ContaBase.get_current()
        xml_example = "" \
            + "<category>\n" \
            + "    <id>7</id>\n" \
            + "    <name>Protein test good category</name>\n" \
            + "    <default>true</default>\n" \
            + "    <contaminant>\n" \
            + "        <uniprot_id>P0ACJ8</uniprot_id>\n" \
            + "    </contaminant>\n" \
            + "</category>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        category_dict = ET.XML(xml_example, parser)

        Category.update(contabase, category_dict)

        category = Category.objects.get(
                number = 7,
                contabase = contabase,
                )
        self.assertEqual(category.contabase, contabase)
        self.assertEqual(category.number, 7)
        self.assertEqual(category.name, "Protein test good category")
        self.assertTrue(category.selected_by_default)

    @mock.patch('contaminer.models.contabase.Contaminant.update')
    def test_update_creates_good_category_default_false(self,
            mock_contaminant_update):
        contabase = ContaBase.get_current()
        xml_example = "" \
            + "<category>\n" \
            + "    <id>8</id>\n" \
            + "    <name>Protein test false default</name>\n" \
            + "    <default>false</default>\n" \
            + "    <contaminant>\n" \
            + "        <uniprot_id>P0ACJ8</uniprot_id>\n" \
            + "    </contaminant>\n" \
            + "</category>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        category_dict = ET.XML(xml_example, parser)

        Category.update(contabase, category_dict)

        category = Category.objects.get(
                number = 8,
                contabase = contabase,
                )
        self.assertFalse(category.selected_by_default)

    def test_to_simple_dict_gives_correct_result(self):
        response_dict = self.category1.to_simple_dict()
        response_expected = {
                'id': 1,
                'name': "Protein in E.Coli",
                'selected_by_default': False,
            }

        self.assertEqual(response_dict, response_expected)

    def test_to_detailed_dict_gives_correct_result(self):
        contaminant = Contaminant.objects.create(
                category = self.category1,
                uniprot_id = 'P0ACJ8',
                short_name = 'CRP_ECOLI',
                long_name = 'regulator',
                sequence = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                organism= 'Mario',
                )
        pack = Pack.objects.create(
                contaminant = contaminant,
                number = 5,
                structure= '5-mer',
                )
        model = Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 1,
                identity = 100,
                nb_residues = 112,
                )
        contaminant = Contaminant.objects.create(
                category = self.category1,
                uniprot_id = 'P0ACJ9',
                short_name = 'CAN_ECOLI',
                long_name = 'regulator',
                sequence = 'ABCDEF',
                organism= 'Luigi',
                )
        pack = Pack.objects.create(
                contaminant = contaminant,
                number = 6,
                structure= '6-mer',
                )
        model = Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 2,
                identity = 100,
                nb_residues = 71,
                )
        response_dict = self.category1.to_detailed_dict()
        response_expected = {
                'id': 1,
                'name': 'Protein in E.Coli',
                'selected_by_default': False,
                'contaminants': [
                    {
                        'uniprot_id': 'P0ACJ8',
                        'short_name': 'CRP_ECOLI',
                        'long_name': 'regulator',
                        'sequence': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                        'organism': 'Mario',
                        'packs': [
                            {
                                'number': 5,
                                'structure': '5-mer',
                                'models': [
                                    {
                                        'template': '3RYP',
                                        'chain': 'A',
                                        'domain': 1,
                                        'identity': 100,
                                        'residues': 112,
                                    },
                                ]
                            },
                        ]
                    },
                    {
                        'uniprot_id': 'P0ACJ9',
                        'short_name': 'CAN_ECOLI',
                        'long_name': 'regulator',
                        'sequence': 'ABCDEF',
                        'organism': 'Luigi',
                        'packs' : [
                            {
                                'number': 6,
                                'structure': '6-mer',
                                'models': [
                                    {
                                        'template': '3RYP',
                                        'chain': 'A',
                                        'domain': 2,
                                        'identity': 100,
                                        'residues': 71,
                                    },
                                ]
                            },
                        ]
                    }
                ]
            }

        self.assertItemsEqual(response_dict, response_expected)

    def test_count_gives_good_result(self):
        Contaminant.objects.create(
                category = self.category1,
                uniprot_id = 'P0ACJ8',
                short_name = 'CRP_ECOLI',
                long_name = 'regulator',
                sequence = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                organism= 'Mario',
                )
        Contaminant.objects.create(
                category = self.category1,
                uniprot_id = 'P0ACJ9',
                short_name = 'CRP_ECOLI',
                long_name = 'regulator',
                sequence = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                organism= 'Mario',
                )
        Contaminant.objects.create(
                category = self.category2,
                uniprot_id = 'P0ACJ0',
                short_name = 'CRP_ECOLI',
                long_name = 'regulator',
                sequence = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                organism= 'Mario',
                )

        self.assertEqual(self.category1.count_contaminants, 2)
        self.assertEqual(self.category2.count_contaminants, 1)
        self.assertEqual(self.category3.count_contaminants, 0)


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
                uniprot_id = "P0ACJ8",
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

    def test_Contaminant_short_name_is_uppercase(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = "P0ACJ8",
                )
        self.assertEqual(contaminant.short_name, 'CRP_ECOLI')

    @mock.patch('contaminer.models.contabase.Reference.update')
    @mock.patch('contaminer.models.contabase.Suggestion.update')
    @mock.patch('contaminer.models.contabase.Pack.update')
    def test_update_updates_good_parameters_pack_ref_sugg(self,
            mock_pack_update, mock_suggestion_update,
            mock_reference_update):
        category = Category.objects.all()[0]
        xml_example = "" \
            + "<contaminant>\n" \
            + "    <uniprot_id>P61517</uniprot_id>\n" \
            + "    <short_name>CAN_ECOLI</short_name>\n" \
            + "    <long_name>Carbonic anhydrase</long_name>\n" \
            + "    <sequence>ABCDEFGHIJKLMNOPQRSTUVWXYZ</sequence>\n" \
            + "    <organism>Escherichia coli</organism>\n" \
            + "    <exact_model>true</exact_model>\n" \
            + "    <reference>\n" \
            + "        <id>3</id>\n" \
            + "    </reference>\n" \
            + "    <suggestion>\n" \
            + "        <id>2</id>\n" \
            + "    </suggestion>\n" \
            + "    <pack>\n" \
            + "        <id>1</id>\n" \
            + "    </pack>\n" \
            + "</contaminant>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        contaminant_dict = ET.XML(xml_example, parser)

        Contaminant.update(category, contaminant_dict)

        contaminant = Contaminant.objects.get(
                uniprot_id = 'P61517',
                )
        _, args, _ = mock_pack_update.mock_calls[0]
        self.assertEqual(contaminant, args[0])
        pack_dict = ET.Element('pack')
        pack_id = ET.SubElement(pack_dict, 'id')
        pack_id.text = '1'
        self.assertEqual(ET.tostring(pack_dict), ET.tostring(args[1]))

        _, args, _ = mock_suggestion_update.mock_calls[0]
        self.assertEqual(contaminant, args[0])
        suggestion_dict = ET.Element('suggestion')
        suggestion_id = ET.SubElement(suggestion_dict, 'id')
        suggestion_id.text = '2'
        self.assertEqual(ET.tostring(suggestion_dict), ET.tostring(args[1]))

        _, args, _ = mock_reference_update.mock_calls[0]
        self.assertEqual(contaminant, args[0])
        reference_dict = ET.Element('reference')
        reference_id = ET.SubElement(reference_dict, 'id')
        reference_id.text = '3'
        self.assertEqual(ET.tostring(reference_dict), ET.tostring(args[1]))

    @mock.patch('contaminer.models.contabase.Reference.update')
    @mock.patch('contaminer.models.contabase.Suggestion.update')
    @mock.patch('contaminer.models.contabase.Pack.update')
    def test_update_updates_good_number_pack_ref_sugg(self,
            mock_pack_update, mock_suggestion_update,
            mock_reference_update):
        category = Category.objects.all()[0]
        xml_example = "" \
            + "<contaminant>\n" \
            + "    <uniprot_id>P61517</uniprot_id>\n" \
            + "    <short_name>CAN_ECOLI</short_name>\n" \
            + "    <long_name>Carbonic anhydrase</long_name>\n" \
            + "    <sequence>ABCDEFGHIJKLMNOPQRSTUVWXYZ</sequence>\n" \
            + "    <organism>Escherichia coli</organism>\n" \
            + "    <exact_model>true</exact_model>\n" \
            + "    <reference>\n" \
            + "        <id>1</id>\n" \
            + "    </reference>\n" \
            + "    <reference>\n" \
            + "        <id>2</id>\n" \
            + "    </reference>\n" \
            + "    <reference>\n" \
            + "        <id>3</id>\n" \
            + "    </reference>\n" \
            + "    <reference>\n" \
            + "        <id>4</id>\n" \
            + "    </reference>\n" \
            + "    <suggestion>\n" \
            + "        <id>1</id>\n" \
            + "    </suggestion>\n" \
            + "    <suggestion>\n" \
            + "        <id>2</id>\n" \
            + "    </suggestion>\n" \
            + "    <suggestion>\n" \
            + "        <id>3</id>\n" \
            + "    </suggestion>\n" \
            + "    <pack>\n" \
            + "        <id>1</id>\n" \
            + "    </pack>\n" \
            + "    <pack>\n" \
            + "        <id>2</id>\n" \
            + "    </pack>\n" \
            + "</contaminant>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        contaminant_dict = ET.XML(xml_example, parser)

        Contaminant.update(category, contaminant_dict)

        self.assertEqual(len(mock_pack_update.mock_calls), 2)
        self.assertEqual(len(mock_suggestion_update.mock_calls), 3)
        self.assertEqual(len(mock_reference_update.mock_calls), 4)

    @mock.patch('contaminer.models.contabase.Reference.update')
    @mock.patch('contaminer.models.contabase.Suggestion.update')
    @mock.patch('contaminer.models.contabase.Pack.update')
    def test_update_creates_good_contaminant(self,
            mock_pack_update, mock_suggestion_update,
            mock_reference_update):
        category = Category.objects.all()[0]
        xml_example = "" \
            + "<contaminant>\n" \
            + "    <uniprot_id>P61517</uniprot_id>\n" \
            + "    <short_name>CAN_ECOLI</short_name>\n" \
            + "    <long_name>Carbonic anhydrase</long_name>\n" \
            + "    <sequence>ABCDEFGHIJKLMNOPQRSTUVWXYZ</sequence>\n" \
            + "    <organism>Escherichia coli</organism>\n" \
            + "    <exact_model>true</exact_model>\n" \
            + "    <reference>\n" \
            + "        <id>3</id>\n" \
            + "    </reference>\n" \
            + "    <suggestion>\n" \
            + "        <id>2</id>\n" \
            + "    </suggestion>\n" \
            + "    <pack>\n" \
            + "        <id>1</id>\n" \
            + "    </pack>\n" \
            + "</contaminant>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        contaminant_dict = ET.XML(xml_example, parser)

        Contaminant.update(category, contaminant_dict)

        contaminant = Contaminant.objects.get(
                uniprot_id = 'P61517',
                )
        self.assertEqual(contaminant.category, category)
        self.assertEqual(contaminant.short_name, "CAN_ECOLI")
        self.assertEqual(contaminant.long_name, "Carbonic anhydrase")
        self.assertEqual(contaminant.sequence, "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        self.assertEqual(contaminant.organism, "Escherichia coli")

    def test_to_simple_dict_gives_correct_result(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        response_dict = contaminant.to_simple_dict()
        response_expected = {
                'uniprot_id': "P0ACJ8",
                'short_name': "CRP_ECOLI",
                'long_name': "cAMP-activated global transcriptional regulator",
                'sequence': "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                'organism': "Escherichia coli",
            }

        self.assertEqual(response_dict, response_expected)

    def test_to_detailed_dict_gives_correct_result(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        Pack.objects.create(
                contaminant = contaminant,
                number = 5,
                structure= '5-mer',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 5,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 1,
                identity = 100,
                nb_residues = 112,
                )
        Pack.objects.create(
                contaminant = contaminant,
                number = 6,
                structure= '6-mer',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 6,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 2,
                identity = 100,
                nb_residues = 71,
                )
        response_dict = contaminant.to_detailed_dict()
        response_expected = {
                'uniprot_id': 'P0ACJ8',
                'short_name': 'CRP_ECOLI',
                'long_name': 'cAMP-activated global transcriptional regulator',
                'sequence': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'organism': 'Escherichia coli',
                'packs': [
                    {
                        'number': 5,
                        'structure': '5-mer',
                        'models': [
                            {
                                'template': '3RYP',
                                'chain': 'A',
                                'domain': 1,
                                'identity': 100,
                                'residues': 112,
                            },
                        ]
                    }, {
                        'number': 6,
                        'structure': '6-mer',
                        'models': [
                            {
                                'template': '3RYP',
                                'chain': 'A',
                                'domain': 2,
                                'identity': 100,
                                'residues': 71,
                            },
                        ]
                    }
                ]
            }

        self.assertEqual(response_dict, response_expected)

    def test_to_detailed_dict_gives_suggestion_reference(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        Pack.objects.create(
                contaminant = contaminant,
                number = 5,
                structure= '5-mer',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 5,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 1,
                identity = 100,
                nb_residues = 112,
                )
        Reference.objects.create(
                pubmed_id = 123456789,
                contaminant = contaminant
                )
        Reference.objects.create(
                pubmed_id = 987654321,
                contaminant = contaminant
                )
        Suggestion.objects.create(
                name = "Jean Dupont",
                contaminant = contaminant,
                )
        Suggestion.objects.create(
                name = "Jean Dupond",
                contaminant = contaminant,
                )
        response_dict = contaminant.to_detailed_dict()
        response_expected = {
                'uniprot_id': 'P0ACJ8',
                'short_name': 'CRP_ECOLI',
                'long_name': 'cAMP-activated global transcriptional regulator',
                'sequence': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                'organism': 'Escherichia coli',
                'packs': [
                    {
                        'number': 5,
                        'structure': '5-mer',
                        'models': [
                            {
                                'template': '3RYP',
                                'chain': 'A',
                                'domain': 1,
                                'identity': 100,
                                'residues': 112,
                            },
                        ]
                    }
                ],
                'references': [
                    {
                        'pubmed_id': 123456789
                    },
                    {
                        'pubmed_id': 987654321
                    },
                ],
                'suggestions': [
                    {
                        'name': 'Jean Dupont'
                    },
                    {
                        'name': 'Jean Dupond'
                    },
                ],
            }

        self.assertItemsEqual(response_dict, response_expected)


class PackTestCase(TestCase):
    """
        Test the Pack model
    """
    def setUp(self):
        contabase = ContaBase.objects.create()
        category = Category.objects.create(
                number = 1,
                name="Protein in E.Coli",
                contabase = contabase,
                )
        contaminant = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        self.pack = Pack.objects.create(
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

    def test_Pack_can_save_if_already_exist(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        self.pack.structure = "3-mer"
        try:
            self.pack.save()
        except ValidationError:
            self.fail("Cannot save an existing pack")

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

    @mock.patch('contaminer.models.contabase.Model.update')
    def test_update_updates_good_parameters_model(self,
            mock_model_update):
        contaminant = Contaminant.objects.all()[0]
        xml_example = "" \
            + "<pack>\n" \
            + "    <quat_structure>8-mer</quat_structure>\n" \
            + "    <model>\n" \
            + "        <id>1</id>\n" \
            + "    </model>\n" \
            + "</pack>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        pack_dict = ET.XML(xml_example, parser)

        Pack.update(contaminant, pack_dict)

        pack = Pack.objects.get(
                structure = "8-mer",
                )

        _, args, _ = mock_model_update.mock_calls[0]
        self.assertEqual(pack, args[0])
        model_dict = ET.Element('model')
        model_id = ET.SubElement(model_dict, 'id')
        model_id.text = '1'
        self.assertEqual(ET.tostring(model_dict), ET.tostring(args[1]))

    @mock.patch('contaminer.models.contabase.Model.update')
    def test_update_updates_good_number_model(self,
            mock_model_update):
        contaminant = Contaminant.objects.all()[0]
        xml_example = "" \
            + "<pack>\n" \
            + "    <quat_structure>2-mer</quat_structure>\n" \
            + "    <model>\n" \
            + "        <id>1</id>\n" \
            + "    </model>\n" \
            + "    <model>\n" \
            + "        <id>2</id>\n" \
            + "    </model>\n" \
            + "</pack>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        pack_dict = ET.XML(xml_example, parser)

        Pack.update(contaminant, pack_dict)

        self.assertEqual(len(mock_model_update.mock_calls), 2)

    @mock.patch('contaminer.models.contabase.Model.update')
    def test_update_creates_good_Pack(self,
            mock_model_update):
        contaminant = Contaminant.objects.all()[0]
        xml_example = "" \
            + "<pack>\n" \
            + "    <quat_structure>16-mer</quat_structure>\n" \
            + "    <model>\n" \
            + "        <id>1</id>\n" \
            + "    </model>\n" \
            + "    <model>\n" \
            + "        <id>2</id>\n" \
            + "    </model>\n" \
            + "</pack>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        pack_dict = ET.XML(xml_example, parser)

        Pack.update(contaminant, pack_dict)

        pack = Pack.objects.get(
                structure = '16-mer',
                )
        self.assertEqual(pack.contaminant, contaminant)
        self.assertEqual(pack.structure, "16-mer")

    @mock.patch('contaminer.models.contabase.Model.update')
    def test_update_creates_incremental_pack_number(self, mock_model_update):
        category = Category.objects.get(
                name="Protein in E.Coli",
                )
        Contaminant.objects.create(
                uniprot_id = "P0A8N5",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0A8N5',
                )
        xml1 = "" \
            + "<pack>\n" \
            + "    <quat_structure>1-mer</quat_structure>\n" \
            + "    <model>\n" \
            + "        <id>1</id>\n" \
            + "    </model>\n" \
            + "</pack>\n"
        xml2 = "" \
            + "<pack>\n" \
            + "    <quat_structure>2-mer</quat_structure>\n" \
            + "    <model>\n" \
            + "        <id>1</id>\n" \
            + "    </model>\n" \
            + "</pack>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        pack1_dict = ET.XML(xml1, parser)
        pack2_dict = ET.XML(xml2, parser)

        Pack.update(contaminant, pack1_dict)
        Pack.update(contaminant, pack2_dict)

        pack1 = Pack.objects.get(
                contaminant = contaminant,
                structure = "1-mer",
                )
        pack2 = Pack.objects.get(
                contaminant = contaminant,
                structure = "2-mer",
                )
        self.assertEqual(pack1.number, 1)
        self.assertEqual(pack2.number, 2)

    def test_to_dict_gives_correct_result(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        Pack.objects.create(
                contaminant = contaminant,
                number = 5,
                structure= '5-mer',
                )
        pack = Pack.objects.get(
                contaminant = contaminant,
                number = 5,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 1,
                identity = 100,
                nb_residues = 112,
                )
        Model.objects.create(
                pack = pack,
                pdb_code = '3RYP',
                chain = 'A',
                domain = 2,
                identity = 100,
                nb_residues = 71,
                )
        response_dict = pack.to_dict()
        response_expected = {
                'number': 5,
                'structure': '5-mer',
                'models': [
                    {
                        'template': '3RYP',
                        'chain': 'A',
                        'domain': 1,
                        'identity': 100,
                        'residues': 112,
                    }, {
                        'template': '3RYP',
                        'chain': 'A',
                        'domain': 2,
                        'identity': 100,
                        'residues': 71,
                    }
                ]
            }

        self.assertEqual(response_dict, response_expected)


class ModelTestCase(TestCase):
    """
        Test the Model model
    """
    def setUp(self):
        self.contabase = ContaBase.objects.create()
        self.category = Category.objects.create(
                number = 1,
                name="Protein in E.Coli",
                contabase = self.contabase,
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
                number = 1,
                structure = "2-mer",
                )
        self.model = Model.objects.create(
                pdb_code = '1o3t',
                chain = 'B',
                domain = 1,
                nb_residues = 20,
                identity = 100,
                pack = self.pack,
                )

        self.contabase.refresh_from_db()
        self.category.refresh_from_db()
        self.contaminant.refresh_from_db()
        self.pack.refresh_from_db()
        self.model.refresh_from_db()

    def test_Model_is_well_displayed(self):
        self.assertEqual(str(self.model), 'P0ACJ8 - CRP_ECOLI - 1 (2-mer) - 1O3T')

    def test_Model_identity_is_valid_percentage(self):
        with self.assertRaises(ValidationError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 20,
                    identity = 101,
                    pack = self.pack,
                    )
        with self.assertRaises(ValidationError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 20,
                    identity = -1,
                    pack = self.pack,
                    )

    def test_Model_identity_cannot_be_none(self):
        with self.assertRaises(IntegrityError):
            Model.objects.create(
                    pdb_code = '1o3t',
                    chain = 'B',
                    domain = 1,
                    nb_residues = 20,
                    pack = self.pack,
                    )

    def test_update_creates_good_model(self):
        xml_example = "" \
            + "<model>\n" \
            + "    <template>3qy1</template>\n" \
            + "    <chain>B</chain>\n" \
            + "    <domain>1</domain>\n" \
            + "    <n_res>10</n_res>\n" \
            + "    <identity>1.000</identity>\n" \
            + "</model>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        model_dict = ET.XML(xml_example, parser)

        Model.update(self.pack, model_dict)

        model = Model.objects.get(pdb_code = "3QY1")
        self.assertEqual(model.pack, self.pack)
        self.assertEqual(model.pdb_code, "3QY1")
        self.assertEqual(model.chain, "B")
        self.assertEqual(model.domain, 1)
        self.assertEqual(model.identity, 100)

    def test_update_creates_good_model_with_identity_float(self):
        xml_example = "" \
            + "<model>\n" \
            + "    <template>3qy1</template>\n" \
            + "    <chain>B</chain>\n" \
            + "    <domain>1</domain>\n" \
            + "    <n_res>10</n_res>\n" \
            + "    <identity>0.887</identity>\n" \
            + "</model>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        model_dict = ET.XML(xml_example, parser)

        Model.update(self.pack, model_dict)

        model = Model.objects.get(pdb_code = "3QY1")
        self.assertEqual(model.pack, self.pack)
        self.assertEqual(model.pdb_code, "3QY1")
        self.assertEqual(model.chain, "B")
        self.assertEqual(model.domain, 1)
        self.assertEqual(model.identity, 89)

    def test_to_dict_gives_correct_result(self):
        response_dict = self.model.to_dict()
        response_expected = {
                'template': '1O3T',
                'chain': 'B',
                'domain': 1,
                'identity': 100,
                'residues': 20,
            }

        self.assertEqual(response_dict, response_expected)

    def test_identity_gives_good_result(self):
        Model.objects.create(
                pdb_code = '3qy1',
                chain = 'A',
                domain = 1,
                nb_residues = 2,
                identity = 20,
                pack = self.pack
                )
        self.assertAlmostEqual(self.pack.identity, float(100*20+20*2)/(22))

    def test_coverage_gives_good_result_on_monomer(self):
        pack = Pack.objects.create(
                contaminant = self.contaminant,
                number = 2,
                structure='1-mer',
                )
        Model.objects.create(
                pdb_code = '3qy1',
                chain = 'A',
                domain = 1,
                nb_residues = 20,
                identity = 20,
                pack = pack
                )
        Model.objects.create(
                pdb_code = '4qy1',
                chain = 'A',
                domain = 1,
                nb_residues = 2,
                identity = 20,
                pack = pack
                )
        self.assertAlmostEqual(pack.coverage, float(22)/26*100)

    def test_coverage_gives_good_result_on_domains(self):
        pack = Pack.objects.create(
                contaminant = self.contaminant,
                number = 2,
                structure='domains',
                )
        Model.objects.create(
                pdb_code = '3qy1',
                chain = 'A',
                domain = 1,
                nb_residues = 20,
                identity = 20,
                pack = pack
                )
        Model.objects.create(
                pdb_code = '4qy1',
                chain = 'A',
                domain = 1,
                nb_residues = 2,
                identity = 20,
                pack = pack
                )
        self.assertAlmostEqual(pack.coverage, float(22)/26*100)

    def test_coverage_gives_good_result_on_multimer(self):
        pack = Pack.objects.create(
                contaminant = self.contaminant,
                number = 3,
                structure='6-mer',
                )
        Model.objects.create(
                pdb_code = '3qy1',
                chain = 'ABCD',
                domain = 1,
                nb_residues = 120,
                identity = 20,
                pack = pack
                )
        self.assertAlmostEqual(pack.coverage, float(20)/26*100)


class ReferenceTestCase(TestCase):
    """
        Test the Reference model
    """
    def setUp(self):
        ContaBase.objects.create()
        contabase = ContaBase.objects.all()[0]
        Category.objects.create(
                contabase = contabase,
                number = 1,
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


    def test_update_creates_good_reference(self):
        contaminant = Contaminant.objects.all()[0]
        xml_example = "" \
            + "<reference>\n" \
            + "    <pubmed_id>11111111</pubmed_id>\n" \
            + "</reference>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        reference_dict = ET.XML(xml_example, parser)

        Reference.update(contaminant, reference_dict)

        reference = Reference.objects.all()[0]
        self.assertEqual(reference.contaminant, contaminant)
        self.assertEqual(reference.pubmed_id, 11111111)

    def test_to_dict_gives_correct_result(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        Reference.objects.create(
                contaminant = contaminant,
                pubmed_id = 123456789,
                )

        reference = Reference.objects.all()[0]
        response_dict = reference.to_dict()
        response_expected = {
                'pubmed_id': 123456789,
            }

        self.assertEqual(response_dict, response_expected)


class SuggestionTestCase(TestCase):
    """
        Test the Suggestion model
    """
    def setUp(self):
        ContaBase.objects.create()
        contabase = ContaBase.objects.all()[0]
        Category.objects.create(
                contabase = contabase,
                number = 1,
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

    def test_update_creates_good_Suggestion(self):
        contaminant = Contaminant.objects.all()[0]
        xml_example = "" \
            + "<suggestion>\n" \
            + "    <name>Mohamed Bin Abdulaziz</name>\n" \
            + "</suggestion>\n"
        parser = ET.XMLParser(remove_blank_text = True)
        suggestion_dict = ET.XML(xml_example, parser)

        Suggestion.update(contaminant, suggestion_dict)

        suggestion = Suggestion.objects.all()[0]
        self.assertEqual(suggestion.contaminant, contaminant)
        self.assertEqual(suggestion.name, "Mohamed Bin Abdulaziz")

    def test_to_dict_gives_correct_result(self):
        contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                )
        Suggestion.objects.create(
                contaminant = contaminant,
                name = 'Mario Luigi',
                )

        suggestion = Suggestion.objects.all()[0]
        response_dict = suggestion.to_dict()
        response_expected = {
                'name': "Mario Luigi",
            }

        self.assertEqual(response_dict, response_expected)


class JobTestCase(TestCase):
    """
        Test the Job model
    """
    def setUp(self):
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
        self.pack1 = Pack.objects.create(
            contaminant = self.contaminant,
            number = 1,
            structure= '1-mer',
            )
        self.pack2 = Pack.objects.create(
            contaminant = self.contaminant,
            number = 2,
            structure= '1-mer',
            )
        self.model1 = Model.objects.create(
            pdb_code="ABCD",
            chain="A",
            domain=1,
            nb_residues=26,
            identity=100,
            pack=self.pack1,
            )
        self.model2 = Model.objects.create(
            pdb_code="ABCD",
            chain="A",
            domain=1,
            nb_residues=26,
            identity=100,
            pack=self.pack2,
            )
        self.job = Job.create(
            name = "test",
            email = "me@example.com",
            )

    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_Job_is_well_displayed(self, mock__):
        id = self.job.id
        self.assertEqual(str(self.job), str(id) + ' (me@example.com) New')

    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_Job_does_not_connect_to_cluster(self, mock_update):
        # Avoid the connection when displaying for performance purpose
        s = str(self.job)
        self.assertFalse(mock_update.called)

    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_status_gives_good_result(self, mock__):
        self.assertEqual(self.job.get_status(), "New")
        self.job.status_submitted = True
        self.assertEqual(self.job.get_status(), "Submitted")
        self.job.status_running = True
        self.assertEqual(self.job.get_status(), "Running")
        self.job.status_complete = True
        self.assertEqual(self.job.get_status(), "Complete")
        self.job.status_error = True
        self.assertEqual(self.job.get_status(), "Error")

    def test_create_Job_saves_in_DB(self):
        Job.objects.create(
                name = "new_job",
                email = "me@example.com,",
                )
        try:
            job = Job.objects.get(name = "new_job")
        except ObjectDoesNotExist:
            self.fail("Job has not been saved in DB")

    def test_create_Job_returns_job(self):
        job = Job.create(
            name = "test",
            email = "me@example.com,",
            )
        self.assertTrue(job is not None)

    def test_custom_create_Job_saves_in_DB(self):
        Job.create(
                name = "new_job2",
                email = "me@example.com,",
                )
        try:
            job = Job.objects.get(name = "new_job2")
        except ObjectDoesNotExist:
            self.fail("Job has not been saved in DB")

    def test_custom_create_Job_allows_empty_email(self):
        try:
            Job.create(
                    name = "test",
                    )
        except ValidationError:
            self.fail("Empty email address should not raise an error.")

    def test_to_detailed_dict_gives_correct_result(self):
        task1 = Task.objects.create(
            job = self.job,
            pack = self.pack1,
            space_group = "P-1-2-1",
            percent = 50,
            q_factor = 0.60,
            status_running = False,
            status_complete = False,
            )
        task2 = Task.objects.create(
            job = self.job,
            pack = self.pack2,
            space_group = "P-1-2-2",
            percent = 40,
            q_factor = 0.70,
            status_running = False,
            status_complete = True,
            )
        task3 = Task.objects.create(
            job = self.job,
            pack = self.pack2,
            space_group = "P-2-2-2",
            percent = 40,
            q_factor = 0.70,
            status_running = True,
            status_complete = False,
            )

        response_dict = self.job.to_detailed_dict()
        self.maxDiff = None
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'pack_nb': 1,
                    'space_group': "P-1-2-1",
                    'status': 'New',
                    'files_available': "False",
                },
                {
                    'uniprot_id': "P0ACJ8",
                    'pack_nb': 2,
                    'space_group': "P-1-2-2",
                    'status': 'Complete',
                    'percent': 40,
                    'q_factor': 0.70,
                    'files_available': "False",
                },
                {
                    'uniprot_id': "P0ACJ8",
                    'pack_nb': 2,
                    'space_group': "P-2-2-2",
                    'status': 'Running',
                    'files_available': "False",
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)

    def test_to_simple_dict_gives_running_tasks_new(self):
        task1 = Task.objects.create(
            job=self.job,
            pack=self.pack1,
            space_group="P-1-2-1",
            percent=50,
            q_factor=0.60,
            status_running=True,
            status_complete=False,
            )
        task2 = Task.objects.create(
            job=self.job,
            pack=self.pack2,
            space_group="P-1-2-1",
            percent=40,
            q_factor=0.70,
            status_running=False,
            status_complete=True,
            )
        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Running',
                    'pack_number': 2,
                    'space_group': "P-1-2-1",
                    'percent': 40,
                    'q_factor': 0.70,
                    'files_available': "False",
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)

    def test_to_simple_dict_gives_running_score_tasks_new_complete(self):
        Task.objects.create(
            job = self.job,
            pack = self.pack1,
            space_group = "P-1-2-1",
            status_running = True,
            ).save()
        Task.objects.create(
            job=self.job,
            pack=self.pack2,
            space_group="P-1-2-1",
            percent=40,
            q_factor=0.53,
            status_running=False,
            status_complete=True,
            ).save()

        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Running',
                    'percent': 40,
                    'q_factor': 0.53,
                    'pack_number': 2,
                    'space_group': "P-1-2-1",
                    'files_available': "False",
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)

    def test_to_simple_dict_gives_running_if_one_new(self):
        Task.objects.create(
            job = self.job,
            pack = self.pack1,
            space_group = "P-1-2-1",
            status_running = False,
            status_complete = False,
            ).save()

        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Running',
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)
        
    def test_to_simple_dict_gives_running_tasks_new_error(self):
        Task.objects.create(
            job = self.job,
            pack = self.pack1,
            space_group = "P-1-2-1",
            percent = 50,
            q_factor = 0.60,
            ).save()
        Task.objects.create(
            job = self.job,
            pack = self.pack2,
            space_group = "P-1-2-1",
            percent = 40,
            q_factor = 0.53,
            status_error = True,
            ).save()

        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Running',
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)

    def test_to_simple_dict_gives_complete_scores_tasks_complete(self):
        Task.objects.create(
            job = self.job,
            pack = self.pack1,
            space_group = "P-1-2-1",
            percent = 50,
            q_factor = 0.60,
            status_complete = True,
            ).save()
        Task.objects.create(
            job = self.job,
            pack = self.pack2,
            space_group = "P-1-2-1",
            percent = 40,
            q_factor = 0.70,
            status_complete = True,
            ).save()

        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Complete',
                    'percent': 50,
                    'q_factor': 0.60,
                    'pack_number': 1,
                    'space_group': "P-1-2-1",
                    'files_available': "False",
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)

    def test_to_simple_dict_gives_complete_scores_tasks_complete_error(self):
        Task.objects.create(
            job=self.job,
            pack=self.pack1,
            space_group="P-1-2-1",
            percent=50,
            q_factor=0.60,
            status_error=True,
            ).save()
        Task.objects.create(
            job=self.job,
            pack=self.pack2,
            space_group="P-1-2-1",
            percent=40,
            q_factor=0.70,
            status_complete = True,
            ).save()

        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Complete',
                    'percent': 40,
                    'q_factor': 0.70,
                    'pack_number': 2,
                    'space_group': "P-1-2-1",
                    'files_available': "False",
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)

    def test_to_simple_dict_gives_error_tasks_error(self):
        Task.objects.create(
            job = self.job,
            pack = self.pack1,
            space_group = "P-1-2-1",
            percent = 50,
            q_factor = 0.60,
            status_error = True,
            ).save()
        Task.objects.create(
            job = self.job,
            pack = self.pack2,
            space_group = "P-1-2-1",
            percent = 40,
            q_factor = 0.70,
            status_error = True,
            ).save()

        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Error',
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)

    @mock.patch('contaminer.models.contaminer.os.path.exists')
    def test_to_simple_dict_gives_available_files(self, mock_exists):
        task1 = Task.objects.create(
            job=self.job,
            pack=self.pack1,
            space_group="P-1-2-1",
            percent=50,
            q_factor=0.60,
            r_free=0.2,
            status_complete=True,
            )

        mock_exists.return_value = True
        response_dict = self.job.to_simple_dict()
        response_expected = {
            'id': self.job.id,
            'results': [
                {
                    'uniprot_id': "P0ACJ8",
                    'status': 'Complete',
                    'percent': 50,
                    'q_factor': 0.60,
                    'r_free': 0.2,
                    'pack_number': 1,
                    'space_group': "P-1-2-1",
                    'files_available': "True",
                },
            ]
        }
        self.assertEqual(response_dict, response_expected)
        self.assertTrue(
            "/media/web_task_" + str(self.job.id) + "/P0ACJ8_1_P-1-2-1" \
            in mock_exists.call_args[0][0])

    def test_get_filename_gives_good_output(self):
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        self.assertEqual(
                job.get_filename(suffix = "txt"),
                "web_task_" + str(job.id) + ".txt")

    def test_get_filename_gives_mtz_default(self):
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        self.assertEqual(
                job.get_filename(),
                "web_task_" + str(job.id))

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.os.remove')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_submit_send_input_file(self, mock_sshchannel, mock_sftpchannel,
            mock_remove, mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_client.exec_command.return_value = ("", "")
        mock_sftpchannel.return_value = mock_client
        mock_sshchannel.return_value = mock_client
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        job.submit("/local/dir/file.mtz", "cont1\ncont2\n")
        mock_client.send_file.assert_called_with(
            "/local/dir/file.mtz",
            "/remote/dir")

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.os.remove')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_submit_write_contaminants_list(self, mock_sshchannel,
            mock_sftpchannel, mock_remove, mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_client.exec_command.return_value = ("", "")
        mock_sftpchannel.return_value = mock_client
        mock_sshchannel.return_value = mock_client
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        job.submit("/local/dir/file.mtz", "cont1\ncont2\n")
        mock_client.write_file("/remote/dir/web_task_" + str(job.id) + ".txt",
            "cont1\ncont2\n")

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.os.remove')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_submit_runs_contaminer(self, mock_sshchannel, mock_sftpchannel,
            mock_remove, mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_client.exec_command.return_value = ("", "")
        mock_sftpchannel.return_value = mock_client
        mock_sshchannel.return_value = mock_client
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        job.submit("/local/dir/file.mtz", "cont1\ncont2\n")
        mock_client.exec_command_in_shell.assert_called_with(
            'cd "/remote/dir" && /remote/CM/contaminer solve ' \
            + '"web_task_' + str(job.id) + '.mtz" ' \
            + '"web_task_' + str(job.id) + '.txt"')

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.os.remove')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_submit_remove_local_file(self, mock_sshchannel, mock_sftpchannel,
            mock_remove, mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_client.exec_command.return_value = ("", "")
        mock_sftpchannel.return_value = mock_client
        mock_sshchannel.return_value = mock_client
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        job.submit("/local/dir/file.mtz", "cont1\ncont2\n")
        mock_remove.assert_called_with("/local/dir/file.mtz")

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.os.remove')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_submit_change_status_to_submitted(self, mock_sshchannel,
            mock_sftpchannel, mock_remove, mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_client.exec_command.return_value = ("", "")
        mock_sftpchannel.return_value = mock_client
        mock_sshchannel.return_value = mock_client
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        job.submit("/local/dir/file.mtz", "cont1\ncont2\n")
        self.assertEqual(job.status_submitted, True)

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_update_status_call_good_command(self, mock_sshchannel,
            mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_client.exec_command.return_value = ("submitted", "")
        mock_sshchannel.return_value = mock_client
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")
        job.update_status()
        mock_client.exec_command_in_shell.assert_called_with(
                '/remote/CM/contaminer job_status /remote/dir/web_task_' \
                        + str(job.id))

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_update_status_change_status(self, mock_sshchannel,
            mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_sshchannel.return_value = mock_client
        job = Job()
        job.create(
                name = "New job 3",
                email = "me@example.com,",
                )
        job = Job.objects.get(name = "New job 3")

        mock_client.exec_command_in_shell.return_value = "Job does not exist\n"
        job.update_status()
        self.assertEqual(job.status_submitted, False)
        self.assertEqual(job.get_status(), "New")

        mock_client.exec_command_in_shell.return_value = "Job is submitted\n"
        job.update_status()
        self.assertEqual(job.status_submitted, True)
        self.assertEqual(job.get_status(), "Submitted")

        mock_client.exec_command_in_shell.return_value = "Job is running\n"
        job.update_status()
        self.assertEqual(job.status_running, True)
        self.assertEqual(job.get_status(), "Running")

        mock_client.exec_command_in_shell.return_value = "Job is complete\n"
        job.update_status()
        self.assertEqual(job.status_complete, True)
        self.assertEqual(job.get_status(), "Complete")

        mock_client.exec_command_in_shell.return_value = "Job encountered an error\n"
        job.update_status()
        self.assertEqual(job.status_error, True)
        self.assertEqual(job.get_status(), "Error")

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_update_status_raise_exception_on_stderr(self, mock_sshchannel,
            mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_config.ssh_contaminer_location = "/remote/CM"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock(side_effect = RuntimeError())
        property_mock = mock.PropertyMock(side_effect = RuntimeError)
        mock_client.exec_command_in_shell = property_mock
        mock_sshchannel.return_value = mock_client
        job = Job.create(
                name = "test",
                email = "me@example.com,",
                )
        with self.assertRaises(RuntimeError):
            job.update_status()

    @mock.patch('contaminer.models.contaminer.Job.update')
    def test_update_all_updates_job(self, mock_update):
        job = Job.create(
                name = "test",
                email="me@example.com",
                )
        job.status_submitted = True
        job.save()
        Job.update_all()
        self.assertTrue(mock_update.called)

    @mock.patch('contaminer.models.contaminer.Job.update')
    def test_update_all_not_update_archived(self, mock_update):
        job = Job.create(
                name = "test",
                email="me@example.com",
                )
        job.status_submitted = True
        job.status_archived = True
        job.save()
        Job.update_all()
        self.assertFalse(mock_update.called)

    @mock.patch('contaminer.models.contaminer.Job.update')
    def test_update_all_not_update_not_submitted(self, mock_update):
        job = Job.create(
                name = "test",
                email="me@example.com",
                )
        job.status_submitted = False
        job.save()
        Job.update_all()
        self.assertFalse(mock_update.called)

    @mock.patch('contaminer.models.contaminer.Job.update')
    @mock.patch('contaminer.models.contaminer.mail_admins')
    def test_update_send_mail_if_exception(self, mock_mail, mock_update):
        mock_update.side_effect = RuntimeError
        job = Job.create(
                name = "test",
                email="me@example.com",
                )
        job.status_submitted = True
        job.save()
        Job.update_all()
        self.assertTrue(mock_mail.called)

    def make_job_complete(self):
        self.job.status_complete = True
        self.job.save()

    @mock.patch('contaminer.models.contaminer.Job.update_tasks')
    @mock.patch('contaminer.models.contaminer.Job.send_complete_mail')
    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_update_send_mail_when_complete(self, mock_status, mock_mail, _):
        mock_status.side_effect = self.make_job_complete
        self.job = Job.create(
                name = "test",
                email = "me@example.com,",
                )
        self.job.update()
        self.assertTrue(mock_mail.called)

    @mock.patch('contaminer.models.contaminer.Job.update_tasks')
    @mock.patch('contaminer.models.contaminer.Job.send_complete_mail')
    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_update_send_no_mail_when_archived(self, _, mock_mail, __):
        job = Job.create(
                name = "test",
                email = "me@example.com,",
                )
        job.status_archived = True
        job.save()
        job.update()
        self.assertFalse(mock_mail.called)

    @mock.patch('contaminer.models.contaminer.Job.update_tasks')
    @mock.patch('contaminer.models.contaminer.Job.send_complete_mail')
    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_update_send_no_mail_when_not_complete(self, _, mock_mail, __):
        job = Job.create(
                name = "test",
                email = "me@example.com,",
                )
        job.update()
        self.assertFalse(mock_mail.called)

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    def test_update_tasks_read_good_file(self, mock_ssh, mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_CMConfig.return_value = mock_config
        mock_channel = mock.MagicMock()
        mock_channel.read_file.return_value = ""
        mock_ssh.return_value = mock_channel
        job = Job()
        job.create(
                name = "test",
                email = "me@example.com",
                )
        job.status_submitted = True
        job.save()
        job.update_tasks()
        expect_call = "/remote/dir/web_task_" + str(job.id) + "/results.txt"
        mock_channel.read_file.assert_called_once_with(expect_call)

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    @mock.patch('contaminer.models.contaminer.Task')
    def test_update_tasks_create_good_task(self, mock_task, mock_ssh,
            mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_CMConfig.return_value = mock_config
        mock_channel = mock.MagicMock()
        mock_channel.read_file.return_value = "line1"
        mock_ssh.return_value = mock_channel
        job = Job()
        job.create(
                name = "test",
                email = "me@example.com",
                )
        job.status_submitted = True
        job.save()
        job.update_tasks()
        mock_task.update.assert_called_once_with(job, "line1")

    @mock.patch('contaminer.models.contaminer.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.SSHChannel')
    @mock.patch('contaminer.models.contaminer.Task')
    def test_update_tasks_create_enough_tasks(self, mock_task, mock_ssh,
            mock_CMConfig):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_CMConfig.return_value = mock_config
        mock_channel = mock.MagicMock()
        mock_channel.read_file.return_value = "line1\nline2"
        mock_ssh.return_value = mock_channel
        job = Job()
        job.create(
                name = "test",
                email = "me@example.com",
                )
        job.status_submitted = True
        job.save()
        job.update_tasks()
        self.assertEqual(mock_task.update.call_count, 2)

    def create_pack(self):
        job = Job.objects.create(
                name = "test",
                email = "me@example.com",
                )
        contabase = ContaBase.objects.create()
        category = Category.objects.create(
                contabase = contabase,
                number = 1,
                name = "Protein in E.Coli",
                )
        contaminant = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        pack = Pack.objects.create(
                contaminant = contaminant,
                number = 5,
                structure= '5-mer',
                )

        return (job, pack)

    def test_get_best_task_gives_empty_if_no_task(self):
        (job, pack) = self.create_pack()
        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, None)

    def test_get_best_task_gives_empty_if_error(self):
        (job, pack) = self.create_pack()
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                status_complete = True,
                status_error = True,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, None)

    def test_get_best_task_gives_empty_if_non_complete(self):
        (job, pack) = self.create_pack()
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                status_complete = False,
                status_error = False,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, None)

    def test_get_best_task_gives_empty_if_error_and_non_complete(self):
        (job, pack) = self.create_pack()
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                status_complete = False,
                status_error = True,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, None)

    def test_get_best_task_gives_non_error(self):
        (job, pack) = self.create_pack()
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = True,
                )
        task2 = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-21-2-2",
                percent = 0,
                q_factor = 0,
                status_complete = True,
                status_error = False,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, task2)

    def test_get_best_task_gives_complete(self):
        (job, pack) = self.create_pack()
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = False,
                status_error = False,
                )
        task2 = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-21-2-2",
                percent = 0,
                q_factor = 0,
                status_complete = True,
                status_error = False,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, task2)

    def test_get_best_task_gives_best_percent(self):
        (job, pack) = self.create_pack()
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )
        task2 = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-21-2-2",
                percent = 0,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, task)

    def test_get_best_task_gives_best_q_factor(self):
        (job, pack) = self.create_pack()
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 0.8,
                status_complete = True,
                status_error = False,
                )
        task2 = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-21-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, task2)

    def test_get_best_task_gives_best_coverage(self):
        (job, pack) = self.create_pack()
        pack2 = Pack.objects.create(
                contaminant = pack.contaminant,
                number = 6,
                structure = '1-mer',
                )
        Model.objects.create(
                pdb_code = 'TEST',
                chain = 'A',
                domain = '1',
                nb_residues = 20,
                identity = 100,
                pack = pack,
                )
        Model.objects.create(
                pdb_code = 'TEST2',
                chain = 'ABCD',
                domain = '1',
                nb_residues = 26,
                identity = 100,
                pack = pack2,
                )
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )
        task2 = Task.objects.create(
                job = job,
                pack = pack2,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, task2)

    def test_get_best_task_gives_best_identity(self):
        (job, pack) = self.create_pack()
        pack2 = Pack.objects.create(
                contaminant = pack.contaminant,
                number = 6,
                structure = '5-mer',
                )
        Model.objects.create(
                pdb_code = 'TEST',
                chain = 'A',
                domain = '1',
                nb_residues = 20,
                identity = 99,
                pack = pack,
                )
        Model.objects.create(
                pdb_code = 'TEST2',
                chain = 'ABCD',
                domain = '1',
                nb_residues = 20,
                identity = 100,
                pack = pack2,
                )
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )
        task2 = Task.objects.create(
                job = job,
                pack = pack2,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )

        best_task = job.get_best_task(pack.contaminant)
        self.assertEqual(best_task, task2)

    def test_get_best_task_works_on_obsolete_contabase(self):
        (job_obsolete, pack_obsolete) = self.create_pack()
        ContaBase.make_all_obsolete()
        (job_new, pack_new) = self.create_pack()

        Model.objects.create(
                pdb_code = 'TEST',
                chain = 'A',
                domain = '1',
                nb_residues = 20,
                identity = 99,
                pack = pack_obsolete,
                )
        task = Task.objects.create(
                job = job_obsolete,
                pack = pack_obsolete,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )
        Model.objects.create(
                pdb_code = 'TEST',
                chain = 'A',
                domain = '1',
                nb_residues = 20,
                identity = 99,
                pack = pack_new,
                )
        task = Task.objects.create(
                job = job_new,
                pack = pack_new,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )

        best_task = job_obsolete.get_best_task(pack_new.contaminant)
        self.assertTrue(best_task)

    def test_get_best_tasks_gives_empty_list_if_no_task(self):
        best_tasks = self.job.get_best_tasks()
        self.assertEqual(best_tasks, [])

    @mock.patch('contaminer.models.contaminer.Job.get_best_task')
    def test_get_best_tasks_gives_as_many_as_contaminants(self, mock_task):
        mock_task.return_value = None
        contaminant2 = Contaminant.objects.create(
                uniprot_id = "P0AA25",
                category = self.category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        pack2 = Pack.objects.create(
                contaminant = contaminant2,
                number = 5,
                structure= '5-mer',
                )
        task = Task.objects.create(
                job = self.job,
                pack = pack2,
                space_group = "P-2-2-2",
                percent = 100,
                q_factor = 1,
                status_complete = True,
                status_error = False,
                )
        best_tasks = self.job.get_best_tasks()
        self.assertEqual(len(best_tasks), 0)
        self.assertEqual(mock_task.call_count, 2)
        mock_task.assert_any_call(pack2.contaminant)
        mock_task.assert_any_call(contaminant2)

    @mock.patch('contaminer.models.contaminer.send_mail')
    def test_send_email_to_good_address(self, mock_send_mail):
        job = Job.create(
                name = "test",
                email = "me@example.com",
                )
        job.send_complete_mail()
        self.assertTrue(mock_send_mail.called)
        self.assertEqual(mock_send_mail.call_args[0][3], ['me@example.com'])

    @mock.patch('contaminer.models.contaminer.send_mail')
    def test_do_not_send_email_if_no_address(self, mock_send_mail):
        job = Job.create(
                name = "test",
                )
        job.send_complete_mail()
        self.assertFalse(mock_send_mail.called)


class TaskTestCase(TestCase):
    """Test the Task model"""
    def setUp(self):
        Job.objects.create(
                name = "test",
                email = "me@example.com",
                )
        self.job = Job.objects.get(name = "test")
        ContaBase.objects.create()
        self.contabase = ContaBase.objects.all()[0]
        Category.objects.create(
                contabase = self.contabase,
                number = 1,
                name = "Protein in E.Coli",
                )
        self.category = Category.objects.get(
                name = "Protein in E.Coli",
                )
        Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = self.category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        self.contaminant = Contaminant.objects.get(
                uniprot_id = 'P0ACJ8',
                category = self.category,
                )
        Pack.objects.create(
                contaminant = self.contaminant,
                number = 5,
                structure= '5-mer',
                )
        self.pack = Pack.objects.get(
                contaminant = self.contaminant,
                number = 5,
                )

    def test_task_from_name_gives_good_task(self):
        task = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                percent = 99,
                q_factor = 0.9,
                )
        self.assertEqual(
                Task.from_name(self.job, "P0ACJ8_5_P-2-2-2"),
                task)

    def test_task_from_name_works_with_underscore(self):
        custom_contaminant = Contaminant.objects.create(
            uniprot_id="c_5jk4",
            category=self.category,
            short_name="CUSTOM",
            long_name="",
            sequence="XXXX",
            organism="Custom")
        custom_pack = Pack.objects.create(
            contaminant=custom_contaminant,
            number=1,
            structure="1-mer")
        task = Task.objects.create(
            job=self.job,
            pack=custom_pack,
            space_group="P-1-1-1",
            percent=99,
            q_factor=0.9)
        self.assertEqual(
            Task.from_name(self.job, "c_5jk4_1_P-1-1-1"),
            task)

    def test_task_works_with_multiple_existing_tasks(self):
        task = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                percent = 99,
                q_factor = 0.9,
                )
        # != space_group
        Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-21",
                percent = 99,
                q_factor = 0.9,
                )
        # != pack_number
        pack = Pack.objects.create(
                contaminant=self.contaminant,
                number=4,
                structure='5-mer',
                )
        Task.objects.create(
                job = self.job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 99,
                q_factor = 0.9,
                )
        # != contaminant
        contaminant = Contaminant.objects.create(
                uniprot_id="P03303",
                category=self.category,
                short_name="short",
                long_name="long",
                sequence="ABCDEF",
                organism="yo",
                )
        pack = Pack.objects.create(
                contaminant=contaminant,
                number=5,
                structure='5-mer',
                )
        Task.objects.create(
                job = self.job,
                pack = pack,
                space_group = "P-2-2-2",
                percent = 99,
                q_factor = 0.9,
                )
        self.assertEqual(
                Task.from_name(self.job, "P0ACJ8_5_P-2-2-2"),
                task)

    def test_comp_gives_expected_result_normal_cases(self):
        task1 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                percent = 51,
                q_factor = 0.9,
                )
        task2 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-21-2-2",
                percent = 52,
                q_factor = 0.9,
                )
        task3 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-21-2",
                percent = 51,
                q_factor = 0.9,
                )
        task4 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-21",
                percent = 51,
                q_factor = 0.8,
                )
        self.assertFalse(task1.is_better_than(task2))
        self.assertTrue(task2.is_better_than(task1))
        self.assertFalse(task1.is_better_than(task3))
        self.assertTrue(task1.is_better_than(task4))

    def test_comp_gives_expected_result_edge_cases(self):
        task1 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                percent = None,
                q_factor = None,
                )
        task2 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-21-2-2",
                percent = 1,
                q_factor = 0,
                )
        task3 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-21-2",
                percent = 1,
                q_factor = None,
                )
        self.assertFalse(task1.is_better_than(task2))
        self.assertTrue(task2.is_better_than(task1))
        self.assertFalse(task1.is_better_than(task3))
        self.assertTrue(task2.is_better_than(task3))

    def test_get_status_gives_good_result(self):
        task = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                percent = 99,
                q_factor = 0.9,
                )
        self.assertEqual(task.get_status(), "New")
        task.status_complete = True
        self.assertEqual(task.get_status(), "Complete")
        task.status_error = True
        self.assertEqual(task.get_status(), "Error")

    @mock.patch('contaminer.models.contaminer.Job.update_status')
    def test_Task_is_well_displayed(self, mock__):
        task = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                percent = 99,
                q_factor = 0.9,
                )
        self.assertEqual(str(task), str(self.job.id) \
                + " (me@example.com) New / P0ACJ8 - CRP_ECOLI - 5 (5-mer)"\
                + " / P-2-2-2 / New")

    def test_Task_percent_is_valid_percentage(self):
        with self.assertRaises(ValidationError):
            task = Task.objects.create(
                    job = self.job,
                    pack = self.pack,
                    space_group = "P-2-2-2",
                    percent = 101,
                    q_factor = 0.9,
                    )
        with self.assertRaises(ValidationError):
            task = Task.objects.create(
                    job = self.job,
                    pack = self.pack,
                    space_group = "P-2-2-2",
                    percent = -1,
                    q_factor = 0.9,
                    )

    def test_Task_percent_qfactor_can_be_emtpy(self):
        task = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                 )

    def test_Task_get_final_filename_gives_good_result(self):
        task = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-2-2-2",
                percent = 99,
                q_factor = 0.9,
                )
        self.assertEqual(task.get_final_filename(),
                "web_task_" + str(self.job.id) + "/P0ACJ8_5_P-2-2-2")
        self.assertEqual(task.get_final_filename(suffix = "pdb"),
                "web_task_" + str(self.job.id) + "/P0ACJ8_5_P-2-2-2.pdb")
        self.assertEqual(task.get_final_filename(suffix = ".pdb"),
                "web_task_" + str(self.job.id) + "/P0ACJ8_5_P-2-2-2.pdb")

    def test_update_create_new_task(self):
        task = Task.update(self.job,
            "P0ACJ8,5,P-1-2-1,running,0.414,52,1h 26m  9s")
        self.assertTrue(task.id is not None)

    def test_update_use_existing_task(self):
        task1 = Task.objects.create(
                job = self.job,
                pack = self.pack,
                space_group = "P-1-2-1",
                )
        task1.save()
        task2 = Task.update(self.job,
            "P0ACJ8,5,P-1-2-1,running,0.414,52,1h 26m  9s")
        self.assertEqual(task1.id, task2.id)

    def test_update_raises_error_on_bad_line(self):
        with self.assertRaises(ValueError):
            task = Task.update(self.job, "Tata yoyo")
        with self.assertRaises(ValueError):
            task = Task.update(self.job, "1,2,3")

    def test_update_creates_good_task(self):
        task = Task.update(self.job,
            "P0ACJ8,5,P-1-1-1,completed,0.414,52,1h 26m  9s")
        self.assertEqual(task.job, self.job)
        self.assertEqual(task.pack, self.pack)
        self.assertEqual(task.space_group, "P-1-1-1")
        self.assertTrue(task.status_complete)
        self.assertFalse(task.status_running)
        self.assertFalse(task.status_error)
        self.assertEqual(task.percent, 52)
        self.assertEqual(task.q_factor, 0.414)
        self.assertEqual(task.exec_time, datetime.timedelta(seconds = 5169))

        task = Task.update(self.job,
            "P0ACJ8,5,P-1-1-2,completed,0,0,2h 26m  9s")
        self.assertEqual(task.job, self.job)
        self.assertEqual(task.pack, self.pack)
        self.assertEqual(task.space_group, "P-1-1-2")
        self.assertTrue(task.status_complete)
        self.assertFalse(task.status_running)
        self.assertFalse(task.status_error)
        self.assertEqual(task.percent, 0)
        self.assertEqual(task.q_factor, 0)
        self.assertEqual(task.exec_time, datetime.timedelta(seconds = 8769))

        task = Task.update(self.job,
            "P0ACJ8,5,P-1-2-1,running,0,0,0h  0m  0s")
        self.assertEqual(task.job, self.job)
        self.assertEqual(task.pack, self.pack)
        self.assertEqual(task.space_group, "P-1-2-1")
        self.assertFalse(task.status_complete)
        self.assertTrue(task.status_running)
        self.assertFalse(task.status_error)
        self.assertEqual(task.exec_time, datetime.timedelta(seconds = 0))

        task = Task.update(self.job,
            "P0ACJ8,5,P-1-2-2,new,0,0,0h  0m  0s")
        self.assertEqual(task.job, self.job)
        self.assertEqual(task.pack, self.pack)
        self.assertEqual(task.space_group, "P-1-2-2")
        self.assertFalse(task.status_complete)
        self.assertFalse(task.status_running)
        self.assertFalse(task.status_error)
        self.assertEqual(task.exec_time, datetime.timedelta(seconds = 0))

        task = Task.update(self.job,
            "P0ACJ8,5,P-2-1-1,error,0,0,1h  1m  1s")
        self.assertEqual(task.job, self.job)
        self.assertEqual(task.pack, self.pack)
        self.assertEqual(task.space_group, "P-2-1-1")
        self.assertTrue(task.status_error)
        self.assertEqual(task.exec_time, datetime.timedelta(seconds = 3661))

    def test_update_works_on_error(self):
        task = Task.update(self.job,
            "P0ACJ8,5,P-1-2-1,error,0,0,0h  0m  0s")
        self.assertEqual(task.job, self.job)
        self.assertEqual(task.pack, self.pack)
        self.assertEqual(task.space_group, "P-1-2-1")
        self.assertFalse(task.status_complete)
        self.assertFalse(task.status_running)
        self.assertTrue(task.status_error)
        self.assertEqual(task.percent, 0)
        self.assertEqual(task.q_factor, 0)

    def test_update_works_on_aborted(self):
        task = Task.update(self.job,
                           "P0ACJ8,5,P-1-2-1,aborted,0,0,0h  0m  0s")
        self.assertEqual(task.job, self.job)
        self.assertEqual(task.pack, self.pack)
        self.assertEqual(task.space_group, "P-1-2-1")
        self.assertTrue(task.status_complete)
        self.assertFalse(task.status_running)
        self.assertFalse(task.status_error)
        self.assertEqual(task.percent, 0)
        self.assertEqual(task.q_factor, 0)

    @mock.patch('contaminer.models.contaminer.PDBHandler.get_r_free')
    @mock.patch('contaminer.models.contaminer.Task.get_final_files')
    def test_update_gets_final_on_high_percentage(self, mock_get, mock_r_free):
        mock_r_free.return_value = 0.2
        task = Task.update(self.job,
            "P0ACJ8,5,P-1-2-1,completed,0.414,89,1h 26m  9s")
        self.assertFalse(mock_get.called)
        task = Task.update(self.job,
            "P0ACJ8,5,P-1-2-2,completed,0.414,91,1h 26m  9s")
        self.assertTrue(mock_get.called)

    @mock.patch('contaminer.models.contaminer.os.makedirs')
    @mock.patch('contaminer.ssh_tools.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.settings')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    def test_get_final_files_get_good_files_writes_MEDIA(self, mock_channel, mock_settings,
            mock_CMConfig, mock_makedirs):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_channel.return_value = mock_client

        mock_settings.MEDIA_ROOT = "/media"

        contabase = ContaBase.objects.create()
        category = Category.objects.create(
                contabase = contabase,
                number = 1,
                name = "Protein in E.Coli",
                )
        contaminant = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        pack = Pack.objects.create(
                contaminant = contaminant,
                number = 1,
                structure= '5-mer',
                )
        job = Job.create(
                name = "test",
                email = "me@example.com",
                )
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-1-2-1",
                percent = 50,
                q_factor = 0.60,
                status_complete = True,
                )
        task.save()

        task.get_final_files()

        mock_client.download_from_contaminer.assert_any_call(
                "web_task_" + str(job.id) \
                + "/P0ACJ8_1_P-1-2-1/results_solve/final.pdb",
                "/media/web_task_" + str(job.id) + "/P0ACJ8_1_P-1-2-1.pdb")
        mock_client.download_from_contaminer.assert_any_call(
                "web_task_" + str(job.id) \
                + "/P0ACJ8_1_P-1-2-1/results_solve/final.mtz",
                "/media/web_task_" + str(job.id) + "/P0ACJ8_1_P-1-2-1.mtz")

    @mock.patch('contaminer.models.contaminer.os.path.isdir')
    @mock.patch('contaminer.models.contaminer.os.makedirs')
    @mock.patch('contaminer.ssh_tools.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.settings')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    def test_get_final_files_error_on_dir_is_file(self, mock_channel,
            mock_settings, mock_CMConfig, mock_makedirs, mock_isdir):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_channel.return_value = mock_client

        mock_settings.MEDIA_ROOT = "/media"

        contabase = ContaBase.objects.create()
        category = Category.objects.create(
                contabase = contabase,
                number = 1,
                name = "Protein in E.Coli",
                )
        contaminant = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        pack = Pack.objects.create(
                contaminant = contaminant,
                number = 1,
                structure= '5-mer',
                )
        job = Job.create(
                name = "test",
                email = "me@example.com",
                )
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-1-2-1",
                percent = 50,
                q_factor = 0.60,
                status_complete = True,
                )
        task.save()

        mock_makedirs.side_effect = OSError(17, 'File exists', 'Foo')
        mock_isdir.return_value = False

        with self.assertRaises(OSError):
            task.get_final_files()

    @mock.patch('contaminer.models.contaminer.os.path.isdir')
    @mock.patch('contaminer.models.contaminer.os.makedirs')
    @mock.patch('contaminer.ssh_tools.apps.get_app_config')
    @mock.patch('contaminer.models.contaminer.settings')
    @mock.patch('contaminer.models.contaminer.SFTPChannel')
    def test_get_final_files_pass_on_existing_local_dir(self, mock_channel,
            mock_settings, mock_CMConfig, mock_makedirs, mock_isdir):
        mock_config = mock.MagicMock()
        mock_config.ssh_work_directory = "/remote/dir"
        mock_CMConfig.return_value = mock_config
        mock_client = mock.MagicMock()
        mock_channel.return_value = mock_client

        mock_settings.MEDIA_ROOT = "/media"

        contabase = ContaBase.objects.create()
        category = Category.objects.create(
                contabase = contabase,
                number = 1,
                name = "Protein in E.Coli",
                )
        contaminant = Contaminant.objects.create(
                uniprot_id = "P0ACJ8",
                category = category,
                short_name = "CRP_ECOLI",
                long_name = "cAMP-activated global transcriptional regulator",
                sequence = "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                organism = "Escherichia coli",
                )
        pack = Pack.objects.create(
                contaminant = contaminant,
                number = 1,
                structure= '5-mer',
                )
        job = Job.create(
                name = "test",
                email = "me@example.com",
                )
        task = Task.objects.create(
                job = job,
                pack = pack,
                space_group = "P-1-2-1",
                percent = 50,
                q_factor = 0.60,
                status_complete = True,
                )
        task.save()

        mock_makedirs.side_effect = OSError(17, 'File exists', 'Foo')
        mock_isdir.return_value = True

        try:
            task.get_final_files()
        except OSError:
            self.fail("OSError raised")

    def test_to_dict_gives_correct_result(self):
        job = Job.objects.create(
                name = "test",
                email = "me@example.com",
                )
        job.save()
        task = Task.objects.create(
                job = job,
                pack = self.pack,
                space_group = "P-1-2-1",
                percent = 40,
                q_factor = 0.53,
                )
        response_dict = task.to_dict()
        response_expected = {
                'uniprot_id': "P0ACJ8",
                'pack_nb': 5,
                'space_group': "P-1-2-1",
                'status': 'New',
                'files_available': "False",
            }
        self.assertEqual(response_dict, response_expected)

        task.status_complete = True
        response_dict = task.to_dict()
        response_expected = {
                'uniprot_id': "P0ACJ8",
                'pack_nb': 5,
                'space_group': "P-1-2-1",
                'status': 'Complete',
                'percent': 40,
                'q_factor': 0.53,
                'files_available': "False",
            }
        self.assertEqual(response_dict, response_expected)

        task.status_error = True
        response_dict = task.to_dict()
        response_expected = {
                'uniprot_id': "P0ACJ8",
                'pack_nb': 5,
                'space_group': "P-1-2-1",
                'status': 'Error',
                'files_available': "False",
            }
        self.assertEqual(response_dict, response_expected)
