import streamlit as st
from datetime import date
import json
import pandas as pd

# Inisialisasi koneksi ke Neon (via st.connection)
def get_connection():
    """Mendapatkan koneksi ke Neon database menggunakan st.connection"""
    return st.connection("neon", type="sql")

def init_db():
    """Inisialisasi tabel-tabel database"""
    conn = get_connection()
    
    # Tabel resumes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id SERIAL PRIMARY KEY,
            file_name TEXT,
            extracted_text TEXT,
            name TEXT,
            email TEXT,
            skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabel jobs
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id SERIAL PRIMARY KEY,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            job_description TEXT,
            status TEXT DEFAULT 'applied',
            match_score INTEGER,
            match_feedback TEXT,
            applied_date DATE DEFAULT CURRENT_DATE,
            deadline DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()

def save_resume(file_name, extracted_text, name, email, skills):
    """Simpan resume ke database"""
    conn = get_connection()
    
    result = conn.execute("""
        INSERT INTO resumes (file_name, extracted_text, name, email, skills)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (file_name, extracted_text, name, email, json.dumps(skills)))
    
    resume_id = result.fetchone()[0]
    conn.commit()
    return resume_id

def get_latest_resume():
    """Ambil resume terbaru"""
    conn = get_connection()
    
    result = conn.execute("""
        SELECT id, name, email, skills, extracted_text
        FROM resumes 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    row = result.fetchone()
    
    if row:
        try:
            skills = json.loads(row[3]) if row[3] else []
        except:
            skills = []
        return {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "skills": skills,
            "text": row[4]
        }
    return None

def save_job(company, role, job_description, status, match_score, match_feedback, deadline=None, notes=""):
    """Simpan job application"""
    conn = get_connection()
    
    result = conn.execute("""
        INSERT INTO jobs (company, role, job_description, status, match_score, 
                         match_feedback, deadline, notes, applied_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (company, role, job_description, status, match_score, 
          match_feedback, deadline, notes, date.today()))
    
    job_id = result.fetchone()[0]
    conn.commit()
    return job_id

def get_all_jobs():
    """Ambil semua jobs"""
    conn = get_connection()
    
    df = conn.query("""
        SELECT id, company, role, status, match_score, applied_date, deadline
        FROM jobs 
        ORDER BY applied_date DESC
    """)
    
    return df.to_dict('records')

def update_job_status(job_id, new_status):
    """Update status lamaran"""
    conn = get_connection()
    conn.execute("UPDATE jobs SET status = %s WHERE id = %s", (new_status, job_id))
    conn.commit()

def get_job_by_id(job_id):
    """Ambil detail job"""
    conn = get_connection()
    
    result = conn.execute("""
        SELECT id, company, role, job_description, status, match_score, 
               match_feedback, applied_date, deadline, notes
        FROM jobs WHERE id = %s
    """, (job_id,))
    
    row = result.fetchone()
    
    if row:
        return {
            "id": row[0],
            "company": row[1],
            "role": row[2],
            "job_description": row[3],
            "status": row[4],
            "match_score": row[5],
            "match_feedback": row[6],
            "applied_date": row[7],
            "deadline": row[8],
            "notes": row[9]
        }
    return None

def get_dashboard_stats():
    """Ambil statistik dashboard"""
    conn = get_connection()
    
    total_df = conn.query("SELECT COUNT(*) as total FROM jobs")
    total = total_df['total'].iloc[0] if not total_df.empty else 0
    
    status_df = conn.query("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
    status_counts = dict(zip(status_df['status'], status_df['count'])) if not status_df.empty else {}
    
    avg_df = conn.query("SELECT AVG(match_score) as avg FROM jobs WHERE match_score IS NOT NULL")
    avg_score = avg_df['avg'].iloc[0] if not avg_df.empty and avg_df['avg'].iloc[0] else 0
    
    return {
        "total": total,
        "status_counts": status_counts,
        "avg_score": round(avg_score, 1)
    }

# Inisialisasi database saat module di-load
init_db()