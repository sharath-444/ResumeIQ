# ResumeIQ 🚀

ResumeIQ is a modern, AI-powered resume analyzer that helps job seekers optimize their resumes for Applicant Tracking Systems (ATS). It evaluates resumes for ATS compatibility, provides skill-gap insights, and offers improvement suggestions.

## Features

- **📄 Multi-Format Support**: Upload PDF or DOCX resumes.
- **⚡ Instant Analysis**: Basic NLP extracts contact info, skills, experience, and projects.
- **🎯 Role-Based Scoring**: Select a target role (Frontend, Backend, DevOps, Data Science) for tailored feedback.
- **📊 Visual Dashboard**: Circular ATS Score Meter, Radar Chart, Skill Gap Analysis.
- **💡 Smart Suggestions**: Actionable feedback and "Power Verb" recommendations.
- **🔐 Secure Access**: Role-based authentication (User/Admin) and secure data handling.

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy, Flask-Login, OpenRouter AI
- **Frontend**: HTML5, CSS, JavaScript, Chart.js (Served by Flask)
- **Parsing**: PyPDF2, python-docx

## Project Structure

```
resumeiq/
├── backend/                 # ── Backend (Python / Flask)
│   ├── run.py               # Entry point → python backend/run.py
│   ├── app.py               # Flask app factory
│   ├── models.py            # SQLAlchemy models
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Secrets (gitignored)
│   ├── routes/
│   │   ├── auth.py          # Login / register / logout
│   │   ├── main.py          # Upload, dashboard, report
│   │   └── admin.py         # Admin panel
│   ├── utils/
│   │   ├── ai_scorer.py     # OpenRouter AI feedback
│   │   ├── analyzer.py      # Resume parsing & skill-gap
│   │   ├── scorer.py        # ATS scoring algorithm
│   │   ├── extractor.py     # PDF/DOCX text extraction
│   │   ├── constants.py     # Role & skill constants
│   │   └── decorators.py    # @admin_required decorator
│   ├── scripts/             # Utility / debug scripts
│   ├── instance/            # SQLite DB (gitignored)
│   └── uploads/             # Uploaded resumes (gitignored)
│
├── frontend/                # ── Frontend (Templates & Static)
│   ├── templates/           # Jinja2 HTML templates
│   └── static/
│       ├── css/
│       └── js/
│
├── .env.example             # Template for environment variables
├── .gitignore
└── README.md
```

## Installation

1. **Clone the repository** (or unzip the folder).
2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Mac/Linux
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Configure environment variables**:
   ```bash
   copy .env.example backend\.env   # Windows
   # cp .env.example backend/.env   # Mac/Linux
   # Then edit backend/.env and set OPENROUTER_API_KEY and SECRET_KEY
   ```

## Running the App

```bash
python backend/run.py
```

Open your browser at `http://127.0.0.1:5000`

**Default admin account**: username `admin` / password `password123`

## License

MIT License
