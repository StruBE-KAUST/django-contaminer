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
Job-related models for ContaMiner application.

This module contains the classes definition for the application named
"ContaMiner".
This module contains only the job management (not the ContaBase).
See models/contabase.py for the ContaBase related models.
"""

import os
import re
import datetime
import logging
import errno

from django.apps import apps
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail import mail_admins
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned

from .contabase import ContaBase
from .contabase import Contaminant
from .contabase import Pack
from ..ssh_tools import SFTPChannel
from ..ssh_tools import SSHChannel
from .tools import PercentageField

# pylint: disable=too-many-instance-attributes
class Job(models.Model):
    """
    Set of tasks launched to test one diffraction data file.

    For each file uploaded by a user, a new Job object is created.
    :status_submitted: True if the job has been submitted to the cluster
    :status_running: True if the job tasks has started on the cluster
    :status_complete: True if the cluster job is finished, and all the data are
    retrieved to the django application. Usually goes with status_archived
    :status_error: True if the job encountered any error at any step
    :status_archived: When true, the cron task will not try to make a future
    modification to the job.
    :submission_date: date of the form submission
    :mail_sent: True if notification mail has been sent. Mainly used for
    debugging purpose as the mail server looks unstable
    :name: Displayed name of the job on the end-user side.
    :author: User who submitted the job if he's logged in. Blank if anonymous.
    :email: E-mail address used to send any notification
    :confidential: If true, only the logged in author can see the results of
    the job.
    """
    # Status
    status_submitted = models.BooleanField(default=False)
    status_running = models.BooleanField(default=False)
    status_complete = models.BooleanField(default=False)
    status_error = models.BooleanField(default=False)
    status_archived = models.BooleanField(default=False)
    mail_sent = models.BooleanField(default=False)
    
    # Form fields
    submission_date = models.DateField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    confidential = models.BooleanField(default=False)

    def __str__(self):
        """Return id (email) status."""
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        """Return id (email) status."""
        res = str(self.id) + " (" \
                + str(self.email) + ")" \
                + " " + self.get_status()
        return res

    def get_status(self):
        """
        Return the status of the job as a string.

        :return: status is a string and can be:
        New
        Submitted
        Running
        Complete
        Error
        """
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
    def create(cls, name, author=None, email=None, confidential=False):
        """
        Create a new job and fill in the fields.

        :param: cls is Job
        :param: name is the displayed job name
        :param: author (optional) is the author
        :param: email (optional) is the address used for notifications
        :param: confidential (default False) sets the job as confidential if 
        True
        :return: The created job
        """
        log = logging.getLogger(__name__)
        log.debug("Entering function with args :\n\
                name : " + str(name) + "\n\
                author : " + str(author) + "\n\
                email : " + str(email))
        job = cls(name=name)
        job.author = author
        job.confidential = confidential
        job.status_submitted = False
        job.status_complete = False
        if author:
            job.email = author.email
        if email:
            job.email = email

        job.save()
        log.debug("Exiting function")

        return job

    def get_filename(self, suffix=''):
        """
        Return the name of the file associated to the job.

        :param: suffix is a string to add at the end of the file. Can be
        the extension.
        :return: web_task_id.suffix
        """
        if not suffix:
            result = "web_task_" + str(self.id)
        else:
            if suffix[0] == '.':
                suffix = suffix[1:]
            result = "web_task_" + str(self.id) + "." + suffix

        return result

    def submit(self, filepath, contaminants):
        """Send the files to the cluster, then launch ContaMiner."""
        # TODO: Divide in send, then launch
        log = logging.getLogger(__name__)
        log.debug("Entering function with args : \n\
                self: " + str(self) + "\n\
                filepath: " + str(filepath) + "\n\
                contaminants: " + str(contaminants))

        # Send files to cluster
        remote_work_directory = \
                apps.get_app_config('contaminer').ssh_work_directory
        input_file_ext = os.path.splitext(filepath)[1]
        remote_filepath = os.path.join(
            remote_work_directory,
            self.get_filename(suffix=input_file_ext))
        remote_contaminants = os.path.join(
            remote_work_directory,
            self.get_filename(suffix='txt'))
        client = SFTPChannel()
        client.send_file(filepath, remote_work_directory)
        client.write_file(remote_contaminants, contaminants)

        # Remove local file
        os.remove(filepath)
        log.debug("Files deleted from MEDIA_ROOT: " + filepath)

        # Run contaminer command
        contaminer_solve_command = os.path.join(
            apps.get_app_config('contaminer').ssh_contaminer_location,
            "contaminer") + " solve"
        cd_command = 'cd "' + remote_work_directory + '"'

        command = cd_command + " && "\
            + contaminer_solve_command + " "\
            + '"' + str(os.path.basename(remote_filepath)) + '" "'\
            + str(os.path.basename(remote_contaminants)) + '"'

        log.debug("Execute command on remote host:\n" + command)
        stdout = SSHChannel().exec_command(command)

        log.debug("stdout: " + str(stdout))

        # Change state
        self.status_submitted = True
        self.save()

        log.debug("Job " + str(self.id) + " submitted")
        log.debug("Exiting function")

    def update_status(self):
        """Retrieve the status from the cluster and update it in DB."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if self.status_archived:
            log.warning("Archived. No modification will be recorded.")
            return

        remote_work_directory = \
                apps.get_app_config('contaminer').ssh_work_directory
        remote_contaminer_command = os.path.join(
            apps.get_app_config('contaminer').ssh_contaminer_location,
            "contaminer") + " job_status"
        remote_filename = os.path.join(
            remote_work_directory,
            self.get_filename(suffix=''))

        command = remote_contaminer_command + " " + remote_filename

        client = SSHChannel()
        log.debug("Execute command on remote host:\n" + command)
        stdout = client.exec_command(command)

        log.debug("stdout: " + str(stdout))

        # Change state
        if "submitted" in stdout:
            self.status_submitted = True
            self.status_error = False
            if self.status_complete or self.status_running:
                log.warning("Job status are not coherent.")
        elif "running" in stdout:
            self.status_submitted = True
            self.status_running = True
            self.status_error = False
            if self.status_complete:
                log.warning("Job status are not coherent.")
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
        """Create the tasks for the job."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if self.status_archived:
            log.warning("Archived. No modification will be recorded.")
            return

        if not self.status_submitted:
            raise RuntimeError("Job should be submitted first.")

        remote_work_dirname = os.path.join(
            apps.get_app_config('contaminer').ssh_work_directory,
            self.get_filename(suffix=''))
        remote_results_filename = os.path.join(
            remote_work_dirname,
            "results.txt")
        results_content = SSHChannel().read_file(remote_results_filename)

        for line in results_content.split('\n'):
            if line is not "":
                Task.update(self, line)

        log.debug("Exit")

    def update(self):
        """If self is not archived, update status and tasks."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if self.status_archived:
            log.warning("Archived. No modification will be recorded.")
            return

        self.update_tasks()
        self.update_status()

        if self.status_complete:
            self.status_archived = True
            self.save()
            self.send_complete_mail()

        log.debug("Exit")

    @classmethod
    def update_all(cls):
        """Update all the non-archived and submitted jobs."""
        log = logging.getLogger(__name__)
        log.debug("Enter")

        jobs = Job.objects.filter(
            status_archived=False,
            status_submitted=True)
        for job in jobs:
            log.debug("Update job: " + str(job))
            try:
                job.update()
            except RuntimeError as excep:
                log.error("Job update interrupted with exception: " \
                    + str(excep))
                message = "Error when updating job: " + str(job) \
                    + "\n" + str(excep)
                mail_admins(
                    "Update error",
                    message)

        log.debug("Exit")

    def to_detailed_dict(self):
        """Return a dictionary of the fields."""
        response_data = {}
        response_data['id'] = self.id

        tasks = Task.objects.filter(job=self)
        tasks_dict = [task.to_dict() for task in tasks]
        response_data['results'] = tasks_dict

        return response_data

    def to_simple_dict(self):
        """Return the results compiled per contaminant."""
        response_data = {}
        response_data['id'] = self.id
        messages = None

        tasks = Task.objects.filter(job=self)
        uniprot_ids = [task.pack.contaminant.uniprot_id for task in tasks]
        unique_uniprot_ids = list(set(uniprot_ids))

        results = []
        app_config = apps.get_app_config('contaminer')
        coverage_threshold = app_config.bad_model_coverage_threshold
        identity_threshold = app_config.bad_model_identity_threshold

        for uniprot_id in unique_uniprot_ids:
            result_data = {}
            result_data['uniprot_id'] = uniprot_id
            messages = {}

            tasks = Task.objects.filter(
                job=self,
                pack__contaminant__uniprot_id=uniprot_id)

            error = True # All tasks are in error
            complete = True # All tasks are complete
            best_task = None

            for task in tasks:
                status = task.get_status()
                if status in ['New', 'Running']:
                    complete = False # At least one is not in error
                    error = False # At least one is not complete
                    continue
                if status == 'Error':
                    continue
                if status == 'Complete':
                    error = False # At least one is not in error
                    best_task = max(task, best_task)

            if error: # All in error, or no task
                result_data['status'] = "Error"
            else:
                if best_task:
                    result_data['percent'] = best_task.percent
                    result_data['q_factor'] = best_task.q_factor
                    result_data['pack_number'] = best_task.pack.number
                    result_data['space_group'] = best_task.space_group

                    final_files_path = os.path.join(\
                        settings.MEDIA_ROOT,
                        best_task.get_final_filename("pdb"))
                    result_data['files_available'] = \
                        str(os.path.exists(final_files_path))

                    coverage = best_task.pack.coverage
                    identity = best_task.pack.identity
                    if coverage < coverage_threshold \
                        or identity < identity_threshold:
                        messages['bad_model'] = \
                            "Your dataset gives a positive result for a "\
                            + "contaminant for which no identical model is "\
                            + "available in the PDB.\nYou could deposit or "\
                            + "publish this structure."

                if complete:
                    result_data['status'] = "Complete"
                else:
                    result_data['status'] = "Running"

            results.append(result_data)

        if messages:
            response_data['messages'] = messages

        response_data['results'] = results
        return response_data

    def get_best_tasks(self):
        """Return the list of the best task for each contaminant."""
        contaminants = Contaminant.objects.filter(
            category__contabase=ContaBase.get_current())
        best_tasks = []
        for contaminant in contaminants:
            best_task = self.get_best_task(contaminant)
            if best_task:
                best_tasks.append(best_task)

        return best_tasks

    def get_best_task(self, contaminant):
        """
        Return the best task for the given contaminant.

        Sort by validity (complete and not error), percent, q_factor,
        pack coverage, then pack identity.
        """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        tasks = Task.objects.filter(job=self,
                pack__contaminant__uniprot_id=contaminant.uniprot_id)

        valid_tasks = [
            task for task in tasks
            if task.status_complete and not task.status_error]

        if valid_tasks == []:
            return None

        return max(valid_tasks)

    def send_complete_mail(self):
        """If an address is available, send an email."""
        log = logging.getLogger(__name__)
        log.debug("Entering function")

        if not self.email:
            log.warning("No mail for this job: " + str(self))
            return

        current_site = Site.objects.get_current()
        logo_url = "{0}://{1}{2}{3}".format(
            "https",
            current_site.domain,
            settings.STATIC_URL,
            "contaminer/img/logo.png")
        result_url = "{0}://{1}{2}".format(
            "https",
            current_site.domain,
            reverse("ContaMiner:display", args=[self.id]))
        log.debug("Result URL : " + str(result_url))

        ctx = {
            'job_name': self.name,
            'logo_url': logo_url,
            'result_link': result_url,
            'site_name': "ContaMiner"}

        exp_mail = settings.DEFAULT_MAIL_FROM

        message = render_to_string(
            "ContaMiner/email/complete_message.html",
            ctx)
        send_mail(
            "ContaMiner job complete",
            "",
            exp_mail,
            [self.email],
            html_message=message)
        log.info("E-Mail sent to " + str(self.email))

        self.mail_sent = True
        self.save()

        log.debug("Exiting function")


class Task(models.Model):
    """
    A task is the test of one pack in one space group against one diffraction
    data file.

    All tasks for one input file make a Job.

    :job: The job this task is part of.
    :pack: The pack being tested in this task.
    :space_group: Space group, dash '-' seprated.
    :status_complete: True if the task is complete.
    :status_running: True if the task is running on the cluster.
    :status_error: True if the task encountered an error.
    :percent: The percent score given by MoRDa (0 if not available).
    :q_factor: The Q_factor given by MoRDa (0 if not available).
    :exec_time: Time of execution (running state) on the cluster.
    """

    # Input
    job = models.ForeignKey(Job)
    pack = models.ForeignKey(Pack)
    space_group = models.CharField(max_length=15)

    # State
    status_complete = models.BooleanField(default=False)
    status_running = models.BooleanField(default=False)
    status_error = models.BooleanField(default=False)

    # Result
    percent = PercentageField(null=True, default=None)
    q_factor = models.FloatField(null=True, default=None)
    exec_time = models.DurationField(default=datetime.timedelta(0))

    def __str__(self):
        """Write job - pack - space group."""
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        """Write job - pack - space group."""
        return str(self.job) \
                + " / " + str(self.pack)\
                + " / " + str(self.space_group)\
                + " / " + self.get_status()

    def __cmp__(self, other):
        """
        Compare the scores of the two tasks.

        The greatest has the highest percentage, then q_factor, then
        coverage, then identity.
        /!\ Does not override __eq__ from django models /!\
        Allow the usage of <, <=, >, >=
        """
        if not isinstance(other, Task):
            return NotImplemented

        if self.percent > other.percent:
            return 1
        elif self.percent < other.percent:
            return -1

        if self.q_factor > other.q_factor:
            return 1
        elif self.q_factor < other.q_factor:
            return -1

        if self.pack.coverage > other.pack.coverage:
            return 1
        elif self.pack.coverage > other.pack.coverage:
            return -1

        if self.pack.identity > other.pack.identity:
            return 1
        elif self.pack.identity > other.pack.identity:
            return -1

        return 0

    def get_status(self):
        """
        Return the status as a string.
        
        :return: Status (string) can be Error, Complete, Running, or New
        """
        if self.status_error:
            return "Error"
        if self.status_complete:
            return "Complete"
        if self.status_running:
            return "Running"
        return "New"

    def name(self):
        """Return standardized name of the task."""
        space_group = self.space_group.replace(' ', '-')
        name = str(self.pack.contaminant.uniprot_id) + '_'\
                + str(self.pack.number) + '_'\
                + space_group

        return name

    @classmethod
    def from_name(cls, job, task_name):
        """Return the task with the given name"""
        uniprot_id, pack_number, space_group = task_name.split('_')

        task = cls.objects.get(
            job=job,
            pack__number=pack_number,
            pack__contaminant__uniprot_id=uniprot_id,
            space_group=space_group)

        return task

    @staticmethod
    def parse_line(line):
        """
        Parse a line from results.txt to give.

        :param line: line to parse
        :returns: dictionnary containing the 7 parsed values
        
        The line formatting must be 7 fields separated by a comma ',' in this
        order:
        uniprot_id: any string without comma or new line
        pack_number: integer
        space group: full space group name, dash '-' separated
        status: can be 'new', 'running', 'completed', or 'error'
        q_factor: decimal, dot '.' separated
        percent: integer
        elapsed_time: following the regexp '\d+h [\d ]\dm [\d ]\ds'

        Return a dictionnary with the keys:
        uniprot_id: string
        pack_number: integer
        space_group: string
        status: string
        q_factor: float
        percent: integer
        elapsed_seconds: integer
        """
        # Split line in fields
        line_bites = line.split(',')
        elapsed_time = line_bites[6]
        
        # Parse time
        try:
            hours, minutes, seconds = re.split(' +', elapsed_time)
        except ValueError:
            elapsed_seconds = 0
        else:
            hours = int(hours[:-1])
            minutes = int(minutes[:-1])
            seconds = int(seconds[:-1])
            elapsed_seconds = ((hours * 60) + minutes) * 60 + seconds

        # Build results dictionary
        result = {
            'uniprot_id': line_bites[0],
            'pack_number': int(line_bites[1]),
            'space_group': line_bites[2],
            'status': line_bites[3],
            'q_factor': float(line_bites[4]),
            'percent': int(line_bites[5]),
            'elapsed_seconds': elapsed_seconds,
            }

        return result

    @classmethod
    def update(cls, job, line):
        """
        Create or update the task attached to job, with line information.

        :param cls: Task class
        :param job: Job instance. A created task is attached to this job. An
        updated task must already be attached to this job to be found.
        :param line: line describing the task.
        :returns: the created or updated task

        The line formatting must be 7 fields separated by a comma ',' in this
        order:
        uniprot_id: any string without comma or new line
        pack_number: integer
        space group: full space group name, dash '-' separated
        status: can be 'new', 'running', 'completed', or 'error'
        q_factor: decimal, dot '.' separated
        percent: integer
        elapsed_time: following the regexp '\d+h [\d ]\dm [\d ]\ds'

        If the task already exist and is complete, not further update is
        done for this task.
        """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        # Parse line
        try:
            parsed_line = cls.parse_line(line)
        except (ValueError, IndexError):
            log.warning("Invalid line to parse: " + str(line))
            raise ValueError("Invalid line to parse: " + str(line))

        try:
            contaminant = Contaminant.objects.get(
                uniprot_id=parsed_line['uniprot_id'],
                category__contabase=ContaBase.get_current())
            pack = Pack.objects.get(
                contaminant=contaminant,
                number=parsed_line['pack_number'])
        except (ObjectDoesNotExist, MultipleObjectsReturned) as excep:
            log.warning("Multiple contaminants or packs returned.")
            log.warning(str(excep))
            log.error("Database is not consistent.")
            raise excep

        try:
            task = Task.objects.get(
                job=job,
                pack=pack,
                space_group=parsed_line['space_group'])
        except ObjectDoesNotExist:
            task = Task()
            task.job = job
            task.pack = pack
            task.space_group = parsed_line['space_group']

        if task.status_complete:
            log.info("Trying to update a complete task. Skipping...")
            return task
        
        task.status_complete = \
            (parsed_line['status'] in ["completed", "aborted"])
        task.status_running = (parsed_line['status'] == "running")
        task.status_error = (parsed_line['status'] == "error")

        task.percent = parsed_line['percent']
        task.q_factor = parsed_line['q_factor']

        if task.percent > 90:
            task.get_final_files()

        task.exec_time = \
            datetime.timedelta(seconds=parsed_line['elapsed_seconds'])

        task.save()
        log.debug("Exit")
        return task

    def get_final_filename(self, suffix=''):
        """Return the filename of the final files followed by the suffix."""
        filename = self.pack.contaminant.uniprot_id + "_" \
                + str(self.pack.number) + "_" \
                + self.space_group.replace(' ', '-')

        if suffix:
            if suffix[0] == '.':
                suffix = suffix[1:]
            filename = filename + "." + suffix

        return os.path.join(self.job.get_filename(), filename)

    def get_final_files(self):
        """
        Download the final PDB, MTZ and MAP files for this task from the
        supercomputer.
        """
        log = logging.getLogger(__name__)
        log.debug("Enter")

        if not self.status_complete:
            log.warning("Trying to retreive files for a non complete task.")
            log.debug("Exit")
            return

        task_dir = self.get_final_filename()

        remote_mtz = os.path.join(task_dir, "results_solve/final.mtz")
        remote_pdb = os.path.join(task_dir, "results_solve/final.pdb")
        remote_map = os.path.join(task_dir, "results_solve/final.map")
        remote_map_diff = os.path.join(task_dir, "results_solve/final.diff.map")

        local_mtz = os.path.join(
            settings.MEDIA_ROOT,
            self.get_final_filename(suffix="mtz"))
        local_pdb = os.path.join(
            settings.MEDIA_ROOT,
            self.get_final_filename(suffix="pdb"))
        local_map = os.path.join(
            settings.MEDIA_ROOT,
            self.get_final_filename(suffix="map"))
        local_map_diff = os.path.join(
            settings.MEDIA_ROOT,
            self.get_final_filename(suffix="diff.map"))

        try:
            os.makedirs(os.path.dirname(local_mtz))
        except OSError as excep:
            if excep.errno == errno.EEXIST \
                    and os.path.isdir(os.path.dirname(local_mtz)):
                pass
            else:
                raise

        client = SFTPChannel()
        try:
            client.download_from_contaminer(remote_mtz, local_mtz)
            client.download_from_contaminer(remote_pdb, local_pdb)
            client.download_from_contaminer(remote_map, local_map)
            client.download_from_contaminer(remote_map_diff, local_map_diff)
        except (OSError, IOError) as excep:
            log.error("Error when downloading files from cluster: " \
                + str(excep))
            raise

        log.debug("Exit")

    def to_dict(self):
        """Return a dictionary of the fields."""
        response_data = {}
        response_data['uniprot_id'] = self.pack.contaminant.uniprot_id
        response_data['pack_nb'] = self.pack.number
        response_data['space_group'] = self.space_group
        response_data['status'] = self.get_status()
        if self.status_complete and not self.status_error:
            response_data['percent'] = self.percent
            response_data['q_factor'] = self.q_factor

        final_files_path = os.path.join(\
            settings.MEDIA_ROOT,
            self.get_final_filename("pdb"))
        response_data['files_available'] = \
            str(os.path.exists(final_files_path))

        return response_data
