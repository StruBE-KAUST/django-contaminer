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
    This module contains only the job management (not the ContaBase).
    See models/contabase.py for the ContaBase related models.
"""

import os
import re
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
from django.core.exceptions import MultipleObjectsReturned
from django.core.exceptions import ValidationError

from ..ssh_tools import SSHChannel
from ..ssh_tools import SFTPChannel
from .contabase import Pack
from .tools import PercentageField

from .contabase import ContaBase
from .contabase import Contaminant
from .contabase import Pack

from ..apps import ContaminerConfig


class Job(models.Model):
    """
        A job is the set of tasks launched to test one diffraction data file

        For each file uploaded by a user, a new Job object is created.
    """
    id = models.AutoField(unique = True, primary_key = True)
    status_submitted = models.BooleanField(default = False)
    status_running = models.BooleanField(default = False)
    status_complete = models.BooleanField(default = False)
    status_error = models.BooleanField(default = False)
    status_archived = models.BooleanField(default = False)

    name = models.CharField(max_length = 50, blank = True, null = True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
            blank = True,
            null = True)
    email = models.EmailField(blank = True, null = True)

    confidential = models.BooleanField(default = False)

    def __str__(self):
        """ Write id (email) """
        res = str(self.id) + " (" \
                + str(self.email) + ")" \
                + " " + self.get_status()
        return res

    def get_status(self):
        """ Gives the status of the job as a string """
        # Return cached result if no improvement is possible
        if self.status_error:
            return "Error"
        if self.status_complete:
            return "Complete"

        if not self.status_archived:
            self.update_status()

        if self.status_error:
            return "Error"
        if self.status_complete:
            return "Complete"
        if self.status_running:
            return "Running"
        if self.status_submitted:
            return "Submitted"
        return "New"

    @classmethod
    def create(cls, name, author = None, email = None, confidential = False):
        """ Populate the fields of a job """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args :\n\
                name : " + str(name) + "\n\
                author : " + str(author) + "\n\
                email : " + str(email))
        job = cls(name = name)
        job.author = author
        job.confidential = confidential
        job.submitted = False
        job.finished = False
        if author:
            job.email = author.email
        if email:
            job.email = email

        job.save()
        log.debug("Exiting function")

        return job

    def get_filename(self, suffix = ''):
        """ Return the name of the file associated to the job """
        if not suffix:
            result = "web_task_" + str(self.id)
        else:
            if suffix[0] == '.':
                suffix = suffix[1:]
            result = "web_task_" + str(self.id) + "." + suffix

        return result

    def submit(self, filepath, contaminants):
        """ Send the files to the cluster, then launch ContaMiner """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                self: " + str(self) + "\n\
                filepath: " + str(filepath) + "\n\
                contaminants: " + str(contaminants))

        # Send files to cluster
        remote_work_directory = ContaminerConfig().ssh_work_directory
        input_file_ext = os.path.splitext(filepath)[1]
        remote_filepath = os.path.join(
                remote_work_directory,
                self.get_filename(suffix = input_file_ext)
                )
        remote_contaminants = self.get_filename(suffix = 'txt')
        client = SFTPChannel()
        client.send_file(filepath, remote_filepath)
        client.write_file(remote_contaminants, contaminants)

        # Remove local file
        os.remove(filepath)
        log.debug("Files deleted from MEDIA_ROOT: " + filepath)

        # Run contaminer command
        contaminer_solve_command = os.path.join(
                ContaminerConfig().ssh_contaminer_location,
                "contaminer") + " solve"
        cd_command = 'cd "' + remote_work_directory + '"'

        command = cd_command + " && "\
            + contaminer_solve_command + " "\
            + '"' + str(os.path.basename(remote_filepath)) + '" "'\
            + str(os.path.basename(remote_contaminants)) + '"'

        log.debug("Execute command on remote host:\n" + command)
        stdout, stderr = client.exec_command(command)

        log.debug("stdout: " + str(stdout))
        log.debug("stderr: " + str(stderr))

        if stderr is not "":
            log.warning("Standard error is not empty : \n" + str(stderr))
            raise RuntimeError(str(stderr))

        # Change state
        self.status_submitted = True
        self.save()

        log.debug("Job " + str(self.id) + " submitted")
        log.debug("Exiting function")

    def update_status(self):
        """ Retrieve the status from the cluster and update it in DB """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if self.status_archived:
            log.warning("Archived. No modification will be recorded.")
            return

        remote_work_directory = ContaminerConfig().ssh_work_directory
        remote_contaminer_command = os.path.join(
                ContaminerConfig().ssh_contaminer_location,
                "contaminer") + " job_status"
        remote_filename = os.path.join(
                remote_work_directory,
                self.get_filename(suffix = '')
                )

        command = remote_contaminer_command + " " + remote_filename

        client = SSHChannel()
        log.debug("Execute command on remote host:\n" + command)
        stdout, stderr = client.exec_command(command)

        log.debug("stdout: " + str(stdout))
        log.debug("stderr: " + str(stderr))

        if stderr is not "":
            log.warning("Standard error is not empty : \n" + str(stderr))
            raise RuntimeError(str(stderr))

        # Change state
        if "submitted" in stdout:
            self.status_submitted = True
            self.status_error = False
            if self.status_complete or self.status_running:
                log.warning("Job states are not coherent.")
        elif "running" in stdout:
            self.status_submitted = True
            self.status_running = True
            self.status_error = False
            if self.status_complete:
                log.warning("Job states are not coherent.")
        elif "complete" in stdout:
            self.status_submitted = True
            self.status_running = False
            self.status_complete = True
        elif "error" in stdout:
            self.status_error = True
            log.warning("Job is in error with id: " + str(self.id))

        self.save()

        log.debug("Exit")

    def update_tasks(self):
        """ Create the tasks for the job """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if self.archived:
            log.warning("Archived. No modification will be recorded.")
            return

        if not self.submitted:
            raise RuntimeError("Job should be submitted first.")

        remote_work_dirname = os.path.join(
                ContaminerConfig().ssh_work_directory,
                self.get_filename(suffix = '')
                )
        remote_results_filename = os.path.join(
                remote_work_dirname,
                "results.txt"
                )
        results_content = SSHChannel().read_file(remote_results_filename)

        for line in results_content.split('\n'):
            if line is not "":
                Task.update(self, line)

        log.debug("Exit")

    def update(self):
        """ If self is not archived, update status and tasks """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if self.archived:
            log.warning("Archived. No modification will be recorded.")
            return

        self.update_status()
        self.update_tasks()
        log.debug("Exit")


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
                'site_name': "ContaMiner",
                }

        message = render_to_string("ContaMiner/email/complete_message.html",
                ctx)
        send_mail("Job complete", "",
                settings.DEFAULT_MAIL_FROM, [self.email],
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
    status_complete = models.BooleanField(default = False)
    status_error = models.BooleanField(default = False)

    # Result
    percent = PercentageField(null = True, default = None)
    q_factor = models.FloatField(null = True, default = None)
    exec_time = models.DurationField(default = datetime.timedelta(0))

    def __str__(self):
        """ Write job - pack - space group """
        return (str(self.job) \
                + " / " + str(self.pack)\
                + " / " + str(self.space_group)\
                + " / " + self.get_status())

    def get_status(self):
        """ Return the status as a string """
        if self.status_error:
            return "Error"
        if self.status_complete:
            return "Complete"
        return "New"

    def name(self):
        space_group = self.space_group.replace(' ', '-')
        name = str(self.pack.contaminant.uniprot_ID) + '_'\
                + str(self.pack.number) + '_'\
                + space_group

        return name

    @classmethod
    def update(cls, job, line):
        """ Create the task attached to job, with line information """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        # Parse line
        try:
            pack, scores, time = line.split(':')

            # Parse pack
            uniprot_id, pack_number, space_group = pack.split('_')

            # Parse time
            hours, minutes, seconds = re.split(' +', time)
            hours = int(hours[:-1])
            minutes = int(minutes[:-1])
            seconds = int(seconds[:-1])
            time_seconds = ((hours * 60) + minutes) * 60 + seconds
        except ValueError:
            log.warning("Invalid line to parse: " + str(line))
            raise

        try:
            contaminant = Contaminant.objects.get(
                    uniprot_id = uniprot_id,
                    category__contabase = ContaBase.get_current(),
                    )
            pack = Pack.objects.get(
                    contaminant = contaminant,
                    number = pack_number,
                    )
        except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
            log.warning("Multiple contaminants or packs returned.")
            log.warning(str(e))
            log.error("Database is not consistent.")
            raise e

        try:
            task = Task.objects.get(
                    job = job,
                    pack = pack,
                    space_group = space_group
                    )
        except ObjectDoesNotExist:
            task = Task()
            task.job = job
            task.pack = pack
            task.space_group = space_group

        if scores == "cancelled":
            task.status_complete = False
            task.percent = 0
            task.q_facotr = 0
        else:
            task.status_complete = True

        if scores == "error":
            task.status_error = True
        else:
            task.status_error = False

        if task.status_complete and not task.status_error:
            if scores == "nosolution":
                task.percent = 0
                task.q_factor = 0
            else:
                try:
                    q_factor, percent = scores.split('-')
                except ValueError:
                    log.warning("Invalid line to parse: " + str(line))
                    raise
                task.percent = int(percent)
                task.q_factor = float(q_factor)

        task.exec_time = datetime.timedelta(seconds = time_seconds)

        task.save()
        log.debug("Exit")
        return task
