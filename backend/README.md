# Backend -- Setup Guide

This guide helps you set up and run the **Backend Service** for the
**Incentive Calculator System**. Follow the steps below carefully and
you'll be up and running in just a few minutes.

------------------------------------------------------------------------

## 🛠️ Technology Stack

-   **FastAPI** -- Backend framework\
-   **Python** -- Version 3.10 or higher\
-   **MySQL** -- Relational database\
-   **Uvicorn** -- ASGI application server

------------------------------------------------------------------------

## ✅ Prerequisites

Ensure the following are installed and properly configured on your
system:

### Python

-   Version **3.10 or higher**

``` bash
python --version
```

### pip (Python Package Manager)

``` bash
pip --version
```

### MySQL

-   MySQL service must be running
-   You should have valid database credentials

------------------------------------------------------------------------

## 🗄️ Database Setup

1.  **Create the database**

``` sql
CREATE DATABASE incentive_calculator;
```

2.  **Select the database**

``` sql
USE incentive_calculator;
```

3.  **Create required tables**

-   Execute the SQL queries provided in the `schemas.sql` file

------------------------------------------------------------------------

## 🔐 Environment Configuration

For security reasons, sensitive configuration values are not stored in
the codebase.

1.  Create a `.env` file in the project root directory
2.  Add the following environment variables:

``` env
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=incentive_calculator
```

⚠️ Ensure these values match your local MySQL configuration.

> Note: The `.env` file is intentionally excluded from GitHub.

------------------------------------------------------------------------

## 📦 Install Dependencies

All required dependencies are listed in the `requirements.txt` file.

Run the following command:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## ▶️ Running the Backend Server

Start the FastAPI backend using Uvicorn:

``` bash
uvicorn app.main:app --reload
```

Once the server starts successfully, the backend will be available at:

    http://localhost:8000

------------------------------------------------------------------------

## 📘 API Documentation

FastAPI provides interactive API documentation out of the box.

-   **Swagger UI:**\
    http://localhost:8000/docs

-   **ReDoc:**\
    http://localhost:8000/redoc

------------------------------------------------------------------------

## 📝 Additional Notes

-   Ensure the database is fully set up before starting the backend
-   The backend and frontend run as independent services
-   Configuration values should never be committed to version control

------------------------------------------------------------------------

Happy coding 🚀
