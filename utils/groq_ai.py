"""
Module untuk AI menggunakan Groq (Llama 3)
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
    
    Args:
        resume_text: Teks resume yang sudah diekstrak dari PDF
        
    Returns:
        Dictionary: {"name": "...", "email": "...", "skills": [...]}
    """
    client = get_groq_client()
    
    prompt = f"""
    Ekstrak informasi penting dari CV berikut. 
    Berikan output hanya dalam format JSON, tanpa teks lain.
    
    CV TEXT:
    {resume_text[:4000]}
    
    OUTPUT FORMAT (JSON):
    {{
        "name": "Nama lengkap orang ini",
        "email": "Alamat email yang terdeteksi",
        "skills": ["skill1", "skill2", "skill3", "..."]
    }}
    
    Untuk skills: ambil semua skill teknis dan soft skill yang relevan.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",,
            messages=[
                {"role": "system", "content": "Kamu adalah HR AI profesional. Output hanya JSON valid."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    
    except Exception as e:
        return {"error": str(e), "name": "", "email": "", "skills": []}

def calculate_match_score(resume_text: str, job_description: str, job_role: str) -> dict:
    """
    Hitung match score antara resume dan job description
    
    Args:
        resume_text: Teks resume
        job_description: Deskripsi pekerjaan
        job_role: Nama role/posisi
        
    Returns:
        Dictionary: {"score": 0-100, "feedback": "...", "strengths": [...], "weaknesses": [...]}
    """
    client = get_groq_client()
    
    prompt = f"""
    Analisis kecocokan antara CV dan deskripsi pekerjaan berikut.
    
    POSISI: {job_role}
    
    CV:
    {resume_text[:2500]}
    
    DESKRIPSI PEKERJAAN:
    {job_description[:2500]}
    
    Berikan output dalam format JSON:
    {{
        "score": (angka 0-100, berapa persen cocok),
        "feedback": "Paragraf singkat menjelaskan hasil analisis",
        "strengths": ["kelebihan 1", "kelebihan 2", "kelebihan 3"],
        "weaknesses": ["kekurangan 1", "kekurangan 2"],
        "tips": ["tips perbaikan 1", "tips perbaikan 2"]
    }}
    
    Hitung score berdasarkan:
    - Kesesuaian skills (60%)
    - Pengalaman relevan (30%)
    - Kesesuaian role (10%)
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",,
            messages=[
                {"role": "system", "content": "Kamu adalah HR AI. Output hanya JSON valid, tanpa teks lain."},
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
    
    Returns:
        List berisi 5 pertanyaan
    """
    client = get_groq_client()
    
    prompt = f"""
    Generate 5 pertanyaan interview yang paling mungkin muncul untuk posisi berikut:
    
    PERUSAHAAN: {company}
    POSISI: {job_role}
    DESKRIPSI PEKERJAAN:
    {job_description[:2000]}
    
    Output hanya list JSON: ["pertanyaan 1", "pertanyaan 2", ...]
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        questions = json.loads(response.choices[0].message.content)
        return questions if isinstance(questions, list) else []
    
    except Exception:
        return [
            "Ceritakan tentang diri Anda",
            "Mengapa Anda tertarik dengan posisi ini?",
            "Apa pengalaman terkuat Anda yang relevan?",
            "Bagaimana Anda menghadapi tantangan dalam tim?",
            "Apa ekspektasi gaji Anda?"
        ]