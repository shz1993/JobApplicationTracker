"""
Job Application Tracker with AI
Streamlit + Neon + Groq
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime

# Import utilities
from utils.resume_parser import extract_text_from_pdf
from utils.groq_ai import extract_resume_data, calculate_match_score, generate_interview_questions
from utils.db_helper import (
    save_resume, get_latest_resume, save_job, get_all_jobs,
    update_job_status, get_job_by_id, get_dashboard_stats
)

# Page configuration
st.set_page_config(
    page_title="Job Tracker AI",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'resume_processed' not in st.session_state:
    st.session_state.resume_processed = False
if 'resume_data' not in st.session_state:
    st.session_state.resume_data = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Dashboard"

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/resume.png", width=50)
    st.title("📋 Job Tracker AI")
    st.markdown("---")
    
    # Upload CV Section
    st.subheader("📄 Upload Your CV")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="cv_uploader")
    
    if uploaded_file and not st.session_state.resume_processed:
        with st.spinner("Reading PDF..."):
            resume_text = extract_text_from_pdf(uploaded_file)
            
            with st.spinner("AI is analyzing your CV..."):
                extracted = extract_resume_data(resume_text)
            
            if "error" not in extracted:
                resume_id = save_resume(
                    file_name=uploaded_file.name,
                    extracted_text=resume_text,
                    name=extracted.get("name", ""),
                    email=extracted.get("email", ""),
                    skills=extracted.get("skills", [])
                )
                
                st.session_state.resume_processed = True
                st.session_state.resume_data = {
                    "name": extracted.get("name", ""),
                    "email": extracted.get("email", ""),
                    "skills": extracted.get("skills", []),
                    "text": resume_text,
                    "id": resume_id
                }
                st.success("✅ CV processed successfully!")
                st.rerun()
            else:
                st.error(f"Error: {extracted.get('error')}")
    
    if st.session_state.resume_data:
        st.markdown("---")
        st.subheader("👤 Your CV Data")
        st.write(f"**Name:** {st.session_state.resume_data['name']}")
        st.write(f"**Email:** {st.session_state.resume_data['email']}")
        st.write("**Skills:**")
        skills = st.session_state.resume_data.get('skills', [])
        for skill in skills[:5]:
            st.markdown(f"- {skill}")
        if len(skills) > 5:
            st.write(f"... and {len(skills)-5} more skills")
        
        if st.button("🔄 Upload New CV"):
            st.session_state.resume_processed = False
            st.session_state.resume_data = None
            st.rerun()
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit + Groq AI")

# ==================== MAIN CONTENT ====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "💼 Log Application", 
    "🎯 AI Match & Interview Prep",
    "📝 Application History"
])

# ==================== TAB 1: DASHBOARD ====================
with tab1:
    st.header("📊 Dashboard Statistics")
    
    if not st.session_state.resume_data:
        st.warning("⚠️ Please upload your CV in the left sidebar first!")
    else:
        stats = get_dashboard_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Applications", stats['total'])
        with col2:
            st.metric("Average Match Score", f"{stats['avg_score']}%")
        with col3:
            applied = stats['status_counts'].get('applied', 0)
            st.metric("In Progress", applied)
        with col4:
            interview = stats['status_counts'].get('interview', 0)
            st.metric("Got Interview", interview)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Application Status")
            if stats['status_counts']:
                df_status = pd.DataFrame({
                    'Status': list(stats['status_counts'].keys()),
                    'Count': list(stats['status_counts'].values())
                })
                fig = px.pie(df_status, values='Count', names='Status', 
                            title="Application Status Distribution",
                            color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No application data yet")
        
        with col2:
            st.subheader("Match Score per Company")
            jobs = get_all_jobs()
            if jobs:
                df_scores = pd.DataFrame([{
                    'Company': j['company'],
                    'Match Score': j['match_score'] or 0
                } for j in jobs])
                fig = px.bar(df_scores, x='Company', y='Match Score',
                            title="CV vs Job Description Match Score",
                            color='Match Score',
                            color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No application data yet")

# ==================== TAB 2: LOG APPLICATION ====================
with tab2:
    st.header("💼 Add New Application")
    
    if not st.session_state.resume_data:
        st.warning("⚠️ Please upload your CV in the sidebar first!")
    else:
        with st.form("job_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company = st.text_input("Company Name *", placeholder="Example: PT Teknologi Indonesia")
                role = st.text_input("Position / Role *", placeholder="Example: Data Scientist")
                status = st.selectbox("Application Status", 
                                     ["applied", "interview", "technical_test", "rejected", "offer"])
            
            with col2:
                deadline = st.date_input("Deadline (optional)", value=None)
                applied_date = st.date_input("Application Date", value=date.today())
            
            job_description = st.text_area("Job Description *", 
                                          height=200,
                                          placeholder="Paste the job description here...")
            
            notes = st.text_area("Personal Notes (optional)", 
                                placeholder="Additional information about this application...")
            
            submitted = st.form_submit_button("💾 Save Application", use_container_width=True)
            
            if submitted:
                if not company or not role or not job_description:
                    st.error("Please fill all required fields (*)")
                else:
                    with st.spinner("AI is analyzing fit..."):
                        match_result = calculate_match_score(
                            resume_text=st.session_state.resume_data['text'],
                            job_description=job_description,
                            job_role=role
                        )
                    
                    job_id = save_job(
                        company=company,
                        role=role,
                        job_description=job_description,
                        status=status,
                        match_score=match_result.get('score', 0),
                        match_feedback=match_result.get('feedback', ''),
                        deadline=deadline if deadline else None,
                        notes=notes
                    )
                    
                    st.success(f"✅ Application to **{company}** saved successfully!")
                    st.info(f"🎯 AI Match Score: **{match_result.get('score', 0)}%**")
                    
                    with st.expander("View AI Analysis"):
                        st.write(match_result.get('feedback', ''))
                        if match_result.get('strengths'):
                            st.write("**Strengths:**")
                            for s in match_result['strengths']:
                                st.write(f"✓ {s}")
                        if match_result.get('tips'):
                            st.write("**Improvement Tips:**")
                            for t in match_result['tips']:
                                st.write(f"→ {t}")

# ==================== TAB 3: AI MATCH & INTERVIEW PREP ====================
with tab3:
    st.header("🎯 AI Match Analysis & Interview Preparation")
    
    if not st.session_state.resume_data:
        st.warning("⚠️ Please upload your CV first!")
    else:
        jobs = get_all_jobs()
        
        if not jobs:
            st.info("No applications saved yet. Please add an application in the 'Log Application' tab first.")
        else:
            job_options = {f"{j['company']} - {j['role']}": j['id'] for j in jobs}
            selected_job_label = st.selectbox("Select application to analyze:", list(job_options.keys()))
            selected_job_id = job_options[selected_job_label]
            
            job_detail = get_job_by_id(selected_job_id)
            
            if job_detail:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Match Score Details")
                    score = job_detail['match_score'] or 0
                    st.progress(score/100)
                    st.metric("Match Score", f"{score}%")
                    
                    if job_detail['match_feedback']:
                        st.write("**AI Feedback:**")
                        st.info(job_detail['match_feedback'])
                
                with col2:
                    st.subheader("💡 CV Improvement Tips")
                    
                    if st.button("🔄 Refresh Analysis & Get Tips", use_container_width=True):
                        with st.spinner("AI is re-analyzing your CV..."):
                            new_match = calculate_match_score(
                                resume_text=st.session_state.resume_data['text'],
                                job_description=job_detail['job_description'],
                                job_role=job_detail['role']
                            )
                        
                        if new_match:
                            if new_match.get('tips'):
                                st.markdown("**💡 CV Improvement Tips:**")
                                for tip in new_match['tips']:
                                    st.markdown(f"✓ {tip}")
                            
                            if new_match.get('strengths'):
                                st.markdown("---")
                                st.markdown("**✅ Your CV Strengths:**")
                                for s in new_match['strengths']:
                                    st.markdown(f"• {s}")
                            
                            if new_match.get('weaknesses'):
                                st.markdown("---")
                                st.markdown("**⚠️ Areas to Improve:**")
                                for w in new_match['weaknesses']:
                                    st.markdown(f"• {w}")
                        else:
                            st.warning("Unable to analyze. Please try again.")
                    else:
                        st.info("👆 Click the button above to get CV improvement tips from AI")
                
                st.markdown("---")
                st.subheader("🎤 Interview Preparation")
                
                if st.button("🤖 Generate Interview Questions", use_container_width=True):
                    with st.spinner("AI is generating interview questions..."):
                        questions = generate_interview_questions(
                            job_description=job_detail['job_description'],
                            job_role=job_detail['role'],
                            company=job_detail['company']
                        )
                    
                    st.success("Here are possible interview questions:")
                    for i, q in enumerate(questions, 1):
                        with st.expander(f"Question {i}"):
                            st.write(q)
                            st.text_area(f"Practice your answer {i}", 
                                       placeholder="Write your answer here...",
                                       key=f"answer_{i}")

# ==================== TAB 4: APPLICATION HISTORY ====================
with tab4:
    st.header("📝 Application History")
    
    jobs = get_all_jobs()
    
    if not jobs:
        st.info("No applications saved yet. Start by adding an application in the 'Log Application' tab!")
    else:
        df = pd.DataFrame(jobs)
        df['applied_date'] = pd.to_datetime(df['applied_date']).dt.date
        df.columns = ['ID', 'Company', 'Position', 'Status', 'Match Score', 'Applied Date', 'Deadline']
        
        status_map = {
            'applied': '📤 Applied',
            'interview': '📞 Interview',
            'technical_test': '💻 Technical Test',
            'rejected': '❌ Rejected',
            'offer': '🎉 Offer'
        }
        df['Status'] = df['Status'].map(status_map).fillna(df['Status'])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("✏️ Update Application Status")
        
        col1, col2 = st.columns(2)
        with col1:
            job_to_update = st.selectbox("Select application:", 
                                        options=[f"{j['company']} - {j['role']}" for j in jobs],
                                        key="update_select")
            selected_job = next(j for j in jobs if f"{j['company']} - {j['role']}" == job_to_update)
        
        with col2:
            new_status = st.selectbox("New status:", 
                                     ['applied', 'interview', 'technical_test', 'rejected', 'offer'],
                                     key="status_select")
            status_display = {
                'applied': '📤 Applied',
                'interview': '📞 Interview',
                'technical_test': '💻 Technical Test',
                'rejected': '❌ Rejected',
                'offer': '🎉 Offer'
            }
            st.write(f"Change to: **{status_display[new_status]}**")
        
        if st.button("✅ Update Status", use_container_width=True):
            update_job_status(selected_job['id'], new_status)
            st.success("Status updated successfully!")
            st.rerun()
        
        st.markdown("---")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export to CSV",
            data=csv,
            file_name=f"job_applications_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )