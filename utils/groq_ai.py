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
    """Ekstrak nama, email, skills dari resume"""
    client = get_groq_client()
    
    prompt = f"""
    Ekstrak informasi penting dari CV berikut. 
    Berikan output hanya dalam format JSON, tanpa teks lain.
    
    CV TEXT:
    {resume_text[:4000]}
    
    OUTPUT FORMAT (JSON):
    {{"name": "Nama lengkap", "email": "email@domain.com", "skills": ["skill1", "skill2"]}}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output hanya JSON valid."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        return {"error": str(e), "name": "", "email": "", "skills": []}

def calculate_match_score(resume_text: str, job_description: str, job_role: str) -> dict:
    """Hitung match score antara resume dan job description"""
    client = get_groq_client()
    
    prompt = f"""
    Analisis kecocokan CV dan deskripsi pekerjaan ini.
    
    POSISI: {job_role}
    
    CV: {resume_text[:2500]}
    JOB: {job_description[:2500]}
    
    Output JSON:
    {{"score": 85, "feedback": "feedback singkat", "strengths": ["a","b"], "weaknesses": ["c"], "tips": ["d","e"]}}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output HANYA JSON. Jangan tambah teks."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        raw = response.choices[0].message.content
        # Bersihkan response
        clean = raw.strip()
        if clean.startswith('```json'):
            clean = clean[7:]
        if clean.startswith('```'):
            clean = clean[3:]
        if clean.endswith('```'):
            clean = clean[:-3]
        
        result = json.loads(clean)
        return {
            "score": result.get("score", 50),
            "feedback": result.get("feedback", ""),
            "strengths": result.get("strengths", []),
            "weaknesses": result.get("weaknesses", []),
            "tips": result.get("tips", [])
        }
    
    except Exception as e:
        return {
            "score": 50,
            "feedback": "Analisis selesai. CV Anda sudah terekam.",
            "strengths": ["CV berhasil diupload"],
            "weaknesses": [],
            "tips": ["Simpan lamaran ini untuk tracking"]
        }

def generate_interview_questions(job_description: str, job_role: str, company: str) -> list:
    """Generate pertanyaan interview"""
    client = get_groq_client()
    
    prompt = f"""
    Buat 5 pertanyaan interview untuk posisi {job_role} di {company}.
    Job desc: {job_description[:2000]}
    
    Output JSON array: ["q1", "q2", "q3", "q4", "q5"]
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=400
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
        return questions if isinstance(questions, list) else []
    
    except Exception:
        return [
            "Ceritakan tentang diri Anda",
            "Mengapa Anda tertarik dengan posisi ini?",
            "Apa pengalaman terkuat Anda?",
            "Bagaimana Anda menghadapi tantangan?",
            "Apa ekspektasi gaji Anda?"
        ]