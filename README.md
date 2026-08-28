# FinWise - Personal Finance Tracker

FinWise is a web-based personal finance tracker that helps users manage their income, expenses, and budgets. The application provides a personalized dashboard to help users understand their spending patterns and monitor their financial activity.

## Features

- User registration and login
- Secure password hashing
- Session-based user authentication
- Add income and expense transactions
- Categorize financial transactions
- Set category-wise budgets
- Track total income and expenses
- Calculate available balance
- View recent transactions
- Monitor spending against budgets
- Budget exceeded alerts
- Personalized spending insights
- Identify the highest spending category
- User logout functionality

## Technologies Used

- Python
- Flask
- SQLite
- HTML
- CSS
- Git
- GitHub

## Database Structure

The application uses SQLite with the following tables:

### Users

Stores user information including:

- User ID
- Full name
- Email
- Hashed password

### Transactions

Stores financial transactions including:

- Transaction type
- Amount
- Category
- Description
- Date
- User ID

### Budgets

Stores category-wise budget information for users.

## Project Structure

```text
FinWise-Personal-Finance-Tracker/
│
├── app.py
├── README.md
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    ├── index.html
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── transaction.html
    └── budget.html
