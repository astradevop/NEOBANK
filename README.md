# NeoBank - Modern Banking Application

A full-featured Django-based neobanking application with secure multi-step signup, KYC verification, and a modern dashboard interface.

## 🚀 Features

### Core Functionality
- **Multi-Step Signup Process** - Secure 5-step account creation with OTP verification
- **KYC Verification** - Aadhaar and PAN verification with OTP
- **Customer Management** - Unique 5-digit customer ID system
- **Account Management** - Bank account creation with account numbers
- **Modern Dashboard** - Beautiful, responsive dashboard with financial metrics
- **Secure Authentication** - Mobile + PIN based login system

### Security Features
- **Session Management** - 30-minute banking session timeout with activity extension
- **OTP Verification** - Multi-level OTP verification for mobile, Aadhaar, and PAN
- **Secure Sessions** - HttpOnly cookies, SameSite protection
- **Data Masking** - Sensitive data (Aadhaar, PAN) masked for display

## 📋 Tech Stack

- **Backend**: Django 5.2.7
- **Database**: PostgreSQL (Supabase)
- **Frontend**: Tailwind CSS, Lucide Icons
- **Authentication**: Custom User Model with Mobile + PIN

## 🏗️ Project Structure

```
neobank/
├── accounts/          # User accounts and authentication
│   ├── models.py      # CustomUser, Account, SignupProgress
│   ├── views.py       # Signup flow (5 steps), Login, Logout
│   ├── forms.py       # Form validation for all signup steps
│   └── utils.py       # OTP generation, verification helpers
├── core/              # Django project settings
│   ├── settings.py    # Application configuration
│   └── urls.py        # URL routing
├── dashboard/         # User dashboard
│   ├── views.py       # Dashboard home view
│   ├── models.py      # UserPreference model
│   └── templates/     # Dashboard templates
└── templates/         # Base templates
```

## 🔐 Signup Process

1. **Step 1: Mobile Verification** - OTP sent to mobile number
2. **Step 2: Personal Details** - Name, email, DOB, gender
3. **Step 3: Aadhaar Verification** - Aadhaar number + address + OTP
4. **Step 4: PAN Verification** - PAN number + OTP
5. **Step 5: PIN Setup** - 6-digit PIN creation + account creation

## ⚙️ Installation

### Prerequisites
- Python 3.12+
- PostgreSQL database
- pip

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/astradevop/NEOBANK.git
cd NEOBANK
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install django python-decouple psycopg2-binary
```

4. **Configure environment variables**
Create a `.env` file:
```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host
DB_PORT=5432
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Create superuser**
```bash
python manage.py createsuperuser
```

7. **Run development server**
```bash
python manage.py runserver
```

## 🔑 Key Models

### CustomUser
- Mobile number (unique, used for login)
- Email, full name, DOB, gender
- Aadhaar number, PAN number
- Customer ID (5-digit unique identifier)
- Account status, credit score
- PIN (6-digit)

### Account
- Account number (10-digit unique)
- Balance
- Account type
- Linked to CustomUser

### SignupProgress
- Tracks multi-step signup state
- Session-based progress tracking
- 30-minute expiry

## 🎨 Dashboard Features

- **Account Overview** - Balance, spending, savings rate
- **Credit Score** - Display with rating
- **Financial Health Score** - Overall financial wellness
- **Account Summary** - Main account and savings pot
- **User Preferences** - Show/hide balance and credit score

## 🔒 Security Settings

- **Session Timeout**: 30 minutes of inactivity
- **Activity Extension**: Sessions extend on each request
- **Signup Expiry**: 30 minutes for incomplete signups
- **Cookie Security**: HttpOnly, SameSite=Strict

## 📝 Admin Panel

Access admin at `/admin/` with superuser credentials.

Features:
- Search by Customer ID, mobile, email
- Filter by account status
- View all user and account details
- Manage user accounts

## 🧪 Testing

```bash
python manage.py test
```

## 📄 License

This project is private and proprietary.

## 👤 Author

**astradevop**

## 🙏 Acknowledgments

- Django Framework
- Tailwind CSS
- Supabase for PostgreSQL hosting

---

**Note**: This is a development project. Ensure proper security measures before production deployment.

