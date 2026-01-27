"""
Serializers for the Credit Approval System API.

Contains serializers for Customer and Loan models with
request/response handling as per assignment specifications.
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Customer, Loan


class CustomerRegistrationSerializer(serializers.Serializer):
    """
    Serializer for customer registration request.
    
    Request fields:
        - first_name: First Name of customer (string)
        - last_name: Last Name of customer (string)
        - age: Age of customer (int)
        - monthly_income: Monthly income of individual (int)
        - phone_number: Phone number (int)
    """
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField(min_value=18, max_value=120)
    monthly_income = serializers.IntegerField(min_value=0)
    phone_number = serializers.IntegerField()

    def create(self, validated_data):
        """
        Create a new customer with approved limit based on salary.
        approved_limit = 36 * monthly_salary (rounded to nearest lakh)
        """
        monthly_salary = validated_data['monthly_income']
        
        # Calculate approved limit: 36 * monthly_salary, rounded to nearest lakh
        raw_limit = 36 * monthly_salary
        # Round to nearest lakh (100,000)
        approved_limit = round(raw_limit / 100000) * 100000
        
        customer = Customer.objects.create(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            age=validated_data['age'],
            phone_number=validated_data['phone_number'],
            monthly_salary=Decimal(monthly_salary),
            approved_limit=Decimal(approved_limit),
            current_debt=Decimal('0.00')
        )
        return customer


class CustomerRegistrationResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for customer registration response.
    
    Response fields:
        - customer_id: Id of customer (int)
        - name: Name of customer (string)
        - age: Age of customer (int)
        - monthly_income: Monthly income of individual (int)
        - approved_limit: Approved credit limit (int)
        - phone_number: Phone number (int)
    """
    name = serializers.SerializerMethodField()
    monthly_income = serializers.SerializerMethodField()
    approved_limit = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number']

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_monthly_income(self, obj):
        return int(obj.monthly_salary)

    def get_approved_limit(self, obj):
        return int(obj.approved_limit)


class CheckEligibilityRequestSerializer(serializers.Serializer):
    """
    Serializer for loan eligibility check request.
    
    Request fields:
        - customer_id: Id of customer (int)
        - loan_amount: Requested loan amount (float)
        - interest_rate: Interest rate on loan (float)
        - tenure: Tenure of loan (int)
    """
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField(min_value=0)
    interest_rate = serializers.FloatField(min_value=0)
    tenure = serializers.IntegerField(min_value=1)

    def validate_customer_id(self, value):
        if not Customer.objects.filter(customer_id=value).exists():
            raise serializers.ValidationError("Customer not found.")
        return value


class CheckEligibilityResponseSerializer(serializers.Serializer):
    """
    Serializer for loan eligibility check response.
    
    Response fields:
        - customer_id: Id of customer (int)
        - approval: Can loan be approved (bool)
        - interest_rate: Interest rate on loan (float)
        - corrected_interest_rate: Corrected Interest Rate based on credit rating (float)
        - tenure: Tenure of loan (int)
        - monthly_installment: Monthly installment to be paid as repayment (float)
    """
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField()


class CreateLoanRequestSerializer(serializers.Serializer):
    """
    Serializer for loan creation request.
    
    Request fields:
        - customer_id: Id of customer (int)
        - loan_amount: Requested loan amount (float)
        - interest_rate: Interest rate on loan (float)
        - tenure: Tenure of loan (int)
    """
    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField(min_value=0)
    interest_rate = serializers.FloatField(min_value=0)
    tenure = serializers.IntegerField(min_value=1)

    def validate_customer_id(self, value):
        if not Customer.objects.filter(customer_id=value).exists():
            raise serializers.ValidationError("Customer not found.")
        return value


class CreateLoanResponseSerializer(serializers.Serializer):
    """
    Serializer for loan creation response.
    
    Response fields:
        - loan_id: Id of approved loan, null otherwise (int)
        - customer_id: Id of customer (int)
        - loan_approved: Is the loan approved (bool)
        - message: Appropriate message if loan is not approved (string)
        - monthly_installment: Monthly installment to be paid as repayment (float)
    """
    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.FloatField()


class CustomerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for customer details in loan view response.
    """
    class Meta:
        model = Customer
        fields = ['customer_id', 'first_name', 'last_name', 'phone_number', 'age']
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Rename customer_id to id for the nested response
        data['id'] = data.pop('customer_id')
        return data


class ViewLoanResponseSerializer(serializers.Serializer):
    """
    Serializer for viewing single loan details response.
    
    Response fields:
        - loan_id: Id of approved loan (int)
        - customer: JSON containing id, first_name, last_name, phone_number, age of customer
        - loan_amount: Loan amount (float)
        - interest_rate: Interest rate of the approved loan (float)
        - monthly_installment: Monthly installment to be paid as repayment (float)
        - tenure: Tenure of loan (int)
    """
    loan_id = serializers.IntegerField()
    customer = CustomerDetailSerializer()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    monthly_installment = serializers.FloatField()
    tenure = serializers.IntegerField()


class ViewLoansItemSerializer(serializers.Serializer):
    """
    Serializer for individual loan item in customer's loans list.
    
    Response fields:
        - loan_id: Id of approved loan (int)
        - loan_amount: Loan amount (float)
        - interest_rate: Interest rate of the approved loan (float)
        - monthly_installment: Monthly installment to be paid as repayment (float)
        - repayments_left: No of EMIs left (int)
    """
    loan_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    monthly_installment = serializers.FloatField()
    repayments_left = serializers.IntegerField()
