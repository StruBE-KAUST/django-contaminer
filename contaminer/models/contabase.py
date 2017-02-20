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
    Models for ContaMiner application
    =================================

    This module contains the classes definition for the application named
    "ContaMiner".
    These models contains only the ContaBase (should be sync with the
    cluster) (not the ContaMiner jobs).
    See models/contaminer.py for the jobs related models.
"""

import os
import datetime
import paramiko
import logging
import re
import lxml.etree as ET

from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError

from .tools import UpperCaseCharField
from .tools import PercentageField
from ..ssh_tools import SSHChannel

class ContaBase(models.Model):
    """
        A version of the ContaBase

        When updated, the current ContaBase is marked as obsolete, and a new
        one is created with the new contaminants and packs.
        Having different ContaBase at the same time allows us to keep the old
        jobs in the database, while being able to update it for the new jobs.
    """
    id = models.IntegerField(unique = True, primary_key = True)
    obsolete = models.BooleanField(default = False)

    def __str__(self):
        """ Write id and (obsolete) if needed """
        obsolete_txt = "obsolete" if self.obsolete else "current"
        return str(self.id) + " - " + obsolete_txt

    @classmethod
    def get_current(cls):
        """ Return the only not obsolete contabase """
        log = logging.getLogger(__name__)
        log.debug("Enter")
        current_list = cls.objects.get(obsolete = False)
        log.debug("Exit")
        return current_list

    def make_obsolete(self):
        """ Mark self as obsolete """
        self.obsolete = True
        self.save()

    @classmethod
    def make_all_obsolete(cls):
        """ Mark all the contabases as obsolete """
        log = logging.getLogger(__name__)
        log.debug("Enter")
        all_objects = cls.objects.all()
        map(lambda x: x.make_obsolete(), all_objects)
        log.debug("Exit")

    @classmethod
    def update(cls):
        """ Update the ContaBase based on the data on the remote cluster """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        cls.make_all_obsolete()

        new_contabase = ContaBase()
        new_contabase.obsolete = False
        new_contabase.save()
        new_contabase = ContaBase.get_current()

        parser = ET.XMLParser(remove_blank_text = True)
        contabase = ET.XML(SSHChannel().get_contabase(), parser)

        for category in contabase.iter('category'):
            log.debug("Category found")
            Category.update(new_contabase, category)

        log.info("ContaBase updated")
        log.debug("Exit")

    def to_detailed_dict(self):
        """ Return a dictionary of the fields and Categories """
        response_data = {}

        categories = Category.objects.filter(contabase = self)
        categories_dict = [cat.to_detailed_dict() for cat in categories]
        response_data['categories'] = categories_dict

        return response_data


class Category(models.Model):
    """
        A category of contaminant

        selected_by_default is used to know if ContaMiner should test the
        contaminants in this category by default
    """
    contabase = models.ForeignKey(ContaBase)
    number = models.IntegerField() # Unique per contabase
    name = models.CharField(max_length = 60)
    selected_by_default = models.BooleanField(default = False)

    def __str__(self):
        """ Write name, selected by default, and (obsolete) if needed """
        obsolete_str = (" (obsolete)" if self.contabase.obsolete else "")
        return self.name + " - " + str(self.selected_by_default) + obsolete_str

    def clean(self, *args, **kwargs):
        """ Clean the fields before saving in the database """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        category = Category.objects.filter(
                contabase = self.contabase,
                number = self.number,
                )
        if len(category) != 0 or (len(category) == 1 and category[0].pk != self.pk):
            raise ValidationError("Category already registered in ContaBase")

        super(Category, self).clean(*args, **kwargs)
        log.debug("Exit")

    def save(self, *args, **kwargs):
        """ Save object in DB """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        self.full_clean()
        super(Category, self).save(*args, **kwargs)

        log.debug("Exit")

    @classmethod
    def update(cls, parent_contabase, category_dict):
        """ Create the category based on category_dict """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        number = int(category_dict.find('id').text)
        new_category = Category()
        new_category.contabase = parent_contabase
        new_category.number = number # Unique per contabase
        new_category.name = category_dict.find('name').text
        default = (category_dict.find('default').text in ['true', 'True'])
        new_category.selected_by_default = default
        new_category.save()

        new_category = Category.objects.get(
                contabase = parent_contabase,
                number = number,
                )

        for contaminant in category_dict.iter('contaminant'):
            log.debug("Contaminant found")
            Contaminant.update(new_category, contaminant)

        log.debug("Exit")

    def to_simple_dict(self):
        """ Return a dictionary of the fields """
        response_data = {}
        response_data['id'] = self.number
        response_data['name'] = self.name
        response_data['selected_by_default'] = self.selected_by_default

        return response_data

    def to_detailed_dict(self):
        """ Return a dictionary of the fields and contaminants """
        response_data = self.to_simple_dict()

        contaminants = Contaminant.objects.filter(category = self)
        contaminants_dict = [cont.to_detailed_dict() for cont in contaminants]
        response_data['contaminants'] = contaminants_dict

        return response_data


class Contaminant(models.Model):
    """
        A possible contaminant

        The contaminants in this table are prepared on the cluster, and can be
        used to test a file of diffraction data
    """
    uniprot_id = UpperCaseCharField(max_length = 10)
    category = models.ForeignKey(Category)
    short_name = UpperCaseCharField(max_length = 20)
    long_name = models.CharField(max_length = 100, null = True, blank = True)
    sequence = models.TextField()
    organism = models.CharField(max_length = 50, null = True, blank = True)

    def __str__(self):
        """ Write uniprot_id + short_name """
        return self.uniprot_id + ' - ' + self.short_name

    @classmethod
    def update(cls, parent_category, contaminant_dict):
        """ Create the contaminant based on contaminant_dict """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        uniprot_id = contaminant_dict.find('uniprot_id').text
        new_contaminant = Contaminant()
        new_contaminant.uniprot_id = uniprot_id
        new_contaminant.category = parent_category
        new_contaminant.short_name = contaminant_dict.find('short_name').text
        new_contaminant.long_name = contaminant_dict.find('long_name').text
        new_contaminant.sequence = contaminant_dict.find('sequence').text
        new_contaminant.organism = contaminant_dict.find('organism').text
        new_contaminant.save()

        new_contaminant = Contaminant.objects.get(
                category = parent_category,
                uniprot_id = uniprot_id,
                )

        for pack in contaminant_dict.iter('pack'):
            log.debug("Pack found")
            Pack.update(new_contaminant, pack)

        for reference in contaminant_dict.iter('reference'):
            log.debug("Reference found")
            Reference.update(new_contaminant, reference)

        for suggestion in contaminant_dict.iter('suggestion'):
            log.debug("Suggestion found")
            Suggestion.update(new_contaminant, suggestion)

        log.debug("Exit")

    @staticmethod
    def get_all():
        """ Get the list of all registered contaminants with the references """
        contaminants = Contaminant.objects.all()
        for contaminant in contaminants:
            refs = Reference.objects.filter(contaminant = contaminant)
            contaminant.references = refs
            sugg = Suggestion.objects.filter(contaminant = contaminant)
            contaminant.suggestions = sugg
        return contaminants

    @staticmethod
    def get_all_by_category():
        """ Get contaminants grouped by category """
        contaminants = Contaminant.get_all()

        if not contaminants:
            contaminants = []

        grouped_contaminants = {}
        for contaminant in contaminants:
            try:
                grouped_contaminants[contaminant.category].append(contaminant)
            except KeyError:
                grouped_contaminants[contaminant.category] = [contaminant]

        return grouped_contaminants

    def to_simple_dict(self):
        """ Return a dictionary of the fields """
        response_data = {}
        response_data['uniprot_id'] = self.uniprot_id
        response_data['short_name'] = self.short_name
        response_data['long_name'] = self.long_name
        response_data['sequence'] = self.sequence
        response_data['organism'] = self.organism

        return response_data

    def to_detailed_dict(self):
        """ Return a dictionary of the fields and packs """
        response_data = self.to_simple_dict()

        packs = Pack.objects.filter(contaminant = self)
        packs_dict = [pack.to_dict() for pack in packs]
        response_data['packs'] = packs_dict

        suggestions = Suggestion.objects.filter(contaminant = self)
        suggestions_dict = [sugg.to_dict() for sugg in suggestions]
        if suggestions_dict:
            response_data['suggestions'] = suggestions_dict

        references = Reference.objects.filter(contaminant = self)
        references_dict = [ref.to_dict() for ref in references]
        if references_dict:
            response_data['references'] = references_dict

        return response_data


class Pack(models.Model):
    """
        A pack of models prepared by morda_prep

        The packs in this table are prepared on the cluster, and are the result
        of morda_prep on the contaminants list.
    """
    contaminant = models.ForeignKey(Contaminant)
    number = models.IntegerField()  # the number assigned by morda_prep : uniq
                                    # per contaminant
    structure = models.CharField(max_length = 15) # dimer, domain, ...

    def __str__(self):
        """ Write uniprot_id, short_name, number, and quaternary structure """
        contaminant = str(self.contaminant)
        number = str(self.number)
        structure = str(self.structure)
        return (contaminant + ' - ' + number + ' (' + structure + ')')

    @classmethod
    def update(cls, parent_contaminant, pack_dict):
        """ Create Pack based on pack_dict """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        number = len(Pack.objects.filter(contaminant = parent_contaminant)) + 1
        new_pack = Pack()
        new_pack.contaminant = parent_contaminant
        new_pack.number = number # Unique per model
        new_pack.structure = pack_dict.find('quat_structure').text
        new_pack.save()

        new_pack = Pack.objects.get(
                contaminant = parent_contaminant,
                number = number,
                )

        for model in pack_dict.iter('model'):
            log.debug("Model found")
            Model.update(new_pack, model)

        log.debug("Exit")

    def clean(self, *args, **kwargs):
        """ Clean the fields before saving in DB """
        log = logging.getLogger(__name__)
        log.debug("Enter")
        # Structure can be domain, domains, or n-mer with n integer
        if not re.match("^([1-9][0-9]*-mer|domains?)$", self.structure):
            log.error("self.structure does not match the valid values "\
                    + "(domain, domains, or X-mer with X a number)")
            raise ValidationError("structure is not valid")

        # (contaminant, number) pair must be unique
        pack = Pack.objects.filter(
                contaminant = self.contaminant,
                number = self.number,
                )
        if len(pack) != 0 or (len(pack) == 1 and pack[0].pk != self.pk):
            log.error("This pack number already exists for this contaminant")
            raise ValidationError("Pack already registered in database")

        super(Pack, self).clean(*args, **kwargs)

        log.debug("Exit")

    def save(self, *args, **kwargs):
        """ Save the object in DB """
        self.full_clean()
        super(Pack, self).save(*args, **kwargs)

    def to_dict(self):
        """ Return a dictionary of the fields and models """
        response_data = {}
        response_data['number'] = self.number
        response_data['structure'] = self.structure

        models = Model.objects.filter(pack = self)
        models_dict = [model.to_dict() for model in models]
        response_data['models'] = models_dict

        return response_data


class Model(models.Model):
    """
        A model prepared by morda_prep

        The models in this table are prepared on the cluster
    """
    pdb_code = UpperCaseCharField(max_length = 4)
    chain = models.CharField(max_length = 10, null = True, blank = True)
    domain = models.IntegerField(null = True, blank = True, default = None)
    nb_residues = models.IntegerField()
    identity = PercentageField() # in %
    pack = models.ForeignKey(Pack)

    def __str__(self):
        """ Write pack and PDB code of the template """
        pack = str(self.pack)
        pdb_code = str(self.pdb_code)
        return (pack + ' - ' + pdb_code)

    @classmethod
    def update(cls, parent_pack, model_dict):
        """ Create Model based on model_dict """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        new_model = Model()
        new_model.pdb_code = model_dict.find('template').text
        new_model.chain = model_dict.find('chain').text
        new_model.domain = int(model_dict.find('domain').text)
        new_model.nb_residues = int(model_dict.find('n_res').text)
        new_model.identity = int(float(model_dict.find('identity').text)) * 100
        new_model.pack = parent_pack
        new_model.save()

        log.debug("Exit")

    def to_dict(self):
        """ Return a dictionary of the field """
        response_data = {}
        response_data['template'] = self.pdb_code
        response_data['chain'] = self.chain
        response_data['domain'] = self.domain
        response_data['residues'] = self.nb_residues
        response_data['identity'] = self.identity

        return response_data


class Reference(models.Model):
    """
        A publication which mentions the protein as a contaminant
    """
    pubmed_id = models.IntegerField()
    contaminant = models.ForeignKey(Contaminant)

    def __str__(self):
        """ Write uniprot_id and pubmed_id """
        return contaminant.uniprot_id + " -> " + str(self.pubmed_id)

    @classmethod
    def update(cls, parent_contaminant, reference_dict):
        """ Create Reference based on reference_dict """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        new_reference = Reference()
        new_reference.pubmed_id = reference_dict.find('pubmed_id').text
        new_reference.contaminant = parent_contaminant
        new_reference.save()

        log.debug("Exit")

    def to_dict(self):
        """ Return a dictionary of the field """
        response_data = {}
        response_data['pubmed_id'] = self.pubmed_id

        return response_data


class Suggestion(models.Model):
    """
        A person who communicated a new contaminant
    """
    name = models.CharField(max_length=200)
    contaminant = models.ForeignKey(Contaminant)

    def __str__(self):
        """ Write uniprot_id and name of the person """
        return contaminant.uniprot_id + " -> " + self.name

    @classmethod
    def update(cls, parent_contaminant, suggestion_dict):
        """ Create a Suggestion based on suggestion_dict """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        new_suggestion = Suggestion()
        new_suggestion.name = suggestion_dict.find('name').text
        new_suggestion.contaminant = parent_contaminant
        new_suggestion.save()

        log.debug("Exit")

    def to_dict(self):
        """ Return a dictionary of the field """
        response_data = {}
        response_data['name'] = self.name

        return response_data
