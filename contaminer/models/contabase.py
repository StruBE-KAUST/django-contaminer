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

from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError

from .tools import UpperCaseCharField
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
        obsolete_txt = "obsolete" if self.obsolete else "current"
        return str(self.id) + " - " + obsolete_txt

    @classmethod
    def get_current(cls):
        current_list = cls.objects.get(obsolete = False)
        return current_list

    def make_obsolete(self):
        self.obsolete = True
        self.save()

    @classmethod
    def make_all_obsolete(cls):
        all_objects = cls.objects.all()
        map(lambda x: x.make_obsolete(), all_objects)



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
        return self.name + " - " + str(self.selected_by_default)

    def clean(self, *args, **kwargs):
        category = Category.objects.filter(
                contabase = self.contabase,
                number = self.number,
                )
        if len(category) != 0 or (len(category) == 1 and category[0].pk != self.pk):
            raise ValidationError("Category already registered in ContaBase")

        super(Category, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Category, self).save(*args, **kwargs)



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
        return self.uniprot_id + ' - ' + self.short_name

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
        contaminant = str(self.contaminant)
        number = str(self.number)
        structure = str(self.structure)
        return (contaminant + ' - ' + number + ' (' + structure + ')')

    def clean(self, *args, **kwargs):
        # Structure can be domain, domains, or n-mer with n integer
        if not re.match("^([1-9][0-9]*-mer|domains?)$", self.structure):
            raise ValidationError("structure is not valid")

        # (contaminant, number) pair must be unique
        pack = Pack.objects.filter(
                contaminant = self.contaminant,
                number = self.number,
                )
        if len(pack) != 0 or (len(pack) == 1 and pack[0].pk != self.pk):
            raise ValidationError("Pack already registered in database")

        super(Pack, self).clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Pack, self).save(*args, **kwargs)


class Model(models.Model):
    """
        A model prepared by morda_prep

        The models in this table are prepared on the cluster
    """
    pdb_code = UpperCaseCharField(max_length = 4)
    chain = models.CharField(max_length = 10, null = True, blank = True)
    domain = models.IntegerField(null = True, blank = True, default = None)
    nb_residues = models.IntegerField()
    identity = models.IntegerField() # in %
    pack = models.ForeignKey(Pack)

    def __str__(self):
        pack = str(self.pack)
        pdb_code = str(self.pdb_code)
        return (pack + ' - ' + pdb_code)

    def clean(self, *args, **kwargs):
        # Number of residues should be lower than the sequence length of
        # the contaminant
        if self.nb_residues > len(self.pack.contaminant.sequence):
            raise ValidationError(
                    "nb_residues is too large for this contaminant"
                    )

        # Identity is a percentage and should be between 0 and 100
        if self.identity < 0 or self.identity > 100:
            raise ValidationError(
                    "A percentage should be between 0 and 100"
                    )

        super(Model, self).clean(*args, **kwargs)

    def save(self,  *args, **kwargs):
        self.full_clean()
        super(Model, self).save(*args, **kwargs)


class Reference(models.Model):
    """
        A publication which mentions the protein as a contaminant
    """
    pubmed_id = models.IntegerField()
    contaminant = models.ForeignKey(Contaminant)

    def __str__(self):
        return contaminant.uniprot_id + " -> " + str(pubmed_id)


class Suggestion(models.Model):
    """
        A person who communicated a new contaminant
    """
    name = models.CharField(max_length=200)
    contaminant = models.ForeignKey(Contaminant)
