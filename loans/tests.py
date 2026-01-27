"""
Unit tests for the Credit Approval System.

Tests cover:
    - Customer registration API
    - Loan eligibility checking
    - Loan creation
    - Credit score calculation
    - EMI calculation
"""

from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Customer, Loan
from .services import (
    calculate_credit_score,
    calculate_monthly_installment,
    check_loan_eligibility,
    create_loan
)


class EMICalculationTests(TestCase):
    """Tests for EMI calculation using compound interest."""
    
    def test_emi_calculation_basic(self):
        """Test basic EMI calculation."""
        # Loan of 100000 at 12% for 12 months
        emi = calculate_monthly_installment(100000, 12, 12)
        # Expected EMI around 8884.88
        self.assertAlmostEqual(emi, 8884.88, places=0)
    
    def test_emi_calculation_zero_interest(self):
        """Test EMI with zero interest rate."""
        emi = calculate_monthly_installment(120000, 0, 12)
        self.assertEqual(emi, 10000.0)
    
    def test_emi_calculation_large_loan(self):
        """Test EMI for a large loan amount."""
        emi = calculate_monthly_installment(1000000, 10, 60)
        self.assertGreater(emi, 0)
        # Total repayment should be greater than principal for non-zero interest
        total_repayment = emi * 60
        self.assertGreater(total_repayment, 1000000)


class CustomerModelTests(TestCase):
    """Tests for Customer model."""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number=9876543210,
            monthly_salary=Decimal("50000.00"),
            approved_limit=Decimal("1800000.00"),
            current_debt=Decimal("0.00")
        )
    
    def test_customer_creation(self):
        """Test customer is created correctly."""
        self.assertEqual(self.customer.first_name, "John")
        self.assertEqual(self.customer.last_name, "Doe")
        self.assertIsNotNone(self.customer.customer_id)
    
    def test_customer_full_name(self):
        """Test full_name property."""
        self.assertEqual(self.customer.full_name, "John Doe")
    
    def test_customer_str(self):
        """Test string representation."""
        self.assertIn("John Doe", str(self.customer))


class LoanModelTests(TestCase):
    """Tests for Loan model."""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Jane",
            last_name="Smith",
            phone_number=9876543211,
            monthly_salary=Decimal("60000.00"),
            approved_limit=Decimal("2000000.00")
        )
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal("100000.00"),
            tenure=12,
            interest_rate=Decimal("12.00"),
            monthly_repayment=Decimal("8884.88"),
            emis_paid_on_time=6,
            start_date=date.today() - timedelta(days=180),
            end_date=date.today() + timedelta(days=180)
        )
    
    def test_loan_creation(self):
        """Test loan is created correctly."""
        self.assertEqual(self.loan.customer, self.customer)
        self.assertEqual(self.loan.tenure, 12)
    
    def test_loan_is_active(self):
        """Test is_active property for active loan."""
        self.assertTrue(self.loan.is_active)
    
    def test_repayments_left(self):
        """Test repayments_left calculation."""
        self.assertGreaterEqual(self.loan.repayments_left, 0)
        self.assertLessEqual(self.loan.repayments_left, 12)


class CreditScoreTests(TestCase):
    """Tests for credit score calculation."""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="User",
            phone_number=9876543212,
            monthly_salary=Decimal("70000.00"),
            approved_limit=Decimal("2500000.00")
        )
    
    def test_credit_score_no_loans(self):
        """Test credit score for customer with no loans."""
        score = calculate_credit_score(self.customer)
        self.assertEqual(score, 50)  # Default score for no history
    
    def test_credit_score_with_good_history(self):
        """Test credit score for customer with good loan history."""
        # Create a loan with good repayment history
        Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal("100000.00"),
            tenure=12,
            interest_rate=Decimal("10.00"),
            monthly_repayment=Decimal("8792.00"),
            emis_paid_on_time=12,
            start_date=date.today() - timedelta(days=365),
            end_date=date.today() - timedelta(days=1)
        )
        score = calculate_credit_score(self.customer)
        self.assertGreater(score, 50)
    
    def test_credit_score_over_limit(self):
        """Test credit score is 0 when loans exceed approved limit."""
        # Create loans exceeding approved limit
        Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal("3000000.00"),  # Exceeds 2500000 limit
            tenure=60,
            interest_rate=Decimal("10.00"),
            monthly_repayment=Decimal("63741.00"),
            emis_paid_on_time=0,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1800)
        )
        score = calculate_credit_score(self.customer)
        self.assertEqual(score, 0)


class CustomerRegistrationAPITests(APITestCase):
    """Tests for customer registration API."""
    
    def test_register_customer_success(self):
        """Test successful customer registration."""
        data = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "age": 28,
            "monthly_income": 50000,
            "phone_number": 9876543213
        }
        response = self.client.post('/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('customer_id', response.data)
        self.assertEqual(response.data['name'], "Alice Johnson")
        # Approved limit should be 36 * 50000 = 1800000
        self.assertEqual(response.data['approved_limit'], 1800000)
    
    def test_register_customer_missing_fields(self):
        """Test registration with missing fields."""
        data = {
            "first_name": "Bob"
        }
        response = self.client.post('/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_register_customer_invalid_age(self):
        """Test registration with invalid age."""
        data = {
            "first_name": "Charlie",
            "last_name": "Brown",
            "age": 10,  # Under 18
            "monthly_income": 50000,
            "phone_number": 9876543214
        }
        response = self.client.post('/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CheckEligibilityAPITests(APITestCase):
    """Tests for loan eligibility API."""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="Customer",
            age=30,
            phone_number=9876543215,
            monthly_salary=Decimal("100000.00"),
            approved_limit=Decimal("3600000.00")
        )
    
    def test_check_eligibility_approved(self):
        """Test eligibility check for approvable loan."""
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 100000,
            "interest_rate": 12,
            "tenure": 12
        }
        response = self.client.post('/check-eligibility', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('approval', response.data)
        self.assertIn('monthly_installment', response.data)
    
    def test_check_eligibility_customer_not_found(self):
        """Test eligibility check for non-existent customer."""
        data = {
            "customer_id": 99999,
            "loan_amount": 100000,
            "interest_rate": 12,
            "tenure": 12
        }
        response = self.client.post('/check-eligibility', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreateLoanAPITests(APITestCase):
    """Tests for loan creation API."""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Loan",
            last_name="Tester",
            age=35,
            phone_number=9876543216,
            monthly_salary=Decimal("80000.00"),
            approved_limit=Decimal("2800000.00")
        )
    
    def test_create_loan_success(self):
        """Test successful loan creation."""
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 100000,
            "interest_rate": 12,
            "tenure": 12
        }
        response = self.client.post('/create-loan', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if response.data['loan_approved']:
            self.assertIsNotNone(response.data['loan_id'])
            # Verify loan was created in database
            loan = Loan.objects.get(loan_id=response.data['loan_id'])
            self.assertEqual(loan.customer, self.customer)


class ViewLoanAPITests(APITestCase):
    """Tests for view loan APIs."""
    
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="View",
            last_name="Tester",
            age=40,
            phone_number=9876543217,
            monthly_salary=Decimal("90000.00"),
            approved_limit=Decimal("3200000.00")
        )
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal("200000.00"),
            tenure=24,
            interest_rate=Decimal("10.00"),
            monthly_repayment=Decimal("9217.00"),
            emis_paid_on_time=6,
            start_date=date.today() - timedelta(days=180),
            end_date=date.today() + timedelta(days=540)
        )
    
    def test_view_loan_success(self):
        """Test viewing a specific loan."""
        response = self.client.get(f'/view-loan/{self.loan.loan_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['loan_id'], self.loan.loan_id)
        self.assertIn('customer', response.data)
    
    def test_view_loan_not_found(self):
        """Test viewing non-existent loan."""
        response = self.client.get('/view-loan/99999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_view_loans_by_customer(self):
        """Test viewing all loans for a customer."""
        response = self.client.get(f'/view-loans/{self.customer.customer_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['loan_id'], self.loan.loan_id)
    
    def test_view_loans_customer_not_found(self):
        """Test viewing loans for non-existent customer."""
        response = self.client.get('/view-loans/99999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
