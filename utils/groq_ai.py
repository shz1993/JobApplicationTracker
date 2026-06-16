"""
Module untuk AI menggunakan Groq (Llama 3.1 8B Instant)
"""
import json
from groq import Groq
import streamlit as st

def get_groq_client():
    """Mendapatkan client Groq dari secrets"""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

def extract_resume_data(resume_text: str) -> dict:
    """
    Ekstrak nama, email, skills dari resume menggunakan Groq
    """
    client = get_groq_client()
    
    prompt = f"""
    Ekstrak informasi penting dari CV berikut. 
    Berikan output hanya dalam format JSON, tanpa teks lain.
    
    CV TEXT:
    {resume_text[:4000]}
    
    OUTPUT FORMAT (JSON):
    {{"name": "Nama lengkap orang ini", "email": "Alamat email", "skills": ["skill1", "skill2"]}}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Kamu adalah HR AI. Output hanya JSON valid."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        return {"error": str(e), "name": "", "email": "", "skills": []}

def calculate_match_score(resume_text: str, job_description: str, job_role: str) -> dict:
    """
    Hitung match score antara resume dan job description
    """
    client = get_groq_client()
    
    prompt = f"""
    Analisis kecocokan antara CV dan deskripsi pekerjaan berikut.
    
    POSISI: {job_role}
    
    CV TEXT:
    {resume_text[:3000]}
    
    JOB DESCRIPTION:
    {job_description[:3000]}
    
    Output hanya JSON:
    {{"score": 85, "feedback": "feedback singkat", "strengths": ["a","b"], "weaknesses": ["c"], "tips": ["d","e"]}}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output hanya JSON valid."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        return {
            "score": 0,
            "feedback": f"Error: {str(e)}",
            "strengths": [],
            "weaknesses": [],
            "tips": ["Coba lagi nanti"]
        }

def generate_interview_questions(job_description: str, job_role: str, company: str) -> list:
    """Generate pertanyaan interview spesifik berdasarkan job description"""
    client = get_groq_client()
    
    prompt = f"""
    Berdasarkan deskripsi pekerjaan ini, buatkan 5 pertanyaan interview yang SPESIFIK dan RELEVAN.
    
    PERUSAHAAN: {company}
    POSISI: {job_role}
    
    DESKRIPSI PEKERJAAN:
    {job_description[:2000]}
    
    BUAT PERTANYAAN YANG:
    1. Menguji skill teknis yang disebutkan di job desc
    2. Menanyakan pengalaman relevan dengan posisi ini
    3. Menggali pemahaman tentang tools/teknologi yang dibutuhkan
    4. Berbasis situasi nyata (behavioral question)
    5. Spesifik untuk industri/perusahaan ini
    
    Output HANYA JSON array, contoh:
    ["Pertanyaan 1", "Pertanyaan 2", "Pertanyaan 3", "Pertanyaan 4", "Pertanyaan 5"]
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Kamu adalah HR AI. Output hanya JSON array. Jangan tambah teks lain."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,  # Lebih tinggi agar lebih kreatif
            max_tokens=500
        )
        
        raw = response.choices[0].message.content
        clean = raw.strip()
        if clean.startswith('```json'):
            clean = clean[7:]
        if clean.startswith('```'):
            clean = clean[3:]
        if clean.endswith('```'):
            clean = clean[:-3]
        
        questions = json.loads(clean)
        return questions if isinstance(questions, list) and len(questions) >= 3 else [
            f"Apa pengalaman Anda dengan tools yang disebutkan di job description {company}?",
            f"Ceritakan proyek {job_role} paling menantang yang pernah Anda kerjakan.",
            f"Bagaimana Anda menangani studi kasus [topik dari job desc]?",
            f"Apa kontribusi terbesar yang bisa Anda berikan ke tim {company}?",
            f"Bagaimana Anda tetap update dengan perkembangan terbaru di bidang ini?"
        ]
    
    except Exception as e:
        # Fallback questions yang lebih spesifik
        return [
            f"Apa pengalaman Anda dengan Python, SQL, dan Machine Learning seperti yang dibutuhkan di {company}?",
            f"Ceritakan proyek Data Scientist yang pernah Anda kerjakan dari awal hingga akhir.",
            f"Bagaimana cara Anda menangani data yang tidak terstruktur atau kotor?",
            f"Tools apa saja yang biasa Anda gunakan untuk visualisasi data?",
            f"Bagaimana Anda menjelaskan hasil analisis kompleks ke tim non-teknis?"
        ]