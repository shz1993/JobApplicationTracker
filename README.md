# Job Application Tracker with AI

Track job applications, analyze CV vs job description, and prepare for interviews with AI.

## Live Demo
[Press here for live demo!](https://jobapplicationtracker-33jb3sus37xx4udvrdojwk.streamlit.app/)

## What This App Does
Helps job seekers manage their job search by storing applications, comparing CV with job descriptions using AI, and generating interview questions.

## Features
- 📄 **Upload CV** - AI extracts name, email, and skills from PDF
- 💼 **Log Applications** - Store company, position, status, job description
- 🎯 **AI Match Score** - Get 0-100% match score + feedback + tips
- 🎤 **Interview Prep** - AI generates 5 questions based on job description
- 📊 **Dashboard** - Charts showing total applications, match score, status distribution
- 📝 **History** - Update status, view table, export to CSV

## Tech Stack
- Streamlit (frontend)
- Groq Llama 3.1 (free AI)
- PostgreSQL (Neon)
- pdfplumber, Plotly, Pandas

## How to Run Locally
1. Clone repo: `git clone https://github.com/shz1993/JobApplicationTracker.git`
2. Install: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml`:
```toml
DB_CONNECTION = "postgresql://..."
GROQ_API_KEY = "gsk_..."

4. Copy table from Neondb into your local database