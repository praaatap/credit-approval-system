"""
Business logic services for the Credit Approval System.

Contains:
- Credit score calculation
- Loan eligibility checking
- EMI calculation using compound interest
"""

from decimal import Decimal
from datetime import date
from django.db.models import Sum
from django.utils import timezone

from .models import Customer, Loan


def calculate_monthly_installment(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Calculate EMI using compound interest formula.
    
    EMI = [P x R x (1+R)^N] / [(1+R)^N - 1]
    
    Where:
        P = Principal loan amount
        R = Monthly interest rate (annual rate / 12 / 100)
        N = Number of monthly installments (tenure)
    
    Args:
        principal: Loan principal amount
        annual_rate: Annual interest rate as percentage
        tenure_months: Loan tenure in months
    
    Returns:
        Monthly EMI amount
    """
    if annual_rate == 0:
        return principal / tenure_months
    
    monthly_rate = annual_rate / 12 / 100
    
    # EMI formula
    emi = (principal * monthly_rate * ((1 + monthly_rate) ** tenure_months)) / \
          (((1 + monthly_rate) ** tenure_months) - 1)
    
    return round(emi, 2)


def calculate_credit_score(customer: Customer) -> int:
    """
    Calculate credit score for a customer out of 100.
    
    Components considered:
        i. Past Loans paid on time
        ii. No of loans taken in past
        iii. Loan activity in current year
        iv. Loan approved volume
        v. If sum of current loans > approved limit, credit score = 0
    
    Args:
        customer: Customer instance
    
    Returns:
        Credit score out of 100
    """
    loans = Loan.objects.filter(customer=customer)
    
    if not loans.exists():
        # No loan history - give a moderate score
        return 50
    
    today = timezone.now().date()
    current_year = today.year
    
    # Get all loans and active loans
    all_loans = list(loans)
    active_loans = [loan for loan in all_loans if loan.end_date >= today]
    
    # Calculate sum of current loan amounts
    current_loan_sum = sum(float(loan.loan_amount) for loan in active_loans)
    approved_limit = float(customer.approved_limit)
    
    # Rule v: If sum of current loans > approved limit, credit score = 0
    if current_loan_sum > approved_limit:
        return 0
    
    score = 0
    
    # Component i: Past Loans paid on time (max 35 points)
    total_emis = sum(loan.emis_paid_on_time for loan in all_loans)
    total_expected_emis = sum(loan.tenure for loan in all_loans)
    
    if total_expected_emis > 0:
        on_time_ratio = total_emis / total_expected_emis
        score += int(on_time_ratio * 35)
    else:
        score += 25  # Default if no EMI history
    
    # Component ii: No of loans taken in past (max 20 points)
    # More loans with good repayment = higher score
    num_loans = len(all_loans)
    if num_loans >= 5:
        score += 20
    elif num_loans >= 3:
        score += 15
    elif num_loans >= 1:
        score += 10
    
    # Component iii: Loan activity in current year (max 20 points)
    current_year_loans = [
        loan for loan in all_loans 
        if loan.start_date.year == current_year
    ]
    if len(current_year_loans) == 0:
        score += 20  # No new loans this year - stable
    elif len(current_year_loans) <= 2:
        score += 15  # Moderate activity
    elif len(current_year_loans) <= 4:
        score += 10  # High activity
    else:
        score += 5   # Very high activity - risky
    
    # Component iv: Loan approved volume (max 25 points)
    total_loan_volume = sum(float(loan.loan_amount) for loan in all_loans)
    if approved_limit > 0:
        volume_ratio = total_loan_volume / approved_limit
        if volume_ratio <= 0.3:
            score += 25  # Low utilization - good
        elif volume_ratio <= 0.5:
            score += 20
        elif volume_ratio <= 0.7:
            score += 15
        elif volume_ratio <= 1.0:
            score += 10
        else:
            score += 5  # Over limit at some point
    else:
        score += 15  # Default
    
    # Ensure score is within 0-100
    return max(0, min(100, score))


def check_loan_eligibility(customer: Customer, loan_amount: float, 
                           interest_rate: float, tenure: int) -> dict:
    """
    Check if a customer is eligible for a loan.
    
    Eligibility rules based on credit score:
        - If credit_rating > 50, approve loan
        - If 50 > credit_rating > 30, approve loans with interest rate > 12%
        - If 30 > credit_rating > 10, approve loans with interest rate > 16%
        - If 10 > credit_rating, don't approve any loans
        - If sum of all current EMIs > 50% of monthly salary, don't approve
    
    Args:
        customer: Customer instance
        loan_amount: Requested loan amount
        interest_rate: Requested interest rate
        tenure: Loan tenure in months
    
    Returns:
        Dictionary with eligibility details
    """
    credit_score = calculate_credit_score(customer)
    monthly_salary = float(customer.monthly_salary)
    
    # Get current EMIs
    today = timezone.now().date()
    active_loans = Loan.objects.filter(customer=customer, end_date__gte=today)
    current_total_emi = sum(float(loan.monthly_repayment) for loan in active_loans)
    
    # Calculate EMI for new loan
    new_emi = calculate_monthly_installment(loan_amount, interest_rate, tenure)
    total_emi_after_loan = current_total_emi + new_emi
    
    # Initialize response
    approval = False
    corrected_interest_rate = interest_rate
    message = ""
    
    # Rule: If sum of all current EMIs > 50% of monthly salary, don't approve
    if total_emi_after_loan > (0.5 * monthly_salary):
        return {
            'customer_id': customer.customer_id,
            'approval': False,
            'interest_rate': interest_rate,
            'corrected_interest_rate': interest_rate,
            'tenure': tenure,
            'monthly_installment': new_emi,
            'message': 'Total EMIs would exceed 50% of monthly salary'
        }
    
    # Apply credit score rules
    if credit_score > 50:
        # Approve loan at requested rate
        approval = True
        corrected_interest_rate = interest_rate
        message = "Loan approved"
    elif 30 < credit_score <= 50:
        # Approve only if interest rate > 12%
        if interest_rate > 12:
            approval = True
            corrected_interest_rate = interest_rate
            message = "Loan approved"
        else:
            approval = True
            corrected_interest_rate = 12.0
            message = "Loan approved with corrected interest rate"
            new_emi = calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure)
    elif 10 < credit_score <= 30:
        # Approve only if interest rate > 16%
        if interest_rate > 16:
            approval = True
            corrected_interest_rate = interest_rate
            message = "Loan approved"
        else:
            approval = True
            corrected_interest_rate = 16.0
            message = "Loan approved with corrected interest rate"
            new_emi = calculate_monthly_installment(loan_amount, corrected_interest_rate, tenure)
    else:
        # credit_score <= 10, don't approve
        approval = False
        corrected_interest_rate = interest_rate
        message = "Loan not approved due to low credit score"
    
    return {
        'customer_id': customer.customer_id,
        'approval': approval,
        'interest_rate': interest_rate,
        'corrected_interest_rate': corrected_interest_rate,
        'tenure': tenure,
        'monthly_installment': new_emi,
        'message': message
    }


def create_loan(customer: Customer, loan_amount: float, 
                interest_rate: float, tenure: int) -> dict:
    """
    Process and create a new loan based on eligibility.
    
    Args:
        customer: Customer instance
        loan_amount: Requested loan amount
        interest_rate: Requested interest rate
        tenure: Loan tenure in months
    
    Returns:
        Dictionary with loan creation response
    """
    # Check eligibility first
    eligibility = check_loan_eligibility(customer, loan_amount, interest_rate, tenure)
    
    if not eligibility['approval']:
        return {
            'loan_id': None,
            'customer_id': customer.customer_id,
            'loan_approved': False,
            'message': eligibility['message'],
            'monthly_installment': eligibility['monthly_installment']
        }
    
    # Create the loan
    from datetime import timedelta
    from dateutil.relativedelta import relativedelta
    
    today = timezone.now().date()
    end_date = today + relativedelta(months=tenure)
    
    final_interest_rate = eligibility['corrected_interest_rate']
    monthly_installment = eligibility['monthly_installment']
    
    loan = Loan.objects.create(
        customer=customer,
        loan_amount=Decimal(str(loan_amount)),
        tenure=tenure,
        interest_rate=Decimal(str(final_interest_rate)),
        monthly_repayment=Decimal(str(monthly_installment)),
        emis_paid_on_time=0,
        start_date=today,
        end_date=end_date
    )
    
    # Update customer's current debt
    customer.current_debt += Decimal(str(loan_amount))
    customer.save()
    
    return {
        'loan_id': loan.loan_id,
        'customer_id': customer.customer_id,
        'loan_approved': True,
        'message': eligibility['message'],
        'monthly_installment': monthly_installment
    }
