# -*- coding : utf-8 -*-

##    Copyright (C) 2015 Hungler Arnaud
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
"""

from django.db import models
from django.conf import settings

import os

import logging

class Category(models.Model):
    """
        A category of contaminant

        selected_by_default is used to know if ContaMiner should test the
        contaminants in this category by default
    """
    name = models.CharField(max_length = 60)
    selected_by_default = models.BooleanField(default = False)

class Contaminant(models.Model):
    """
        A possible contaminant

        The contaminants in this table are prepared on the cluster, and can be
        used to test a file of diffraction data
    """
    uniprot_ID = models.CharField(max_length = 10)
    short_name = models.CharField(max_length = 20)
    long_name = models.CharField(max_length = 100, null = True, blank = True)
    sequence = models.TextField()
    organism = models.CharField(max_length = 50, null = True, blank = True)
    organism_pdb = models.CharFIeld(max_length = 50, null = True, blank = True)

class Pack(models.Model):
    """
        A pack of models prepared by morda_prep

        The packs in this table are prepared on the cluster, and are the result
        of morda_prep on the contaminants list.
    """
    contaminant = models.ForeignKey(Contaminant)
    architecture = models.CharField(max_length = 15) # dimer, domain, ...
    coverage = models.IntegerField() # in %

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

class Job(models.Model):
    """
        A job is the set of tasks launched to test one diffraction data file

        For each file uploaded by a user, a new Job object is created.
    """
    name = models.CharField(max_length = 50, blank = True, null = True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
            blank = True,
            null = True)
    submitted = models.BooleanField(default = False)
    finished = models.BooleanField(default = False)

class Task(models.Model):
    """
        A task is the test of one pack against one diffraction data file

        All tasks for one input file make a Job
    """
    # Input
    job = models.ForeignKey(Job)
    pack = models.ForeignKey(Pack)
    space_group = models.CharField(max_length = 15)

    # State
    error = models.BooleanField(default = False)
    finished = models.BooleanField(default = False)

    # Result
    percent = models.IntegerField(default = None)
    q_factor = models.FloatField(default = None)
    exec_time = models.DurantionField(default = datetime.timedelta(0))
