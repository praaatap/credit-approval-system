# Credit Approval System

A Django-based Credit Approval System API that manages customer loans, calculates credit scores, and processes loan applications.

## 🚀 Features

- **Customer Registration**: Register new customers with auto-calculated credit limits
- **Credit Score Calculation**: Dynamic credit scoring based on loan history
- **Loan Eligibility Check**: Check if a customer qualifies for a loan
- **Loan Processing**: Create and manage loans
- **Background Data Ingestion**: Celery-based Excel data import
- **API Documentation**: Interactive Swagger UI at `/docs` and ReDoc at `/redoc`

## 🛠️ Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL 15
- **Message Broker**: Redis 7
- **Task Queue**: Celery 5.2
- **Containerization**: Docker & Docker Compose

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register` | POST | Register a new customer |
| `/check-eligibility` | POST | Check loan eligibility |
| `/create-loan` | POST | Create a new loan |
| `/view-loan/<loan_id>` | GET | View loan details |
| `/view-loans/<customer_id>` | GET | View all loans by customer |
| `/docs` | GET | Interactive API Documentation (Swagger) |
| `/redoc` | GET | Static API Documentation (ReDoc) |

## 🏃 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd credit_approval_system
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the API**
   - API: http://localhost:8000
   - Admin: http://localhost:8000/admin

The application will automatically:
- Set up PostgreSQL database
- Run migrations
- Ingest data from Excel files (customer_data.xlsx & loan_data.xlsx)
- Start the development server

### API Usage Examples

#### 1. Register a Customer

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "age": 30,
    "monthly_income": 50000,
    "phone_number": 9876543210
  }'
```

**Response:**
```json
{
  "customer_id": 1,
  "name": "John Doe",
  "age": 30,
  "monthly_income": 50000,
  "approved_limit": 1800000,
  "phone_number": 9876543210
}
```

#### 2. Check Loan Eligibility

```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 100000,
    "interest_rate": 12,
    "tenure": 12
  }'
```

**Response:**
```json
{
  "customer_id": 1,
  "approval": true,
  "interest_rate": 12,
  "corrected_interest_rate": 12,
  "tenure": 12,
  "monthly_installment": 8884.88
}
```

#### 3. Create a Loan

```bash
curl -X POST http://localhost:8000/create-loan \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 100000,
    "interest_rate": 12,
    "tenure": 12
  }'
```

**Response:**
```json
{
  "loan_id": 1,
  "customer_id": 1,
  "loan_approved": true,
  "message": "Loan approved",
  "monthly_installment": 8884.88
}
```

#### 4. View Loan Details

```bash
curl http://localhost:8000/view-loan/1
```

**Response:**
```json
{
  "loan_id": 1,
  "customer": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": 9876543210,
    "age": 30
  },
  "loan_amount": 100000,
  "interest_rate": 12,
  "monthly_installment": 8884.88,
  "tenure": 12
}
```

#### 5. View All Customer Loans

```bash
curl http://localhost:8000/view-loans/1
```

**Response:**
```json
[
  {
    "loan_id": 1,
    "loan_amount": 100000,
    "interest_rate": 12,
    "monthly_installment": 8884.88,
    "repayments_left": 10
  }
]
```

## 📊 Credit Score Calculation

The credit score (0-100) is calculated based on:

1. **Past Loans Paid on Time** (35 points max)
2. **Number of Loans Taken** (20 points max)
3. **Loan Activity in Current Year** (20 points max)
4. **Loan Approved Volume** (25 points max)

**Special Rule**: If the sum of current loans exceeds the approved limit, credit score = 0

## 📋 Loan Approval Rules

| Credit Score | Approval Condition |
|--------------|-------------------|
| > 50 | Approve at requested rate |
| 30-50 | Approve only if interest rate > 12% |
| 10-30 | Approve only if interest rate > 16% |
| < 10 | Reject all loans |

**Additional Rule**: If total EMIs > 50% of monthly salary, loan is rejected

## 🧪 Running Tests

```bash
# Inside the container
docker-compose exec web python manage.py test loans

# Or locally
python manage.py test loans
```

## 📁 Project Structure

```
credit_approval_system/
├── config/                 # Django project configuration
│   ├── __init__.py
│   ├── celery.py          # Celery configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py
├── loans/                  # Main application
│   ├── management/
│   │   └── commands/
│   │       └── ingest_data.py  # Data ingestion command
│   ├── admin.py           # Admin configuration
│   ├── models.py          # Customer and Loan models
│   ├── serializers.py     # API serializers
│   ├── services.py        # Business logic (credit score, EMI)
│   ├── tasks.py           # Celery background tasks
│   ├── tests.py           # Unit tests
│   ├── urls.py            # API endpoints
│   └── views.py           # API views
├── docker-compose.yml      # Docker services configuration
├── Dockerfile              # Application container
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `1` |
| `SECRET_KEY` | Django secret key | (provided) |
| `POSTGRES_NAME` | Database name | `credit_approval_db` |
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `POSTGRES_HOST` | Database host | `db` |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` |

## 📝 Notes

- The approved limit is calculated as: `36 × monthly_salary` (rounded to nearest lakh)
- EMI is calculated using the compound interest formula
- Data from Excel files is automatically ingested on startup
- All API responses include appropriate HTTP status codes

## 👤 Author

Built as part of a Backend Internship Assignment.
