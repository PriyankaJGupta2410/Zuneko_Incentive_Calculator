Backend – Setup Instructions
🔧 Tech Stack

Backend Framework: FastAPI

Language: Python 3.10+

Database: MySQL

API Server: Uvicorn

✅ Prerequisites

Ensure the following are installed on your system:

Python
python --version


Python 3.10 or higher is required.

pip
pip --version

MySQL

MySQL service must be running locally

Database should be accessible with valid credentials

🗄️ Database Setup

Create the required MySQL database:

CREATE DATABASE incentive_calculator;

🔐 Environment Configuration

Environment variables are gitignored and are not committed to the repository.

Create a .env file locally and add the following values:

DB_HOST=localhost
DB_USER=
DB_PASSWORD=
DB_NAME=incentive_calculator


⚠️ Ensure correct MySQL credentials are provided before starting the backend.

📦 Install Dependencies

All required dependencies are listed in requirements.txt.

pip install -r requirements.txt

▶️ Run Backend Server

Start the FastAPI server using Uvicorn:

uvicorn app.main:app --reload


Backend will be available at:

http://localhost:8000

📘 API Documentation

FastAPI automatically generates API documentation.

Swagger UI:

http://localhost:8000/docs


ReDoc:

http://localhost:8000/redoc

📝 Notes

.env file is excluded from version control via .gitignore

MySQL database must be created before running the backend

Backend and frontend are decoupled and run independently