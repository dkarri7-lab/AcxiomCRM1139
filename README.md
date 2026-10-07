# AcxiomCRM - Enterprise Sales & CRM System

A full-featured, role-based Customer Relationship Management (CRM) web application built with **Python 3**, **Flask**, **SQLite**, **Bootstrap 5**, **Chart.js**, and **REST APIs**.

---

## 🌟 Features Overview

- **🔐 Authentication & Security**:
  - Secure password hashing using Werkzeug.
  - Configurable Password Policy (min 8 chars, uppercase, lowercase, digit, special character).
  - Account Lockout protection (5 failed login attempts locks account for 15 minutes).
  - Role-based Access Control (`Admin`, `Manager`, `SalesExecutive`).
- **📊 Interactive Dashboard**:
  - Role-scoped KPI cards (Total Customers, Open Leads, Pipeline Value, Pending Follow-ups).
  - Interactive Chart.js graphs (Lead Status breakdown, Opportunity Pipeline by stage).
- **💼 CRM Core Workflows**:
  - **Customer Management**: Complete CRUD, search, filter, email/phone uniqueness validation.
  - **Lead Lifecycle**: Prospect capture, qualification, and 1-click **Lead Conversion** into Customer & Opportunity.
  - **Opportunity Pipeline**: Stage tracking, weighted pipeline calculations ($Amount \times Probability / 100$), close date validation.
  - **Follow-Up Planner**: Scheduling, date validation (cannot schedule earlier than today), completion updates.
- **🛡 Audit & Administration**:
  - Immutable append-only audit trail logging login, CRUD, security events, IP address, and record changes.
  - Admin User & Role Administration with password reset and account unlocking.
- **🌐 REST API**:
  - Authenticated JSON REST API endpoints (`/api/customers`, `/api/leads`, `/api/opportunities`, `/api/followups`, `/api/reports/pipeline`).

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed on your computer.

### 2. Installation & Execution

```bash
# 1. Navigate to project folder
cd AcxiomCRM

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
python app.py
```

Open your browser and visit: **`http://127.0.0.1:5000`**

---

## 🔑 Demo Account Credentials

| Role | Email | Password | Access Scope |
|---|---|---|---|
| **Admin** | `admin@acxiom.com` | `Admin123!` | Full Administration, User Management, Audit Logs |
| **Manager** | `manager@acxiom.com` | `Manager123!` | Team Pipeline, Reports, Lead/Customer Management |
| **Sales Executive** | `sales@acxiom.com` | `Sales123!` | Assigned Customers, Leads, Opportunities, Follow-ups |

*(Note: The login screen also features 1-Click Quick Fill buttons for instant testing during evaluation!)*

---

## 🐙 How to Share on GitHub

To upload this project to your GitHub account and share the link:

1. Create a new repository on [GitHub](https://github.com/new) named `AcxiomCRM`.
2. Open terminal in the `AcxiomCRM` directory and run:

```bash
git init
git add .
git commit -m "Initial commit - AcxiomCRM Project"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/AcxiomCRM.git
git push -u origin main
```

Your project will now be live on GitHub! 🚀
