# Airbnb Clone Project

# Overview

The Airbnb Clone Project is a full-stack web application designed to replicate the core functionality of Airbnb — a global online marketplace for lodging and travel experiences. This project serves as a hands-on learning experience in designing, developing, and deploying a scalable booking platform. It emphasizes backend architecture, database modeling, API design, and modern DevOps practices.

# Project Goals

The main objectives of this project are to:

 Develop a robust backend system capable of handling complex booking workflows.

Strengthen understanding of relational database design and optimization.

Implement secure and efficient RESTful API endpoints.

 Apply collaborative software engineering practices using GitHub and CI/CD tools.

 Integrate multiple technologies to create a seamless and scalable application experience.

# Tech Stack

This project leverages a combination of modern technologies, including:

 Backend Framework: Django (Python)

 Database: MySQL

 API Development: Django REST Framework / GraphQL

 Version Control: Git & GitHub




# 👥 Team Roles

Building a scalable Airbnb Clone requires a collaborative effort across several specialized roles. Each member contributes unique expertise to ensure the project’s success.

# 🧑‍💻 Backend Developer

Responsible for designing, implementing, and maintaining the server-side logic of the application.
They build RESTful APIs, handle authentication, integrate third-party services, and ensure that the backend is efficient, secure, and scalable.

Key Responsibilities:

Develop and maintain the core logic and APIs using Django.

Manage user sessions, authentication, and authorization.

Integrate frontend requests with the backend logic.

Optimize performance and ensure code scalability.

# 🗄️ Database Administrator (DBA)

Ensures that the project’s data layer is well-structured, optimized, and secure.
The DBA manages all database-related operations, including schema design, normalization, indexing, and backup management.

Key Responsibilities:

Design and implement the relational database schema (MySQL).

Manage data integrity, migrations, and security.

Optimize queries for performance.

Perform regular data backups and recovery testing.

# 💻 Frontend Developer

Focuses on creating the visual and interactive aspects of the Airbnb Clone application.
They transform backend data into user-friendly interfaces, ensuring smooth navigation and responsiveness.

Key Responsibilities:

Design and develop responsive user interfaces.

Integrate frontend components with backend APIs.

Enhance user experience (UX) and accessibility.

Test and debug UI components across devices.

# 🔐 Security Engineer

Responsible for securing the application from potential vulnerabilities.
They ensure all transactions, data transfers, and authentication mechanisms follow industry-standard security practices.

Key Responsibilities:

Implement encryption and authentication protocols.

Monitor and mitigate potential security threats.

Conduct vulnerability assessments and penetration testing.

Maintain compliance with data protection standards.

# ⚙️ DevOps Engineer

Manages the automation, deployment, and monitoring processes.
They set up the CI/CD pipeline to streamline integration and deployment while ensuring application uptime and stability.

Key Responsibilities:

Set up Docker containers and manage deployments.

Implement CI/CD using GitHub Actions.

Monitor server performance and logs.

Automate testing, build, and release processes.

# 🧾 Project Manager

Oversees project planning, timelines, and deliverables.
They coordinate communication between all team members, ensuring that goals and deadlines are met.

Key Responsibilities:

Define project scope and milestones.

Facilitate team collaboration and workflow.

Track progress and manage documentation.

Ensure timely delivery and quality control.



# 🧠 Technology Stack

The Airbnb Clone Project is built using a collection of modern tools and frameworks that work together to deliver a scalable, secure, and high-performing application. Each technology in the stack plays a specific role in achieving these goals.

🐍 Django

A high-level Python web framework used for building robust, maintainable, and secure web applications.
In this project, Django handles the backend logic, routing, user authentication, and API integration while following the Model-View-Template (MVT) architecture.

🗃️ MySQL

A powerful relational database management system (RDBMS) used to store and manage application data.
MySQL ensures data integrity, relational mapping, and high performance for user profiles, listings, reservations, and payment records.

🔗 GraphQL

An advanced query language for APIs that provides clients with the ability to request specific data.
GraphQL improves efficiency by minimizing over-fetching and under-fetching, offering flexibility when querying data across listings, users, and bookings.

🐳 Docker

A containerization platform that allows applications and dependencies to run consistently across multiple environments.
Docker is used to containerize the Airbnb Clone application, simplifying development, testing, and deployment.

⚙️ Git & GitHub

A version control system (Git) and a collaboration platform (GitHub) used for managing source code, version tracking, and team collaboration.
They support efficient teamwork, issue tracking, and CI/CD integrations.

🚀 GitHub Actions

An automation tool integrated into GitHub that enables CI/CD workflows.
GitHub Actions automates testing, building, and deploying the Airbnb Clone, ensuring reliability and reducing manual effort.

☁️ Cloud Deployment (AWS / Render / Heroku)

A cloud hosting environment used to deploy the application and make it accessible to end users.
This ensures scalability, performance, and continuous availability of the Airbnb Clone web platform.


🔒 API Security Tools

Includes libraries and middleware for implementing authentication (JWT, OAuth2), data validation, and encryption.
These ensure that all communication between the client and server remains private and tamper-proof.


 # 🗄️ Database Design

The Airbnb Clone Project uses a relational database model built with MySQL, ensuring data integrity, scalability, and efficient querying. The database is designed to represent real-world relationships between users, properties, bookings, reviews, and payments.

🧑‍🤝‍🧑 Users

Represents all users registered on the platform — including hosts and guests.

Key Fields:

id: Unique identifier for each user

name: Full name of the user

email: User’s email address (unique)

password_hash: Encrypted password for authentication

role: Defines whether the user is a host or guest

Relationships:

A user can list multiple properties.

A user can make multiple bookings.

A user can write multiple reviews.

🏠 Properties

Represents all listed accommodations available for booking.

Key Fields:

id: Unique identifier for each property

host_id: Foreign key referencing the user (host)

title: Property name or title

description: Overview of the property

price_per_night: Cost per night for booking

Relationships:

A property belongs to one host (user).

A property can have multiple bookings and reviews.

📅 Bookings

Tracks reservations made by users for specific properties.

Key Fields:

id: Unique booking identifier

user_id: Foreign key referencing the guest (user)

property_id: Foreign key referencing the booked property

check_in_date: Start date of the booking

check_out_date: End date of the booking

Relationships:

A booking belongs to one property.

A booking is made by one user (guest).

A booking can have one associated payment record.

💳 Payments

Handles all financial transactions between guests and hosts.

Key Fields:

id: Unique payment identifier

booking_id: Foreign key referencing the related booking

amount: Total payment amount

payment_method: Method used (e.g., credit card, PayPal)

status: Indicates whether payment is pending, completed, or failed

Relationships:

A payment belongs to one booking.

A booking has one payment record.

⭐ Reviews

Captures feedback and ratings given by guests after their stay.

Key Fields:

id: Unique review identifier

user_id: Foreign key referencing the guest (user)

property_id: Foreign key referencing the reviewed property

rating: Numeric rating (e.g., 1–5 stars)

comment: Text feedback on the stay

Relationships:

A review is written by one user (guest).

A review belongs to one property.

🔗 Entity Relationships Summary

User → Property: One-to-Many

User → Booking: One-to-Many

User → Review: One-to-Many



# 🧩 Feature Breakdown

The Airbnb Clone Project includes several core features that work together to deliver a seamless experience for both hosts and guests. Each feature is designed to mirror real-world Airbnb functionalities while showcasing strong backend and architectural design principles.

👤 User Management

Handles user registration, authentication, and profile management.
This feature enables users to create accounts, log in securely, and manage personal information. It also distinguishes between hosts (who list properties) and guests (who book stays).

🏠 Property Management

Allows hosts to create, update, and delete property listings.
Each property includes detailed descriptions, images, location data, and pricing. This feature ensures accurate representation of listings and simplifies the property discovery process for guests.

📅 Booking System

Facilitates the reservation of properties by guests.
Users can select available dates, confirm bookings, and receive notifications. The system prevents overlapping reservations and maintains accurate booking records.

💳 Payment Integration

Manages secure payments between guests and hosts.
It supports multiple payment methods and ensures that transactions are processed safely through encryption and validation. This feature provides transparency and trust in financial operations.

⭐ Reviews and Ratings

Allows guests to leave feedback on properties they’ve stayed in.
Each review includes a written comment and a rating score, contributing to host credibility and helping future guests make informed decisions.

🔐 Security and Authentication

Implements secure user authentication using methods such as JWT or OAuth2.
This feature ensures that only authorized users can access restricted endpoints, protecting sensitive user and transaction data from unauthorized access.

⚙️ CI/CD and Deployment

Automates the development workflow using GitHub Actions and Docker.
Continuous Integration and Continuous Deployment ensure that code changes are tested, built, and deployed efficiently, reducing human errors and improving delivery speed.

📊 Admin Dashboard (Optional Enhancement)

Provides administrators with tools to manage users, properties, and payments.
This feature enhances system oversight, allowing admins to monitor activity, verify listings, and ensure compliance with platform policies.

Property → Booking: One-to-Many

Property → Review: One-to-Many




# 🔒 API Security

Securing the backend API is essential to ensure that user data, financial transactions, and platform operations remain protected from unauthorized access or malicious activity. The Airbnb Clone Project integrates several layers of security to maintain data confidentiality, integrity, and availability.

🔑 Authentication

Implements secure user login and identity verification using JWT (JSON Web Tokens) or OAuth2.
This ensures that only registered users can access protected endpoints and perform authorized actions.
Why it’s important: Protects user accounts from unauthorized access and prevents impersonation attacks.

🧾 Authorization

Defines specific permissions and access control for different user roles — such as hosts, guests, and admins.
Authorization ensures that users can only perform actions they are permitted to (e.g., a guest cannot edit another host’s property listing).
Why it’s important: Prevents privilege escalation and maintains proper role-based security boundaries.

🚦 Rate Limiting

Restricts the number of API requests a user or client can make within a set time frame.
By using tools like Django REST Framework throttling or NGINX rate limiting, the system prevents denial-of-service (DoS) attacks and API abuse.
Why it’s important: Protects the server from being overwhelmed by malicious or excessive requests.

🔐 Data Encryption

Ensures that sensitive information — such as passwords, payment details, and personal data — is encrypted both in transit (using HTTPS/SSL) and at rest (in the database).
Why it’s important: Safeguards user privacy and prevents data leaks or theft.

🧱 Input Validation & Sanitization

All API inputs are validated to prevent injection attacks (e.g., SQL Injection, XSS).
Data is sanitized before being stored or processed to maintain data integrity.
Why it’s important: Protects the backend from malicious payloads and ensures system stability.

🧩 Error Handling & Logging

Implements secure error responses that avoid exposing sensitive system information while maintaining detailed server-side logs for auditing and debugging.
Why it’s important: Prevents attackers from gathering system details and helps in quick issue tracking during incidents.

🕵️‍♀️ Secure Payment Processing

Integrates trusted payment gateways and ensures all payment APIs comply with PCI DSS (Payment Card Industry Data Security Standard).
Sensitive financial data is tokenized rather than stored directly in the database.
Why it’s important: Protects user financial information and builds trust in the platform’s payment system.

Booking → Payment: One-to-One



# ⚙️ CI/CD Pipeline

Continuous Integration (CI) and Continuous Deployment (CD) are key components of modern software development. They automate the process of building, testing, and deploying code, ensuring faster delivery, fewer human errors, and more reliable updates.

🔄 Continuous Integration (CI)

In the Airbnb Clone Project, Continuous Integration ensures that every code change pushed to the repository is automatically tested and validated.
This helps detect errors early in the development process, maintain code quality, and keep the main branch stable.

Key Benefits:

Early detection of bugs and integration issues.

Consistent testing environment for all contributors.

Smooth collaboration through automated build checks.

🚀 Continuous Deployment (CD)

Continuous Deployment automates the process of pushing tested and approved changes to the production environment.
This ensures that new features and fixes are delivered quickly and consistently without manual intervention.

Key Benefits:

Faster feature delivery and updates.

Reduced downtime through automated deployment.

Improved reliability and rollback management.

🧰 Tools Used

To achieve CI/CD automation, the following tools are utilized in this project:

GitHub Actions: Automates workflows for testing, building, and deploying code directly from the GitHub repository.

Docker: Containerizes the application, ensuring consistency across development, testing, and production environments.

Cloud Deployment Services (e.g., AWS, Render, Heroku): Used for hosting the production-ready application.

Testing Frameworks (e.g., Pytest, Django Test): Ensure that the code meets functional and performance requirements before deployment.






# 🛠️ Getting Started

### Prerequisites

- Python 3.13+
- (Optional) Docker Desktop, to run with MySQL

### Local setup (SQLite, no Docker)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env          # then set SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8000/admin/.

### Docker setup (MySQL)

```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py createsuperuser
```

### Quality checks

```bash
ruff check .          # lint
ruff format .         # format
pytest                # tests
```

These same checks run in GitHub Actions on every push and pull request.

### Project structure

```
config/         # Django settings, root URLs, WSGI/ASGI
apps/
  users/        # Custom User model (email login, guest/host/admin roles)
  properties/   # Listings
  bookings/     # Reservations
  reviews/      # Ratings & comments
  payments/     # Payment records
requirements/   # base.txt (prod) and dev.txt (tooling)
```

### API endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | — | Create an account (`role`: `guest` or `host`) |
| POST | `/api/auth/login/` | — | Get `access` + `refresh` JWT tokens |
| POST | `/api/auth/refresh/` | — | Get a new access token from a refresh token |
| GET / PATCH | `/api/users/me/` | Bearer | View or update your profile |

Send the access token as `Authorization: Bearer <token>`. Access tokens last 15 minutes and refresh tokens 7 days. Register and login are limited to 10 requests per minute.
