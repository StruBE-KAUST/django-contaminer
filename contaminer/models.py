# -*- coding : utf-8 -*-

##    Copyright (C) 2016 Hungler Arnaud
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

from .cluster import SSHChannel


class Category(models.Model):
    """
        A category of contaminant

        selected_by_default is used to know if ContaMiner should test the
        contaminants in this category by default
    """
    name = models.CharField(max_length = 60)
    selected_by_default = models.BooleanField(default = False)

    def __str__(self):
        return self.name


class Contaminant(models.Model):
    """
        A possible contaminant

        The contaminants in this table are prepared on the cluster, and can be
        used to test a file of diffraction data
    """
    uniprot_ID = models.CharField(max_length = 10)
    category = models.ForeignKey(Category)
    short_name = models.CharField(max_length = 20)
    long_name = models.CharField(max_length = 100, null = True, blank = True)
    sequence = models.TextField()
    organism = models.CharField(max_length = 50, null = True, blank = True)
    organism_pdb = models.CharField(max_length = 50, null = True, blank = True)

    def __str__(self):
        return self.uniprot_ID


    @staticmethod
    def get_all():
        """ Get the list of all registered contaminants """
        contaminants = Contaminant.objects.all()
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
    architecture = models.CharField(max_length = 15) # dimer, domain, ...
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
    email = models.EmailField(blank = True, null = True)

    confidential = models.BooleanField(default = False)

    def __str__(self):
        res = str(self.name) + " - " + \
                str(self.id) + " (" + \
                str(self.finished) + ")"
        return res


    def create(self, name, author, email, confidential):
        """ Populate the fields of a job """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args :\n\
                name : " + str(name) + "\n\
                author : " + str(author) + "\n\
                email : " + str(email))
        self.name = name
        self.author = author
        self.confidential = confidential
        self.submitted = False
        self.finished = False
        if author:
            self.email = author.email
        if email:
            self.email = email

        self.save()
        log.debug("Exiting function")


    def get_filename(self, suffix = "mtz"):
        """ Return the name of the file associated to the job """
        if not suffix:
            result = "contaminer_" + str(self.id)
        else:
            result = "contaminer_" + str(self.id) + "." + suffix

        return result


    def submit(self, filepath, listpath):
        """ Send the files to the cluster, then launch ContaMiner """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                self : " + str(self) + "\n\
                filepath : " + str(filepath) + "\n\
                listpath : " + str(listpath))

        cluster_comm = SSHChannel()
        cluster_comm.send_file(filepath)
        cluster_comm.send_file(listpath)
        log.debug("Files sent")
        os.remove(filepath)
        os.remove(listpath)
        log.debug("Files deleted from MEDIA_ROOT")

        cluster_comm.launch_contaminer(
                os.path.basename(filepath),
                os.path.basename(listpath)
                )

        self.submitted = True
        self.save()

        log.debug("Job " + str(self.id) + " submitted")
        log.debug("Exiting function")


    def terminate(self):
        """ Retrieve the job from the cluster, then clean-up """
        log = logging.getLogger(__name__)
        log.debug("Entering function for job : " + str(self.id))

        if self.finished:
            log.info("Job is already finished")
            return

        cluster_comm = SSHChannel()
        result_file = cluster_comm.get_result(self.id)

        with open(result_file, 'r') as f:
            for line in f:
                label, value, elaps_time = line[:-1].split(':')
                uniprot_ID, ipack, space_group = label.split('_')
                task = Task()
                task.job = self
                try:
                    contaminant = Contaminant.objects.get(
                            uniprot_ID = uniprot_ID)
                    pack = Pack.objects.filter(
                            contaminant = contaminant).get(
                                    number = ipack)
                except ObjectDoesNotExist:
                    log.error("Database and MoRDa preparation are not "\
                            + "synchronized. Please use the same version "\
                            + "of ContaMiner and django-contaminer, and "\
                            + "load data from fixtures")
                    raise
                task.pack = pack
                task.space_group = space_group
                task.finished = True

                if value in ["error", "nosolution", "cancelled"]:
                    task.percent = 0
                    task.q_factor = 0
                    task.error = (value == "error")
                else:
                    q_factor, percent, seq, struct, mod = value.split('-')
                    task.q_factor = q_factor
                    task.percent = percent
                    task.error = False

                    if int(percent) > 95:
                        cluster_comm.get_final(
                                self.id,
                                task.pack.contaminant.uniprot_ID,
                                task.pack.number,
                                task.space_group
                                )

                task.save()

        self.send_complete_mail()

        self.finished = True
        self.save()

        log.info("Job complete")

        log.debug("Exiting function")


    def send_complete_mail(self):
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        current_site = Site.objects.get_current()
        result_url = "{0}://{1}{2}".format(
                "https",
                current_site.domain,
                reverse("ContaMiner:result", args=[self.id])
                )
        log.debug("Result URL : " + str(result_url))

        ctx = { 'job_name': self.name,
                'result_link': result_url,
                'SITE_NAME': current_site.name,
                }

        message = render_to_string("ContaMiner/email/complete_message.html",
                ctx)
        send_mail("Job complete", "",
                settings.DEFAULT_MAIL, [self.email],
                html_message = message)
        log.info("E-Mail sent to " + str(self.email))

        log.debug("Exiting function")


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
    exec_time = models.DurationField(default = datetime.timedelta(0))

    def __str__(self):
        return (str(self.job) + str(self.pack) + str(self.space_group))

    def name(self):
        space_group = self.space_group.replace(' ', '-')
        name = str(self.pack.contaminant.uniprot_ID) + '_'\
                + str(self.pack.number) + '_'\
                + space_group

        return name
