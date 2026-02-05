Frontend – Setup Instructions
🔧 Tech Stack

Node.js

Express

JavaScript

npm

Nodemon (development)

🚀 Prerequisites

Ensure the following are installed on your system:

Node.js (v16+ recommended)

npm (comes bundled with Node.js)

Check versions:

node -v
npm -v

⚙️ Setup Instructions
📍 Step 1: Navigate to Frontend Folder
cd frontend

📍 Step 2: Initialize Node Project

(Skip this step if package.json already exists)

npm init -y


This will create:

package.json

📍 Step 3: Install Express
npm install express


This will create:

node_modules/

package-lock.json

📍 Step 4: Install Nodemon (Development Dependency)
npm install nodemon --save-dev


Nodemon automatically restarts the server during development.

▶️ Run Frontend Server

If using Nodemon:

npx nodemon index.js


Or using npm script (if configured):

npm run dev

🔗 Backend API Integration

Ensure backend is running at:

http://localhost:8000


Frontend communicates with backend APIs using this base URL.