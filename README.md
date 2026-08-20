# HR Agent MVP

An AI-powered HR Agent application with a Python backend and Angular frontend.

## Project Structure

```text
hr_agent_mvp/
│
├── backend/              # Python Backend
│   ├── ...
│   └── data/
│
├── web_app/
│   └── hr_agent_web/     # Angular Frontend
│       ├── src/
│       ├── angular.json
│       └── package.json
│
├── venv/                 # Python Virtual Environment (not included in Git)
├── .gitignore
└── README.md
```

---

## Requirements

Before running the project, make sure you have the following installed:

* Python 3.x
* Node.js
* npm
* Angular CLI

You can check your installed versions:

```bash
python --version
node --version
npm --version
ng version
```

---

# Backend Setup

Open a terminal in the project root.

### 1. Create a Virtual Environment

```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### macOS / Linux

```bash
source venv/bin/activate
```

### 3. Install Backend Dependencies

Navigate to the backend folder:

```bash
cd backend
```

Install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file inside the `backend` folder:

```text
backend/
└── .env
```

Add the required environment variables.

Example:

```env
OPENAI_API_KEY=your_api_key_here
```

> Do not commit your `.env` file to GitHub.

### 5. Run the Backend

From the `backend` directory, run:

```bash
python main.py
```

> If your backend uses a different entry point, replace `main.py` with the appropriate file.

---

# Frontend Setup

Open another terminal.

Navigate to the Angular project:

```bash
cd web_app/hr_agent_web
```

### 1. Install Dependencies

```bash
npm install
```

### 2. Run Angular

```bash
ng serve
```

The application will usually be available at:

```text
http://localhost:4200
```

---

# Running the Complete Application

You need to run both the backend and frontend.

### Terminal 1 — Backend

```bash
cd hr_agent_mvp
venv\Scripts\activate
cd backend
python main.py
```

### Terminal 2 — Frontend

```bash
cd hr_agent_mvp/web_app/hr_agent_web
npm install
ng serve
```

Then open:

```text
http://localhost:4200
```

---

# Configuration

Make sure the Angular frontend is configured to communicate with the backend API.

For example:

```text
Frontend:
http://localhost:4200

Backend:
http://localhost:8000
```

Update the API URL in the Angular environment/configuration files if necessary.

---

# Important Notes

* `venv/` is not included in the repository. Create it locally.
* `node_modules/` is not included in the repository. Run `npm install`.
* `.env` is not included in the repository for security reasons.
* `backend/data/chroma_db/` is not included in the repository.
* `backend/data/hr_data.db` is not included in the repository.

---

# Troubleshooting

### `pip install` fails

Make sure your virtual environment is activated:

```bash
venv\Scripts\activate
```

Then run:

```bash
pip install -r requirements.txt
```

### `ng` is not recognized

Install Angular CLI:

```bash
npm install -g @angular/cli
```

Then verify:

```bash
ng version
```

### Angular dependencies are missing

Run:

```bash
cd web_app/hr_agent_web
npm install
```

### Port 4200 is already in use

Run Angular on another port:

```bash
ng serve --port 4300
```

Then open:

```text
http://localhost:4300
```

---

# License

This project is for educational and development purposes.
