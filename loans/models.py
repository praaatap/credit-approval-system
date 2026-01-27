"""
Models for the Credit Approval System.

Contains Customer and Loan models with all required attributes
as specified in the assignment.
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Customer(models.Model):
    """
    Customer model representing bank customers.
    
    Attributes:
        customer_id: Primary key, auto-generated or from Excel data
        first_name: Customer's first name
        last_name: Customer's last name
        age: Customer's age (optional for imported customers)
        phone_number: Customer's phone number
        monthly_salary: Monthly salary/income of the customer
        approved_limit: Credit limit approved for the customer
        current_debt: Current debt amount
    """
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(null=True, blank=True)
    phone_number = models.BigIntegerField()
    monthly_salary = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    approved_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    current_debt = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'customers'
        ordering = ['customer_id']

    def __str__(self):
        return f"{self.first_name} {self.last_name} (ID: {self.customer_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Loan(models.Model):
    """
    Loan model representing loans taken by customers.
    
    Attributes:
        loan_id: Primary key, auto-generated or from Excel data
        customer: Foreign key to Customer
        loan_amount: Principal amount of the loan
        tenure: Loan tenure in months
        interest_rate: Annual interest rate as percentage
        monthly_repayment: EMI amount
        emis_paid_on_time: Number of EMIs paid on time
        start_date: Loan start date
        end_date: Loan end date
    """
    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE,
        related_name='loans'
    )
    loan_amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    tenure = models.PositiveIntegerField(
        help_text="Loan tenure in months"
    )
    interest_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Annual interest rate as percentage"
    )
    monthly_repayment = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="EMI amount"
    )
    emis_paid_on_time = models.PositiveIntegerField(
        default=0,
        help_text="Number of EMIs paid on time"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loans'
        ordering = ['loan_id']

    def __str__(self):
        return f"Loan {self.loan_id} - {self.customer.full_name} - ₹{self.loan_amount}"

    @property
    def total_emis(self):
        """Total number of EMIs for this loan."""
        return self.tenure

    @property
    def emis_paid(self):
        """Calculate EMIs paid based on start date and current date."""
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        
        today = timezone.now().date()
        if today < self.start_date:
            return 0
        
        months_passed = relativedelta(today, self.start_date).months + \
                       relativedelta(today, self.start_date).years * 12
        return min(months_passed, self.tenure)

    @property
    def repayments_left(self):
        """Calculate remaining repayments."""
        return max(0, self.tenure - self.emis_paid)

    @property
    def is_active(self):
        """Check if loan is still active (has remaining EMIs)."""
        from django.utils import timezone
        return self.end_date >= timezone.now().date()
