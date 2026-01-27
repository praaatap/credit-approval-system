"""
Django management command to ingest data from Excel files.

Usage:
    python manage.py ingest_data
    python manage.py ingest_data --sync  # Run synchronously instead of using Celery
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Ingest customer and loan data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run synchronously instead of using Celery background tasks',
        )
        parser.add_argument(
            '--customers-only',
            action='store_true',
            help='Only ingest customer data',
        )
        parser.add_argument(
            '--loans-only',
            action='store_true',
            help='Only ingest loan data',
        )

    def handle(self, *args, **options):
        from loans.tasks import ingest_customer_data, ingest_loan_data
        
        sync_mode = options['sync']
        customers_only = options['customers_only']
        loans_only = options['loans_only']
        
        customer_file = os.path.join(settings.DATA_FILES_PATH, 'customer_data.xlsx')
        loan_file = os.path.join(settings.DATA_FILES_PATH, 'loan_data.xlsx')
        
        self.stdout.write(self.style.NOTICE('Starting data ingestion...'))
        
        if not loans_only:
            self.stdout.write(f'Customer data file: {customer_file}')
            if not os.path.exists(customer_file):
                self.stdout.write(self.style.ERROR(f'Customer file not found: {customer_file}'))
            else:
                if sync_mode:
                    self.stdout.write('Ingesting customer data synchronously...')
                    result = ingest_customer_data(customer_file)
                    self.stdout.write(self.style.SUCCESS(f'Customer data ingestion result: {result}'))
                else:
                    self.stdout.write('Queuing customer data ingestion task...')
                    task = ingest_customer_data.delay(customer_file)
                    self.stdout.write(self.style.SUCCESS(f'Customer task queued with ID: {task.id}'))
        
        if not customers_only:
            self.stdout.write(f'Loan data file: {loan_file}')
            if not os.path.exists(loan_file):
                self.stdout.write(self.style.ERROR(f'Loan file not found: {loan_file}'))
            else:
                if sync_mode:
                    self.stdout.write('Ingesting loan data synchronously...')
                    result = ingest_loan_data(loan_file)
                    self.stdout.write(self.style.SUCCESS(f'Loan data ingestion result: {result}'))
                else:
                    self.stdout.write('Queuing loan data ingestion task...')
                    task = ingest_loan_data.delay(loan_file)
                    self.stdout.write(self.style.SUCCESS(f'Loan task queued with ID: {task.id}'))
        
        self.stdout.write(self.style.SUCCESS('Data ingestion process initiated!'))
