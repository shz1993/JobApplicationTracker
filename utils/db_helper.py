import streamlit as st
from datetime import date
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def get_connection():
    """Mendapatkan koneksi ke Neon database"""
    try:
        conn_string = st.secrets["DB_CONNECTION"]
        conn = psycopg2.connect(conn_string)
        return conn
    except Exception as e:
        st.error(f"Gagal koneksi ke database: {str(e)}")
        raise e

def init_db():
    """Inisialisasi tabel-tabel database"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Hapus tabel lama jika ada (untuk reset)
    cur.execute("DROP TABLE IF EXISTS resumes CASCADE")
    cur.execute("DROP TABLE IF EXISTS jobs CASCADE")
    
    # Tabel resumes dengan skill sebagai TEXT (bukan array)
    cur.execute("""
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
    cur.execute("""
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
    cur.close()
    conn.close()

def save_resume(file_name, extracted_text, name, email, skills):
    """Simpan resume ke database"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Simpan skills sebagai JSON string (bukan array PostgreSQL)
    skills_json = json.dumps(skills) if skills else "[]"
    
    cur.execute("""
        INSERT INTO resumes (file_name, extracted_text, name, email, skills)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (file_name, extracted_text, name, email, skills_json))
    
    resume_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return resume_id

def get_latest_resume():
    """Ambil resume terbaru"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, name, email, skills, extracted_text
        FROM resumes 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        # Parse skills dari JSON string
        try:
            skills = json.loads(result['skills']) if result['skills'] else []
        except:
            skills = []
        
        return {
            "id": result['id'],
            "name": result['name'],
            "email": result['email'],
            "skills": skills,
            "text": result['extracted_text']
        }
    return None

def save_job(company, role, job_description, status, match_score, match_feedback, deadline=None, notes=""):
    """Simpan job application"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO jobs (company, role, job_description, status, match_score, 
                         match_feedback, deadline, notes, applied_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (company, role, job_description, status, match_score, 
          match_feedback, deadline, notes, date.today()))
    
    job_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return job_id

def get_all_jobs():
    """Ambil semua jobs"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, company, role, status, match_score, applied_date, deadline
        FROM jobs 
        ORDER BY applied_date DESC
    """)
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    
    return results

def update_job_status(job_id, new_status):
    """Update status lamaran"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE jobs SET status = %s WHERE id = %s
    """, (new_status, job_id))
    
    conn.commit()
    cur.close()
    conn.close()

def get_job_by_id(job_id):
    """Ambil detail job berdasarkan ID"""
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    cur.execute("""
        SELECT id, company, role, job_description, status, match_score, 
               match_feedback, applied_date, deadline, notes
        FROM jobs WHERE id = %s
    """, (job_id,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return result

def get_dashboard_stats():
    """Ambil statistik untuk dashboard"""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM jobs")
    total = cur.fetchone()[0] or 0
    
    cur.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    status_rows = cur.fetchall()
    status_counts = {row[0]: row[1] for row in status_rows}
    
    cur.execute("SELECT AVG(match_score) FROM jobs WHERE match_score IS NOT NULL")
    avg_row = cur.fetchone()
    avg_score = avg_row[0] if avg_row and avg_row[0] else 0
    
    cur.close()
    conn.close()
    
    return {
        "total": total,
        "status_counts": status_counts,
        "avg_score": round(float(avg_score), 1)
    }

# Inisialisasi database
try:
    init_db()
except Exception as e:
    print(f"Database init error: {e}")