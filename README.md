# 🏦 NeoBank - Modern Digital Banking Platform

Hey there! 👋 Welcome to **NeoBank**, a sleek Django-based digital banking application that I've been working on. This isn't just another banking app - it's a complete KYC-compliant signup system that handles everything from mobile verification to secure account creation.

## 🚀 What's This All About?

Think of NeoBank as your modern-day banking solution that takes the hassle out of account creation. Instead of filling out endless forms and waiting days for verification, users can complete their entire signup process in just 5 simple steps, all while maintaining the highest security standards.

## ✨ Key Features

### 🔐 **5-Step Secure Signup Process**
1. **Mobile Verification** - OTP-based phone number verification
2. **Personal Details** - Collect essential user information
3. **Aadhaar Verification** - Government ID verification with OTP
4. **PAN Verification** - Tax ID verification with OTP  
5. **PIN Setup** - Secure 6-digit PIN creation for account access

### 🛡️ **Security First**
- **OTP Verification** for all sensitive operations
- **Hashed PIN Storage** using SHA-256 (production-ready for bcrypt)
- **Session Management** with UUID-based tracking
- **Rate Limiting** to prevent brute force attacks
- **Data Masking** for sensitive information display

### 🎨 **Modern UI/UX**
- **Glassmorphism Design** with Tailwind CSS
- **Responsive Layout** that works on all devices
- **Smooth Animations** and transitions
- **Real-time Validation** and feedback
- **Progress Tracking** throughout the signup flow

## 🏗️ Technical Architecture

### **Backend (Django)**
- **Django 5.2.6** with custom user model
- **PostgreSQL** database (configurable via environment)
- **JSON API endpoints** for seamless frontend integration
- **Session-based state management** for multi-step forms
- **Admin-managed KYC records** for verification

### **Frontend**
- **Vanilla JavaScript** with modern ES6+ features
- **Tailwind CSS** for styling
- **AJAX-based** API communication
- **Progressive form validation**
- **Real-time OTP input handling**

### **Database Models**
- `CustomUser` - Extended user model with phone and KYC fields
- `SignupSession` - Tracks multi-step signup progress
- `AadhaarRecord` - Admin-managed Aadhaar verification data
- `PANRecord` - Admin-managed PAN verification data
- `KYCRecord` - Audit trail for all verification attempts
- `Account` - Basic account information

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (or SQLite for development)
- pip/virtualenv

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/neobank.git
cd neobank
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost:5432/neobank
```

5. **Database setup**
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. **Run the development server**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to see your NeoBank in action! 🎉

## 📱 How It Works

### The Signup Journey

1. **Step 1: Mobile Verification**
   - User enters their phone number
   - System generates a 6-digit OTP
   - OTP is displayed in console (demo mode)
   - User verifies OTP to proceed

2. **Step 2: Personal Details**
   - Collect full name, email, date of birth, gender
   - Real-time validation and formatting
   - Age verification (18+ required)

3. **Step 3: Aadhaar Verification**
   - User enters 12-digit Aadhaar number
   - System cross-verifies with admin-managed records
   - Name, DOB, and gender matching
   - OTP sent for final verification

4. **Step 4: PAN Verification**
   - User enters PAN number (format: ABCDE1234F)
   - Cross-verification with admin records
   - OTP-based final verification

5. **Step 5: PIN Setup**
   - User creates a 6-digit PIN
   - PIN confirmation and strength validation
   - Account creation with all collected data
   - Welcome to NeoBank! 🎉

### Admin Panel Features

The Django admin panel allows you to:
- **Manage Aadhaar Records** - Add pre-approved Aadhaar numbers for verification
- **Manage PAN Records** - Add pre-approved PAN numbers for verification
- **Monitor Signup Sessions** - Track user progress and troubleshoot issues
- **View KYC Records** - Audit trail of all verification attempts
- **User Management** - View and manage created accounts

## 🔧 Configuration

### Adding Test Data

To test the verification process, add some records in the admin panel:

**Aadhaar Records:**
- Aadhaar Number: `123456789012`
- Name: `John Doe`
- DOB: `1990-01-15`
- Gender: `M`

**PAN Records:**
- PAN Number: `ABCDE1234F`
- Name: `John Doe`
- DOB: `1990-01-15`

### Environment Variables

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/neobank
```

## 🛠️ Development

### Project Structure
```
neobank/
├── core/                 # Django project settings
├── users/               # Main app with models, views, URLs
├── templates/           # HTML templates
├── figma-signup-pages/  # Design mockups
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

### API Endpoints

All API endpoints return JSON responses:

- `POST /users/api/send-otp/` - Send OTP to phone
- `POST /users/api/verify-otp/` - Verify OTP code
- `POST /users/api/save-personal-details/` - Save personal info
- `POST /users/api/verify-aadhaar/` - Verify Aadhaar details
- `POST /users/api/verify-aadhaar-otp/` - Verify Aadhaar OTP
- `POST /users/api/verify-pan/` - Verify PAN details
- `POST /users/api/verify-pan-otp/` - Verify PAN OTP
- `POST /users/api/setup-pin/` - Create account with PIN

## 🔒 Security Considerations

This is a **demo/learning project**. For production use, consider:

- **OTP Storage**: Use Redis with hashed OTPs instead of database storage
- **PIN Hashing**: Implement bcrypt or Argon2 for PIN hashing
- **Rate Limiting**: Add proper rate limiting middleware
- **CSRF Protection**: Remove `@csrf_exempt` decorators
- **HTTPS**: Always use HTTPS in production
- **Data Encryption**: Encrypt sensitive data at rest
- **Audit Logging**: Implement comprehensive audit trails

## 🤝 Contributing

I'd love to see this project grow! Here's how you can contribute:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Ideas for Contributions
- Add biometric authentication
- Implement account balance management
- Add transaction history
- Create mobile app version
- Add multi-language support
- Implement advanced security features

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **Django** for the amazing web framework
- **Tailwind CSS** for the beautiful styling
- **Inter Font** for the clean typography
- **All contributors** who help make this project better

## 📞 Support

Having issues? Here's how to get help:

1. **Check the Issues** - Look through existing GitHub issues
2. **Create a New Issue** - Describe your problem with details
3. **Join Discussions** - Use GitHub Discussions for questions
4. **Email Support** - For urgent matters, reach out directly

---

**Built with ❤️ for the future of digital banking**

*This project demonstrates modern web development practices, security best practices, and user experience design in the fintech space. Perfect for learning Django, understanding KYC processes, and building production-ready applications.*
