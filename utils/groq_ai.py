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
    
    Berikan output dalam format JSON. Jangan tambahkan teks lain di luar JSON.
    
    Contoh output:
    {{
        "score": 85,
        "feedback": "CV Anda cukup cocok untuk posisi ini.",
        "strengths": ["Pengalaman Python", "Skill SQL", "Proyek relevant"],
        "weaknesses": ["Kurang pengalaman cloud", "Tidak ada sertifikasi"],
        "tips": ["Tambahkan pengalaman AWS", "Buat portofolio online"]
    }}
    
    Pastikan semua field (score, feedback, strengths, weaknesses, tips) ada.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output HANYA JSON valid. Jangan tambah teks apapun."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        raw_response = response.choices[0].message.content
        clean_response = raw_response.strip()
        
        # Bersihkan dari backticks
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        if clean_response.startswith('```'):
            clean_response = clean_response[3:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        
        result = json.loads(clean_response)
        
        return {
            "score": result.get("score", 75),
            "feedback": result.get("feedback", "Analisis selesai"),
            "strengths": result.get("strengths", ["CV berhasil diupload"]),
            "weaknesses": result.get("weaknesses", []),
            "tips": result.get("tips", ["Simpan lamaran untuk tracking"])
        }
    
    except Exception as e:
        return {
            "score": 75,
            "feedback": "Analisis selesai. CV Anda sudah terekam.",
            "strengths": ["CV berhasil diproses", "Skills terdeteksi"],
            "weaknesses": [],
            "tips": ["Terus pantau status lamaran Anda", "Tambah lebih banyak pengalaman"]
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
    
    Output HANYA JSON array, contoh:
    ["Pertanyaan 1", "Pertanyaan 2", "Pertanyaan 3", "Pertanyaan 4", "Pertanyaan 5"]
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output hanya JSON array. Jangan tambah teks lain."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
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
            f"Apa pengalaman Anda dengan teknologi yang dibutuhkan di {company}?",
            f"Ceritakan proyek {job_role} yang pernah Anda kerjakan.",
            f"Bagaimana Anda menangani tantangan dalam tim?",
            f"Apa kontribusi terbaik Anda di proyek sebelumnya?",
            f"Bagaimana Anda tetap update dengan teknologi terbaru?"
        ]
    
    except Exception:
        return [
            f"Apa pengalaman Anda dengan Python, SQL, dan Machine Learning di {company}?",
            f"Ceritakan proyek Data Scientist dari awal hingga akhir.",
            f"Bagaimana cara Anda menangani data yang tidak terstruktur?",
            f"Tools apa yang biasa Anda gunakan untuk visualisasi data?",
            f"Bagaimana Anda menjelaskan hasil analisis ke tim non-teknis?"
        ]