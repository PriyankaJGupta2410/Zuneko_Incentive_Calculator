Frontend – Setup Guide

This section explains how to run the frontend service for the Incentive Calculator System.
The frontend communicates with the backend APIs to display and manage data.

🛠️ Technology Used

Node.js – Runtime environment

Express – Web framework

JavaScript – Programming language

npm – Package manager

Nodemon – Auto-restart during development

✅ What You Need Before Starting

Please ensure the following are available on your system:

Node.js (version 16 or above)

npm (comes bundled with Node.js)

Check installation using:

node -v
npm -v

⚙️ Setup Steps
📍 Step 1: Go to the Frontend Folder
cd frontend

📍 Step 2: Initialize the Project

(Skip this step if package.json already exists)

npm init -y


This will create the project configuration file:

package.json

📍 Step 3: Install Required Packages

Install Express:

npm install express


This will create:

node_modules/

package-lock.json

📍 Step 4: Enable Auto-Restart (Optional but Recommended)

Install Nodemon for development:

npm install nodemon --save-dev


Nodemon automatically restarts the server whenever code changes are made.

▶️ Start the Frontend Server

Using Nodemon:

npx nodemon index.js


Or using an npm script (if configured):

npm run dev

🔗 Backend Connection

Make sure the backend service is running before using the frontend.

Backend URL:

http://localhost:8000


The frontend uses this base URL to communicate with backend APIs.

📝 Additional Notes

Frontend and backend run as separate services

Backend must be running to test full functionality