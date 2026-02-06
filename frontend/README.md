# Frontend -- Setup Guide

This guide explains how to run the **Frontend Service** for the
**Incentive Calculator System**. The frontend communicates with backend
APIs to display and manage incentive data.

------------------------------------------------------------------------

## 🛠️ Technology Stack

-   **Node.js** -- Runtime environment\
-   **Express** -- Web framework\
-   **JavaScript** -- Programming language\
-   **npm** -- Package manager\
-   **Nodemon** -- Auto-restart during development

------------------------------------------------------------------------

## ✅ Prerequisites

Ensure the following are installed on your system:

### Node.js

-   Version **16 or higher**

``` bash
node -v
```

### npm

-   Comes bundled with Node.js

``` bash
npm -v
```

------------------------------------------------------------------------

## ⚙️ Setup Instructions

### 📍 Step 1: Navigate to Frontend Directory

``` bash
cd frontend
```

------------------------------------------------------------------------

### 📍 Step 2: Initialize the Project

> Skip this step if `package.json` already exists.

``` bash
npm init -y
```

This will create the project configuration file:

-   `package.json`

------------------------------------------------------------------------

### 📍 Step 3: Install Required Packages

Install Express:

``` bash
npm install express
```

This will generate:

-   `node_modules/`
-   `package-lock.json`

------------------------------------------------------------------------

### 📍 Step 4: Enable Auto-Restart (Optional but Recommended)

Install Nodemon for development:

``` bash
npm install nodemon --save-dev
```

Nodemon automatically restarts the server when code changes are
detected.

------------------------------------------------------------------------

## ▶️ Running the Frontend Server

### Using Nodemon

``` bash
npx nodemon index.js
```

### Using npm script (if configured)

``` bash
npm run dev
```

------------------------------------------------------------------------

## 🔗 Backend Integration

Ensure the backend service is running before starting the frontend.

**Backend Base URL:**

    http://localhost:8000

The frontend uses this URL to communicate with backend APIs.

------------------------------------------------------------------------

## 📝 Additional Notes

-   Frontend and backend run as independent services\
-   Backend must be running to test full application functionality\
-   Update API base URLs if backend runs on a different port or host

------------------------------------------------------------------------

Happy building 🚀
