"""
Celery tasks for background data processing.

Contains tasks for:
    - Ingesting customer data from Excel
    - Ingesting loan data from Excel
"""

import os
from celery import shared_task
from django.conf import settings
from decimal import Decimal
import pandas as pd
from datetime import datetime


@shared_task(bind=True, max_retries=3)
def ingest_customer_data(self, file_path=None):
    """
    Ingest customer data from customer_data.xlsx using background worker.
    
    Expected columns:
        - customer_id
        - first_name
        - last_name
        - phone_number
        - monthly_salary
        - approved_limit
        - current_debt
    
    Args:
        file_path: Optional path to the Excel file
    
    Returns:
        Dictionary with ingestion results
    """
    from .models import Customer
    
    try:
        if file_path is None:
            file_path = os.path.join(settings.DATA_FILES_PATH, 'customer_data.xlsx')
        
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        created_count = 0
        updated_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Handle different possible column names
                customer_id = row.get('customer_id') or row.get('customer id')
                first_name = row.get('first_name') or row.get('first name', '')
                last_name = row.get('last_name') or row.get('last name', '')
                phone_number = row.get('phone_number') or row.get('phone number', 0)
                monthly_salary = row.get('monthly_salary') or row.get('monthly salary', 0)
                approved_limit = row.get('approved_limit') or row.get('approved limit', 0)
                current_debt = row.get('current_debt') or row.get('current debt', 0)
                
                # Clean values
                if pd.isna(phone_number):
                    phone_number = 0
                if pd.isna(monthly_salary):
                    monthly_salary = 0
                if pd.isna(approved_limit):
                    approved_limit = 0
                if pd.isna(current_debt):
                    current_debt = 0
                
                customer, created = Customer.objects.update_or_create(
                    customer_id=int(customer_id),
                    defaults={
                        'first_name': str(first_name) if not pd.isna(first_name) else '',
                        'last_name': str(last_name) if not pd.isna(last_name) else '',
                        'phone_number': int(phone_number),
                        'monthly_salary': Decimal(str(monthly_salary)),
                        'approved_limit': Decimal(str(approved_limit)),
                        'current_debt': Decimal(str(current_debt))
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index}: {str(e)}")
        
        return {
            'status': 'success',
            'created': created_count,
            'updated': updated_count,
            'errors': error_count,
            'error_details': errors[:10]  # Limit error details
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=60)
        return {'error': str(e)}


@shared_task(bind=True, max_retries=3)
def ingest_loan_data(self, file_path=None):
    """
    Ingest loan data from loan_data.xlsx using background worker.
    
    Expected columns:
        - customer_id
        - loan_id
        - loan_amount
        - tenure
        - interest_rate
        - monthly_repayment (emi)
        - EMIs_paid_on_time
        - start_date
        - end_date
    
    Args:
        file_path: Optional path to the Excel file
    
    Returns:
        Dictionary with ingestion results
    """
    from .models import Customer, Loan
    
    try:
        if file_path is None:
            file_path = os.path.join(settings.DATA_FILES_PATH, 'loan_data.xlsx')
        
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        created_count = 0
        updated_count = 0
        error_count = 0
        skipped_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Handle different possible column names
                customer_id = row.get('customer_id') or row.get('customer id')
                loan_id = row.get('loan_id') or row.get('loan id')
                loan_amount = row.get('loan_amount') or row.get('loan amount', 0)
                tenure = row.get('tenure', 12)
                interest_rate = row.get('interest_rate') or row.get('interest rate', 0)
                monthly_repayment = row.get('monthly_repayment') or row.get('monthly_repayment_(emi)') or row.get('emi', 0)
                emis_paid_on_time = row.get('emis_paid_on_time') or row.get('emis paid on time', 0)
                start_date = row.get('start_date') or row.get('start date')
                end_date = row.get('end_date') or row.get('end date')
                
                # Check if customer exists
                try:
                    customer = Customer.objects.get(customer_id=int(customer_id))
                except Customer.DoesNotExist:
                    skipped_count += 1
                    errors.append(f"Row {index}: Customer {customer_id} not found")
                    continue
                
                # Parse dates
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                elif hasattr(start_date, 'date'):
                    start_date = start_date.date() if hasattr(start_date, 'date') else start_date
                
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                elif hasattr(end_date, 'date'):
                    end_date = end_date.date() if hasattr(end_date, 'date') else end_date
                
                # Clean numeric values
                if pd.isna(loan_amount):
                    loan_amount = 0
                if pd.isna(tenure):
                    tenure = 12
                if pd.isna(interest_rate):
                    interest_rate = 0
                if pd.isna(monthly_repayment):
                    monthly_repayment = 0
                if pd.isna(emis_paid_on_time):
                    emis_paid_on_time = 0
                
                loan, created = Loan.objects.update_or_create(
                    loan_id=int(loan_id),
                    defaults={
                        'customer': customer,
                        'loan_amount': Decimal(str(loan_amount)),
                        'tenure': int(tenure),
                        'interest_rate': Decimal(str(interest_rate)),
                        'monthly_repayment': Decimal(str(monthly_repayment)),
                        'emis_paid_on_time': int(emis_paid_on_time),
                        'start_date': start_date,
                        'end_date': end_date
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Row {index}: {str(e)}")
        
        return {
            'status': 'success',
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': error_count,
            'error_details': errors[:10]  # Limit error details
        }
        
    except Exception as e:
        self.retry(exc=e, countdown=60)
        return {'error': str(e)}


@shared_task
def ingest_all_data():
    """
    Master task to ingest all data from Excel files.
    
    This task orchestrates the ingestion of both customer and loan data.
    Customer data is ingested first since loans depend on customers.
    """
    # First ingest customers
    customer_result = ingest_customer_data.delay()
    
    # Then ingest loans (will be queued and run after customers in sequence)
    # In a real scenario, you might want to use a chain or chord for dependencies
    loan_result = ingest_loan_data.delay()
    
    return {
        'customer_task_id': str(customer_result.id),
        'loan_task_id': str(loan_result.id)
    }
