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

# Konfigurasi halaman
st.set_page_config(
    page_title="Job Tracker AI",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inisialisasi session state
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
    st.subheader("📄 Upload CV Kamu")
    uploaded_file = st.file_uploader("Pilih file PDF", type="pdf", key="cv_uploader")
    
    if uploaded_file and not st.session_state.resume_processed:
        with st.spinner("Membaca PDF..."):
            # Ekstrak teks dari PDF
            resume_text = extract_text_from_pdf(uploaded_file)
            
            # Ekstrak data dengan Groq AI
            with st.spinner("AI sedang menganalisis CV..."):
                extracted = extract_resume_data(resume_text)
            
            if "error" not in extracted:
                # Simpan ke database
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
                st.success("✅ CV berhasil diproses!")
                st.rerun()
            else:
                st.error(f"Error: {extracted.get('error')}")
    
    # Tampilkan data CV jika sudah diproses
    if st.session_state.resume_data:
        st.markdown("---")
        st.subheader("👤 Data CV")
        st.write(f"**Nama:** {st.session_state.resume_data['name']}")
        st.write(f"**Email:** {st.session_state.resume_data['email']}")
        st.write("**Skills:**")
        skills = st.session_state.resume_data.get('skills', [])
        for skill in skills[:5]:
            st.markdown(f"- {skill}")
        if len(skills) > 5:
            st.write(f"... dan {len(skills)-5} skill lainnya")
        
        if st.button("🔄 Upload CV Baru"):
            st.session_state.resume_processed = False
            st.session_state.resume_data = None
            st.rerun()
    
    st.markdown("---")
    st.caption("Made with ❤️ using Streamlit + Groq AI")

# ==================== MAIN CONTENT ====================
# Tab navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "💼 Log Lamaran", 
    "🎯 AI Match & Interview Prep",
    "📝 Riwayat Lamaran"
])

# ==================== TAB 1: DASHBOARD ====================
with tab1:
    st.header("📊 Dashboard Statistik")
    
    # Cek apakah ada resume
    if not st.session_state.resume_data:
        st.warning("⚠️ Silakan upload CV terlebih dahulu di sidebar kiri!")
    else:
        stats = get_dashboard_stats()
        
        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Lamaran", stats['total'])
        with col2:
            st.metric("Rata-rata Match Score", f"{stats['avg_score']}%")
        with col3:
            applied = stats['status_counts'].get('applied', 0)
            st.metric("Dalam Proses", applied)
        with col4:
            interview = stats['status_counts'].get('interview', 0)
            st.metric("Dapat Interview", interview)
        
        st.markdown("---")
        
        # Chart status distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Status Lamaran")
            if stats['status_counts']:
                df_status = pd.DataFrame({
                    'Status': list(stats['status_counts'].keys()),
                    'Jumlah': list(stats['status_counts'].values())
                })
                fig = px.pie(df_status, values='Jumlah', names='Status', 
                            title="Distribusi Status Lamaran",
                            color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada data lamaran")
        
        with col2:
            st.subheader("Match Score per Lamaran")
            jobs = get_all_jobs()
            if jobs:
                df_scores = pd.DataFrame([{
                    'Perusahaan': j['company'],
                    'Match Score': j['match_score'] or 0
                } for j in jobs])
                fig = px.bar(df_scores, x='Perusahaan', y='Match Score',
                            title="Skor Kecocokan CV vs Job Desc",
                            color='Match Score',
                            color_continuous_scale='Viridis')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Belum ada data lamaran")

# ==================== TAB 2: LOG LAMARAN ====================
with tab2:
    st.header("💼 Tambah Lamaran Baru")
    
    if not st.session_state.resume_data:
        st.warning("⚠️ Silakan upload CV terlebih dahulu di sidebar!")
    else:
        with st.form("job_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                company = st.text_input("Nama Perusahaan *", placeholder="Contoh: PT Teknologi Indonesia")
                role = st.text_input("Posisi / Role *", placeholder="Contoh: Data Scientist")
                status = st.selectbox("Status Lamaran", 
                                     ["applied", "interview", "technical_test", "rejected", "offer"])
            
            with col2:
                deadline = st.date_input("Deadline (opsional)", value=None)
                applied_date = st.date_input("Tanggal Lamar", value=date.today())
            
            job_description = st.text_area("Deskripsi Pekerjaan (Job Description) *", 
                                          height=200,
                                          placeholder="Tempelkan job description di sini...")
            
            notes = st.text_area("Catatan Pribadi (opsional)", 
                                placeholder="Informasi tambahan tentang lamaran ini...")
            
            submitted = st.form_submit_button("💾 Simpan Lamaran", use_container_width=True)
            
            if submitted:
                if not company or not role or not job_description:
                    st.error("Mohon isi semua field yang wajib (*)")
                else:
                    with st.spinner("AI sedang menganalisis kecocokan..."):
                        # Hitung match score dengan Groq
                        match_result = calculate_match_score(
                            resume_text=st.session_state.resume_data['text'],
                            job_description=job_description,
                            job_role=role
                        )
                    
                    # Simpan ke database
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
                    
                    st.success(f"✅ Lamaran ke **{company}** berhasil disimpan!")
                    st.info(f"🎯 AI Match Score: **{match_result.get('score', 0)}%**")
                    
                    # Tampilkan feedback singkat
                    with st.expander("Lihat Analisis AI"):
                        st.write(match_result.get('feedback', ''))
                        if match_result.get('strengths'):
                            st.write("**Kelebihan:**")
                            for s in match_result['strengths']:
                                st.write(f"✓ {s}")
                        if match_result.get('tips'):
                            st.write("**Tips Perbaikan:**")
                            for t in match_result['tips']:
                                st.write(f"→ {t}")

# ==================== TAB 3: AI MATCH & INTERVIEW PREP ====================
with tab3:
    st.header("🎯 AI Match Analysis & Interview Preparation")
    
    if not st.session_state.resume_data:
        st.warning("⚠️ Silakan upload CV terlebih dahulu!")
    else:
        # Pilih job yang sudah ada
        jobs = get_all_jobs()
        
        if not jobs:
            st.info("Belum ada lamaran yang disimpan. Silakan tambahkan lamaran di tab 'Log Lamaran' terlebih dahulu.")
        else:
            job_options = {f"{j['company']} - {j['role']}": j['id'] for j in jobs}
            selected_job_label = st.selectbox("Pilih lamaran untuk dianalisis:", list(job_options.keys()))
            selected_job_id = job_options[selected_job_label]
            
            job_detail = get_job_by_id(selected_job_id)
            
            if job_detail:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Match Score Detail")
                    score = job_detail['match_score'] or 0
                    st.progress(score/100)
                    st.metric("Match Score", f"{score}%")
                    
                    if job_detail['match_feedback']:
                        st.write("**Feedback AI:**")
                        st.info(job_detail['match_feedback'])
                
                with col2:
                    st.subheader("💡 Tips Perbaikan CV")
                    
                    # Hitung ulang match untuk dapat tips
                    if st.button("🔄 Refresh Analisis & Tips", use_container_width=True):
                        with st.spinner("AI sedang menganalisis ulang..."):
                            new_match = calculate_match_score(
                                resume_text=st.session_state.resume_data['text'],
                                job_description=job_detail['job_description'],
                                job_role=job_detail['role']
                            )
                        if new_match.get('tips'):
                            for tip in new_match['tips']:
                                st.write(f"✓ {tip}")
                        if new_match.get('weaknesses'):
                            st.write("\n**Area yang perlu ditingkatkan:**")
                            for w in new_match['weaknesses']:
                                st.write(f"⚠️ {w}")
                    else:
                        st.write("Klik tombol di atas untuk mendapatkan tips dari AI")
                
                # Interview preparation section
                st.markdown("---")
                st.subheader("🎤 Interview Preparation")
                
                if st.button("🤖 Generate Pertanyaan Interview", use_container_width=True):
                    with st.spinner("AI sedang membuat pertanyaan interview..."):
                        questions = generate_interview_questions(
                            job_description=job_detail['job_description'],
                            job_role=job_detail['role'],
                            company=job_detail['company']
                        )
                    
                    st.success("Berikut kemungkinan pertanyaan yang akan muncul:")
                    for i, q in enumerate(questions, 1):
                        with st.expander(f"Pertanyaan {i}"):
                            st.write(q)
                            st.text_area(f"Latihan jawaban {i}", 
                                       placeholder="Tulis jawabanmu di sini...",
                                       key=f"answer_{i}")

# ==================== TAB 4: RIWAYAT LAMARAN ====================
with tab4:
    st.header("📝 Riwayat Lamaran")
    
    jobs = get_all_jobs()
    
    if not jobs:
        st.info("Belum ada lamaran yang disimpan. Mulai tambahkan lamaran di tab 'Log Lamaran'!")
    else:
        # Tampilkan dalam tabel
        df = pd.DataFrame(jobs)
        df['applied_date'] = pd.to_datetime(df['applied_date']).dt.date
        
        # Rename columns
        df.columns = ['ID', 'Perusahaan', 'Posisi', 'Status', 'Match Score', 'Tanggal Lamar', 'Deadline']
        
        # Format status
        status_map = {
            'applied': '📤 Applied',
            'interview': '📞 Interview',
            'technical_test': '💻 Technical Test',
            'rejected': '❌ Rejected',
            'offer': '🎉 Offer'
        }
        df['Status'] = df['Status'].map(status_map).fillna(df['Status'])
        
        # Tampilkan dataframe
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Edit status
        st.markdown("---")
        st.subheader("✏️ Update Status Lamaran")
        
        col1, col2 = st.columns(2)
        with col1:
            job_to_update = st.selectbox("Pilih lamaran:", 
                                        options=[f"{j['company']} - {j['role']}" for j in jobs],
                                        key="update_select")
            selected_job = next(j for j in jobs if f"{j['company']} - {j['role']}" == job_to_update)
        
        with col2:
            new_status = st.selectbox("Status baru:", 
                                     ['applied', 'interview', 'technical_test', 'rejected', 'offer'],
                                     key="status_select")
            status_display = {
                'applied': '📤 Applied',
                'interview': '📞 Interview',
                'technical_test': '💻 Technical Test',
                'rejected': '❌ Rejected',
                'offer': '🎉 Offer'
            }
            st.write(f"Menjadi: **{status_display[new_status]}**")
        
        if st.button("✅ Update Status", use_container_width=True):
            update_job_status(selected_job['id'], new_status)
            st.success("Status berhasil diupdate!")
            st.rerun()
        
        # Export option
        st.markdown("---")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export ke CSV",
            data=csv,
            file_name=f"job_applications_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )