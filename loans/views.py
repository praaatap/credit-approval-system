"""
API Views for the Credit Approval System.

Endpoints:
    - /register: Register a new customer
    - /check-eligibility: Check loan eligibility
    - /create-loan: Create a new loan
    - /view-loan/<loan_id>: View loan details
    - /view-loans/<customer_id>: View all loans by customer
"""

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Customer, Loan
from .serializers import (
    CustomerRegistrationSerializer,
    CustomerRegistrationResponseSerializer,
    CheckEligibilityRequestSerializer,
    CheckEligibilityResponseSerializer,
    CreateLoanRequestSerializer,
    CreateLoanResponseSerializer,
    ViewLoanResponseSerializer,
    ViewLoansItemSerializer,
    CustomerDetailSerializer
)
from .services import (
    check_loan_eligibility,
    create_loan,
    calculate_monthly_installment
)


@api_view(['POST'])
def register_customer(request):
    """
    Register a new customer.
    
    POST /register
    
    Request body:
        - first_name: First Name of customer (string)
        - last_name: Last Name of customer (string)
        - age: Age of customer (int)
        - monthly_income: Monthly income of individual (int)
        - phone_number: Phone number (int)
    
    Returns:
        Customer registration response with approved limit
    """
    serializer = CustomerRegistrationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        customer = serializer.save()
        response_serializer = CustomerRegistrationResponseSerializer(customer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response(
            {'error': 'Failed to register customer', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def check_eligibility(request):
    """
    Check loan eligibility for a customer.
    
    POST /check-eligibility
    
    Request body:
        - customer_id: Id of customer (int)
        - loan_amount: Requested loan amount (float)
        - interest_rate: Interest rate on loan (float)
        - tenure: Tenure of loan (int)
    
    Returns:
        Loan eligibility response with approval status and corrected interest rate
    """
    serializer = CheckEligibilityRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        customer = get_object_or_404(
            Customer, 
            customer_id=serializer.validated_data['customer_id']
        )
        
        result = check_loan_eligibility(
            customer=customer,
            loan_amount=serializer.validated_data['loan_amount'],
            interest_rate=serializer.validated_data['interest_rate'],
            tenure=serializer.validated_data['tenure']
        )
        
        response_serializer = CheckEligibilityResponseSerializer(data=result)
        if response_serializer.is_valid():
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to check eligibility', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_loan_view(request):
    """
    Create a new loan for a customer.
    
    POST /create-loan
    
    Request body:
        - customer_id: Id of customer (int)
        - loan_amount: Requested loan amount (float)
        - interest_rate: Interest rate on loan (float)
        - tenure: Tenure of loan (int)
    
    Returns:
        Loan creation response with loan_id if approved
    """
    serializer = CreateLoanRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        customer = get_object_or_404(
            Customer, 
            customer_id=serializer.validated_data['customer_id']
        )
        
        result = create_loan(
            customer=customer,
            loan_amount=serializer.validated_data['loan_amount'],
            interest_rate=serializer.validated_data['interest_rate'],
            tenure=serializer.validated_data['tenure']
        )
        
        response_serializer = CreateLoanResponseSerializer(data=result)
        if response_serializer.is_valid():
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to create loan', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def view_loan(request, loan_id):
    """
    View details of a specific loan.
    
    GET /view-loan/<loan_id>
    
    Returns:
        Loan details with customer information
    """
    try:
        loan = get_object_or_404(Loan, loan_id=loan_id)
        
        response_data = {
            'loan_id': loan.loan_id,
            'customer': CustomerDetailSerializer(loan.customer).data,
            'loan_amount': float(loan.loan_amount),
            'interest_rate': float(loan.interest_rate),
            'monthly_installment': float(loan.monthly_repayment),
            'tenure': loan.tenure
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Loan.DoesNotExist:
        return Response(
            {'error': 'Loan not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve loan', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def view_loans_by_customer(request, customer_id):
    """
    View all loans for a specific customer.
    
    GET /view-loans/<customer_id>
    
    Returns:
        List of all loans for the customer
    """
    try:
        customer = get_object_or_404(Customer, customer_id=customer_id)
        loans = Loan.objects.filter(customer=customer)
        
        response_data = []
        for loan in loans:
            loan_data = {
                'loan_id': loan.loan_id,
                'loan_amount': float(loan.loan_amount),
                'interest_rate': float(loan.interest_rate),
                'monthly_installment': float(loan.monthly_repayment),
                'repayments_left': loan.repayments_left
            }
            response_data.append(loan_data)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Customer.DoesNotExist:
        return Response(
            {'error': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Failed to retrieve loans', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
