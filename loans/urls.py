"""
URL configuration for the loans app.

API Endpoints:
    - POST /register: Register a new customer
    - POST /check-eligibility: Check loan eligibility
    - POST /create-loan: Create a new loan
    - GET /view-loan/<loan_id>: View loan details
    - GET /view-loans/<customer_id>: View all loans by customer
"""

from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register_customer, name='register'),
    path('check-eligibility', views.check_eligibility, name='check-eligibility'),
    path('create-loan', views.create_loan_view, name='create-loan'),
    path('view-loan/<int:loan_id>', views.view_loan, name='view-loan'),
    path('view-loans/<int:customer_id>', views.view_loans_by_customer, name='view-loans'),
]
