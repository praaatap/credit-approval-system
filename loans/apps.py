"""
Loans app configuration.
"""

from django.apps import AppConfig


class LoansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'loans'
    verbose_name = 'Credit Approval System - Loans'
