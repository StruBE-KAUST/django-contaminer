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

from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from .tools import UpperCaseCharField

class Category(models.Model):
    """
        A category of contaminant

        selected_by_default is used to know if ContaMiner should test the
        contaminants in this category by default
    """
    id = models.IntegerField(unique = True, primary_key = True)
    name = models.CharField(max_length = 60)
    selected_by_default = models.BooleanField(default = False)

    def __str__(self):
        return self.name + " - " + str(self.selected_by_default)


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
    coverage = models.IntegerField() # in %

    def __str__(self):
        return (str(self.contaminant) + str(self.number))


class Model(models.Model):
    """
        A model prepared by morda_prep

        The models in this table are prepared on the cluster
    """
    pdb_code = models.CharField(max_length = 4)
    chain = models.CharField(max_length = 10, null = True, blank = True)
    domain = models.IntegerField(null = True, blank = True, default = None)
    identity = models.IntegerField() # in %
    pack = models.ForeignKey(Pack)

    def __str__(self):
        return (str(self.pdb_code) + self.chain + str(self.domain))
