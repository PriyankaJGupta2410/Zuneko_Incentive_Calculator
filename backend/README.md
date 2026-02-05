Backend – Setup Guide

This section helps you run the backend service for the Incentive Calculator System.
Follow the steps in order and you’ll be up and running in minutes.

🛠️ Technology Used

FastAPI – Backend framework

Python – Programming language (version 3.10 or above)

MySQL – Database

Uvicorn – Application server

✅ What You Need Before Starting

Please ensure the following are available on your system:

Python (3.10 or higher)
Check using:

python --version


pip (Python package manager)
Check using:

pip --version


MySQL

MySQL service should be running

You should have valid database credentials

🗄️ Database Setup

Create the database:

CREATE DATABASE incentive_calculator;


Use the database:

USE incentive_calculator;


Create required tables:

Execute the SQL queries available in the schemas.sql file

🔐 Configuration (Important)

Configuration values are kept outside the codebase for security reasons.

Create a .env file locally

Add the following details:

DB_HOST=localhost
DB_USER=
DB_PASSWORD=
DB_NAME=incentive_calculator


⚠️ Make sure these values match your local MySQL setup.

📦 Install Required Packages

All dependencies are already listed in the project.

Run:

pip install -r requirements.txt

▶️ Start the Backend Server

Launch the backend using the command below:

uvicorn app.main:app --reload


Once started, the backend will be available at:

http://localhost:8000

📘 API Documentation

The backend automatically provides API documentation:

Swagger UI:

http://localhost:8000/docs


ReDoc:

http://localhost:8000/redoc

📝 Additional Notes

The .env file is intentionally excluded from GitHub

Database must be set up before starting the backend

Backend and frontend run as independent services