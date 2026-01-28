from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal
import django.core.validators

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('customer_id', models.AutoField(primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('age', models.PositiveIntegerField(blank=True, null=True)),
                ('phone_number', models.BigIntegerField()),
                ('monthly_salary', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('approved_limit', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('current_debt', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'customers',
                'ordering': ['customer_id'],
            },
        ),
        migrations.CreateModel(
            name='Loan',
            fields=[
                ('loan_id', models.AutoField(primary_key=True, serialize=False)),
                ('loan_amount', models.DecimalField(decimal_places=2, max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))])),
                ('tenure', models.PositiveIntegerField(help_text='Loan tenure in months')),
                ('interest_rate', models.DecimalField(decimal_places=2, help_text='Annual interest rate as percentage', max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('monthly_repayment', models.DecimalField(decimal_places=2, help_text='EMI amount', max_digits=15, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
                ('emis_paid_on_time', models.PositiveIntegerField(default=0, help_text='Number of EMIs paid on time')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loans', to='loans.customer')),
            ],
            options={
                'db_table': 'loans',
                'ordering': ['loan_id'],
            },
        ),
    ]
