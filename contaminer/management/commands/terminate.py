from django.core.management.base import BaseCommand, CommandError
from contaminer.models import Job

import re

class Command(BaseCommand):
    help = 'Retrieve information from the cluster to terminate a job'

    def add_arguments(self, parser):
        parser.add_argument('job_id', nargs='+', type=int)

    def handle(self, *args, **options):
        for job_id in options['job_id']:
            try:
                job = Job.objects.get(pk=job_id)
                job.terminate()
            except (Job.DoesNotExist, RuntimeError):
                raise CommandError(
                'Job "%s" does not exist or is not completed.' % job_id)
            self.stdout.write('Successfully terminate job number "%s"' % job_id)
