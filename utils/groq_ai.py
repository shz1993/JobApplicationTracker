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
    """
    Generate kemungkinan pertanyaan interview berdasarkan job description
    """
    client = get_groq_client()
    
    prompt = f"""
    Buat 5 pertanyaan interview untuk posisi {job_role} di {company}.
    Job desc: {job_description[:2000]}
    
    Output hanya JSON array: ["q1", "q2", "q3", "q4", "q5"]
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        questions = json.loads(response.choices[0].message.content)
        return questions if isinstance(questions, list) else []
    
    except Exception:
        return [
            "Ceritakan tentang diri Anda",
            "Mengapa Anda tertarik dengan posisi ini?",
            "Apa pengalaman terkuat Anda?",
            "Bagaimana Anda menghadapi tantangan?",
            "Apa ekspektasi gaji Anda?"
        ]