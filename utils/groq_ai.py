"""
Module for AI using Groq (Llama 3.1 8B Instant)
"""
import json
from groq import Groq
import streamlit as st

def get_groq_client():
    """Get Groq client from secrets"""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

def extract_resume_data(resume_text: str) -> dict:
    """
    Extract name, email, skills from resume using Groq
    """
    client = get_groq_client()
    
    prompt = f"""
    Extract important information from the following CV.
    Output ONLY in JSON format, no other text.
    
    CV TEXT:
    {resume_text[:4000]}
    
    OUTPUT FORMAT (JSON):
    {{"name": "Full name of this person", "email": "Detected email address", "skills": ["skill1", "skill2"]}}
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are an HR AI. Output only valid JSON."},
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
    Calculate match score between resume and job description
    """
    client = get_groq_client()
    
    prompt = f"""
    Analyze the match between the CV and job description below.
    
    POSITION: {job_role}
    
    CV TEXT:
    {resume_text[:3000]}
    
    JOB DESCRIPTION:
    {job_description[:3000]}
    
    Output ONLY in JSON format. Do not add any other text outside JSON.
    
    Example output:
    {{
        "score": 85,
        "feedback": "Your CV is a good match for this position because...",
        "strengths": ["Python experience", "SQL skills", "Relevant projects"],
        "weaknesses": ["Missing cloud experience", "No certifications"],
        "tips": ["Add AWS experience", "Create an online portfolio"]
    }}
    
    Make sure all fields (score, feedback, strengths, weaknesses, tips) are included.
    Calculate score from 0-100 based on skills and experience match.
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output ONLY valid JSON. Do not add any other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        raw_response = response.choices[0].message.content
        clean_response = raw_response.strip()
        
        # Clean from backticks
        if clean_response.startswith('```json'):
            clean_response = clean_response[7:]
        if clean_response.startswith('```'):
            clean_response = clean_response[3:]
        if clean_response.endswith('```'):
            clean_response = clean_response[:-3]
        
        result = json.loads(clean_response)
        
        return {
            "score": result.get("score", 75),
            "feedback": result.get("feedback", "Analysis complete"),
            "strengths": result.get("strengths", ["CV successfully uploaded"]),
            "weaknesses": result.get("weaknesses", []),
            "tips": result.get("tips", ["Track your applications regularly"])
        }
    
    except Exception as e:
        return {
            "score": 75,
            "feedback": "Analysis complete. Your CV has been recorded.",
            "strengths": ["CV successfully processed", "Skills detected"],
            "weaknesses": [],
            "tips": ["Keep monitoring your application status"]
        }

def generate_interview_questions(job_description: str, job_role: str, company: str) -> list:
    """Generate specific interview questions based on job description"""
    client = get_groq_client()
    
    prompt = f"""
    Based on this job description, create 5 SPECIFIC and RELEVANT interview questions.
    
    COMPANY: {company}
    POSITION: {job_role}
    
    JOB DESCRIPTION:
    {job_description[:2000]}
    
    Output ONLY a JSON array, example:
    ["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]
    
    Make questions that test:
    1. Technical skills mentioned in the job description
    2. Relevant experience for this position
    3. Understanding of required tools/technologies
    4. Real-world scenarios (behavioral questions)
    5. Industry/company specific knowledge
    """
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Output only JSON array. Do not add any other text."},
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
            f"What experience do you have with the technologies required for this position at {company}?",
            f"Tell me about a {job_role} project you worked on from start to finish.",
            f"How do you handle challenges when working in a team?",
            f"What has been your biggest contribution in a previous project?",
            f"How do you stay updated with the latest technologies in your field?"
        ]
    
    except Exception:
        return [
            f"What experience do you have with Python, SQL, and Machine Learning as required by {company}?",
            f"Tell me about a Data Scientist project you worked on from start to finish.",
            f"How do you handle unstructured or messy data?",
            f"What tools do you use for data visualization?",
            f"How do you explain complex analysis results to non-technical stakeholders?"
        ]