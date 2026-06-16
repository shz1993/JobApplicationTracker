-- Tabel users (opsional, untuk multi-user nanti)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabel resumes (CV yang diupload)
CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1,
    file_name VARCHAR(255),
    extracted_text TEXT,
    name VARCHAR(255),
    email VARCHAR(255),
    skills TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabel jobs (lamaran kerja)
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER DEFAULT 1,
    company VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    job_description TEXT,
    status VARCHAR(50) DEFAULT 'applied',
    match_score INTEGER,
    match_feedback TEXT,
    applied_date DATE DEFAULT CURRENT_DATE,
    deadline DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabel match_history (untuk riwayat match score)
CREATE TABLE IF NOT EXISTS match_history (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    resume_id INTEGER REFERENCES resumes(id),
    score INTEGER,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index untuk performa query
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_applied_date ON jobs(applied_date);