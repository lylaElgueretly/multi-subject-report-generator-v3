# =========================================
# MULTI-SUBJECT REPORT COMMENT GENERATOR - Secure Streamlit Version
# Supports Year 5, 7 & 8; Subjects: English, Maths, Science
# =========================================

import random
import streamlit as st
from docx import Document
import tempfile, os, time, io
from datetime import datetime, timedelta
import pandas as pd
import re

# ========== SETTINGS ==========
TARGET_CHARS = 499
MAX_FILE_SIZE_MB = 5
MAX_ROWS_PER_UPLOAD = 100
RATE_LIMIT_SECONDS = 10

st.set_page_config(
    page_title="🔒 Secure Report Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session
if 'app_initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.app_initialized = True
    st.session_state.upload_count = 0
    st.session_state.last_upload_time = datetime.now()
    st.session_state.generated_files = []

# ========== IMPORT STATEMENTS ==========
try:
    # Year 5
    from statements_year5_English import (
        opening_phrases as eng_opening_phrases,
        attitude_bank as eng_attitude_bank,
        reading_bank as eng_reading_bank,
        writing_bank as eng_writing_bank,
        reading_target_bank as eng_reading_target_bank,
        writing_target_bank as eng_writing_target_bank,
        closer_bank as eng_closer_bank
    )
    from statements_year5_Maths import (
        opening_phrases as maths_opening_phrases,
        attitude_bank as maths_attitude_bank,
        number_bank as maths_achievement_bank,
        problem_solving_bank as maths_problem_solving_bank,
        target_bank as maths_target_bank,
        closer_bank as maths_closer_bank
    )
    from statements_year5_Science import (
        opening_phrases as sci_opening_phrases,
        attitude_bank as sci_attitude_bank,
        science_bank as sci_achievement_bank,
        target_bank as sci_target_bank,
        closer_bank as sci_closer_bank
    )

    # Years 7 & 8 English
    from statements_year7_English import (
        opening_phrases as opening_7_eng,
        attitude_bank as attitude_7_eng,
        reading_bank as reading_7_eng,
        writing_bank as writing_7_eng,
        reading_target_bank as target_7_eng,
        writing_target_bank as target_write_7_eng,
        closer_bank as closer_7_eng
    )
    from statements_year8_English import (
        opening_phrases as opening_8_eng,
        attitude_bank as attitude_8_eng,
        reading_bank as reading_8_eng,
        writing_bank as writing_8_eng,
        reading_target_bank as target_8_eng,
        writing_target_bank as target_write_8_eng,
        closer_bank as closer_8_eng
    )
    
    # Years 7 & 8 Maths
    from statements_year7_Maths import (
        opening_phrases as opening_7_maths,
        attitude_bank as attitude_7_maths,
        number_and_algebra_bank as number_algebra_7_maths,
        geometry_and_measurement_bank as geometry_measurement_7_maths,
        problem_solving_and_reasoning_bank as problem_solving_7_maths,
        target_bank as target_7_maths,
        closer_bank as closer_7_maths
    )
    from statements_year8_Maths import (
        opening_phrases as opening_8_maths,
        attitude_bank as attitude_8_maths,
        maths_bank as maths_8_maths,
        target_bank as target_8_maths,
        closer_bank as closer_8_maths
    )
    
    # Years 7 & 8 Science
    from statements_year7_Science import (
        opening_phrases as opening_7_sci,
        attitude_bank as attitude_7_sci,
        science_bank as science_7_sci,
        target_bank as target_7_sci,
        closer_bank as closer_7_sci
    )
    from statements_year8_Science import (
        opening_phrases as opening_8_sci,
        attitude_bank as attitude_8_sci,
        science_bank as science_8_sci,
        target_bank as target_8_sci,
        closer_bank as closer_8_sci
    )

except ImportError as e:
    st.error(f"Missing required statement files: {e}")
    st.stop()

# ========== SECURITY FUNCTIONS ==========
def validate_upload_rate():
    time_since_last = datetime.now() - st.session_state.last_upload_time
    if time_since_last < timedelta(seconds=RATE_LIMIT_SECONDS):
        wait_time = RATE_LIMIT_SECONDS - time_since_last.seconds
        st.error(f"Please wait {wait_time} seconds before uploading again")
        return False
    return True

def sanitize_input(text, max_length=100):
    if not text:
        return ""
    sanitized = ''.join(c for c in text if c.isalnum() or c in " .'-")
    return sanitized[:max_length].strip().title()

def validate_file(file):
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return False, f"File too large (max {MAX_FILE_SIZE_MB}MB)"
    if not file.name.lower().endswith('.csv'):
        return False, "Only CSV files allowed"
    return True, ""

def process_csv_securely(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp:
        tmp.write(uploaded_file.getvalue())
        temp_path = tmp.name
    try:
        df = pd.read_csv(temp_path, nrows=MAX_ROWS_PER_UPLOAD + 1)
        if len(df) > MAX_ROWS_PER_UPLOAD:
            st.warning(f"Only processing first {MAX_ROWS_PER_UPLOAD} rows")
            df = df.head(MAX_ROWS_PER_UPLOAD)
        if 'Student Name' in df.columns:
            df['Student Name'] = df['Student Name'].apply(lambda x: sanitize_input(str(x)))
        return df
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return None
    finally:
        try: os.unlink(temp_path)
        except: pass

# ========== HELPER FUNCTIONS ==========
def get_pronouns(gender):
    gender = gender.lower()
    if gender == "male": return "he","his"
    elif gender == "female": return "she","her"
    return "they","their"

def lowercase_first(text):
    return text[0].lower() + text[1:] if text else ""

def truncate_comment(comment, target=TARGET_CHARS):
    if len(comment) <= target: return comment
    truncated = comment[:target].rstrip(" ,;.")
    if "." in truncated: truncated = truncated[:truncated.rfind(".")+1]
    return truncated

def fix_pronouns_in_text(text, pronoun, possessive):
    if not text: return text
    text = re.sub(r'\bhe\b', pronoun, text, flags=re.IGNORECASE)
    text = re.sub(r'\bHe\b', pronoun.capitalize(), text)
    text = re.sub(r'\bhis\b', possessive, text, flags=re.IGNORECASE)
    text = re.sub(r'\bHis\b', possessive.capitalize(), text)
    text = re.sub(r'\bhim\b', pronoun, text, flags=re.IGNORECASE)
    text = re.sub(r'\bHim\b', pronoun.capitalize(), text)
    text = re.sub(r'\bhimself\b', f"{pronoun}self", text, flags=re.IGNORECASE)
    text = re.sub(r'\bherself\b', f"{pronoun}self", text, flags=re.IGNORECASE)
    return text

# ========== COMMENT GENERATOR ==========
def generate_comment(subject, year, name, gender, att, achieve, target, pronouns, attitude_target=""):
    p, p_poss = pronouns
    name = sanitize_input(name)

    # --- Select statement banks ---
    if year == 5:
        if subject == "English":
            opening = random.choice(eng_opening_phrases)
            attitude_text = fix_pronouns_in_text(eng_attitude_bank[att], p, p_poss)
            reading_text = fix_pronouns_in_text(eng_reading_bank[achieve], p, p_poss)
            writing_text = fix_pronouns_in_text(eng_writing_bank[achieve], p, p_poss)
            reading_target_text = fix_pronouns_in_text(eng_reading_target_bank[target], p, p_poss)
            writing_target_text = fix_pronouns_in_text(eng_writing_target_bank[target], p, p_poss)
            closer_sentence = random.choice(eng_closer_bank)

        elif subject == "Maths":
            opening = random.choice(maths_opening_phrases)
            attitude_text = fix_pronouns_in_text(maths_attitude_bank[att], p, p_poss)
            reading_text = fix_pronouns_in_text(maths_achievement_bank[achieve], p, p_poss)
            writing_text = ""  # not used
            reading_target_text = fix_pronouns_in_text(maths_target_bank[target], p, p_poss)
            writing_target_text = ""
            closer_sentence = random.choice(maths_closer_bank)

        else:  # Science
            opening = random.choice(sci_opening_phrases)
            attitude_text = fix_pronouns_in_text(sci_attitude_bank[att], p, p_poss)
            reading_text = fix_pronouns_in_text(sci_achievement_bank[achieve], p, p_poss)
            writing_text = ""
            reading_target_text = fix_pronouns_in_text(sci_target_bank[target], p, p_poss)
            writing_target_text = ""
            closer_sentence = random.choice(sci_closer_bank)

    else:
        # Years 7 & 8
        if subject == "English":
            if year == 7:
                opening = random.choice(opening_7_eng)
                attitude_text = fix_pronouns_in_text(attitude_7_eng[att], p, p_poss)
                reading_text = fix_pronouns_in_text(reading_7_eng[achieve], p, p_poss)
                writing_text = fix_pronouns_in_text(writing_7_eng[achieve], p, p_poss)
                reading_target_text = fix_pronouns_in_text(target_7_eng[target], p, p_poss)
                writing_target_text = fix_pronouns_in_text(target_write_7_eng[target], p, p_poss)
                closer_sentence = random.choice(closer_7_eng)
            else:
                opening = random.choice(opening_8_eng)
                attitude_text = fix_pronouns_in_text(attitude_8_eng[att], p, p_poss)
                reading_text = fix_pronouns_in_text(reading_8_eng[achieve], p, p_poss)
                writing_text = fix_pronouns_in_text(writing_8_eng[achieve], p, p_poss)
                reading_target_text = fix_pronouns_in_text(target_8_eng[target], p, p_poss)
                writing_target_text = fix_pronouns_in_text(target_write_8_eng[target], p, p_poss)
                closer_sentence = random.choice(closer_8_eng)
        
        elif subject == "Maths":
            if year == 7:
                opening = random.choice(opening_7_maths)
                attitude_text = fix_pronouns_in_text(attitude_7_maths[att], p, p_poss)
                # Combine achievement areas for comprehensive comment
                achievement_parts = []
                if achieve in number_algebra_7_maths:
                    achievement_parts.append(fix_pronouns_in_text(number_algebra_7_maths[achieve], p, p_poss))
                if achieve in problem_solving_7_maths:
                    achievement_parts.append(fix_pronouns_in_text(problem_solving_7_maths[achieve], p, p_poss))
                reading_text = ". ".join(achievement_parts)
                writing_text = ""
                reading_target_text = fix_pronouns_in_text(target_7_maths[target], p, p_poss)
                writing_target_text = ""
                closer_sentence = random.choice(closer_7_maths)
            else:
                opening = random.choice(opening_8_maths)
                attitude_text = fix_pronouns_in_text(attitude_8_maths[att].replace("{name}", name), p, p_poss)
                reading_text = fix_pronouns_in_text(maths_8_maths[achieve].replace("{name}", name), p, p_poss)
                writing_text = ""
                reading_target_text = fix_pronouns_in_text(target_8_maths[target].replace("{name}", name), p, p_poss)
                writing_target_text = ""
                closer_sentence = random.choice([c.replace("{name}", name) for c in closer_8_maths])
        
        else:  # Science
            if year == 7:
                opening = random.choice(opening_7_sci)
                attitude_text = fix_pronouns_in_text(attitude_7_sci[att], p, p_poss)
                reading_text = fix_pronouns_in_text(science_7_sci[achieve], p, p_poss)
                writing_text = ""
                reading_target_text = fix_pronouns_in_text(target_7_sci[target], p, p_poss)
                writing_target_text = ""
                closer_sentence = random.choice(closer_7_sci)
            else:
                opening = random.choice(opening_8_sci)
                attitude_text = fix_pronouns_in_text(attitude_8_sci[att], p, p_poss)
                reading_text = fix_pronouns_in_text(science_8_sci[achieve], p, p_poss)
                writing_text = ""
                reading_target_text = fix_pronouns_in_text(target_8_sci[target], p, p_poss)
                writing_target_text = ""
                closer_sentence = random.choice(closer_8_sci)

    attitude_target_sentence = f" {attitude_target.strip()}" if attitude_target else ""

    comment_parts = [
        f"{opening} {name} {attitude_text}{attitude_target_sentence}",
        reading_text,
        writing_text,
        f"For the next term, {p} should {lowercase_first(reading_target_text)}" if reading_target_text else "",
        f"Additionally, {p} should {lowercase_first(writing_target_text)}" if writing_target_text else "",
        closer_sentence
    ]

    comment = " ".join([c for c in comment_parts if c])
    comment = truncate_comment(comment, TARGET_CHARS)
    if not comment.endswith('.'):
        comment = comment.rstrip(' ,;') + '.'
    return comment

# ========== DOCUMENT GENERATION ==========
def generate_docx(comments_df):
    doc = Document()
    doc.add_heading('Student Report Comments', 0)
    
    for _, row in comments_df.iterrows():
        doc.add_heading(f"{row['Student Name']} - {row['Subject']} (Year {row['Year']})", level=2)
        doc.add_paragraph(row['Generated Comment'])
        doc.add_paragraph()  # Add spacing
    
    return doc

# ========== APP LAYOUT ==========
st.title("📚 Multi-Subject Report Comment Generator")
st.caption(f"~{TARGET_CHARS} characters per comment • Secure • No data retention")

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Configuration")
    
    mode = st.radio("Mode:", ["Single Student", "Bulk Upload (CSV)"], index=0)
    
    if mode == "Single Student":
        year = st.selectbox("Year Group:", [5, 7, 8])
        subject = st.selectbox("Subject:", ["English", "Maths", "Science"])
        name = st.text_input("Student Name:", placeholder="Enter full name")
        gender = st.selectbox("Gender/Pronouns:", ["Male", "Female", "Other"])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            attitude_score = st.slider("Attitude:", 0, 90, 70, step=5)
        with col2:
            achievement_score = st.slider("Achievement:", 0, 90, 70, step=5)
        with col3:
            target_score = st.slider("Target:", 0, 90, 70, step=5)
        
        attitude_target = st.text_area("Custom Attitude Target (optional):", 
                                      placeholder="Add specific behavior target...",
                                      height=60)
        
        if st.button("Generate Comment", type="primary", use_container_width=True):
            if name.strip():
                pronouns = get_pronouns(gender)
                comment = generate_comment(
                    subject=subject,
                    year=year,
                    name=name,
                    gender=gender,
                    att=attitude_score,
                    achieve=achievement_score,
                    target=target_score,
                    pronouns=pronouns,
                    attitude_target=attitude_target
                )
                
                st.session_state.generated_comment = comment
                st.session_state.student_info = {
                    "name": name,
                    "subject": subject,
                    "year": year
                }
            else:
                st.error("Please enter a student name")
    
    else:  # Bulk Upload mode
        st.info("Upload a CSV file with columns: 'Student Name', 'Year', 'Subject', 'Gender', 'Attitude', 'Achievement', 'Target'")
        uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
        
        if uploaded_file:
            if validate_upload_rate():
                ok, msg = validate_file(uploaded_file)
                if ok:
                    df = process_csv_securely(uploaded_file)
                    if df is not None:
                        st.session_state.upload_df = df
                        st.session_state.last_upload_time = datetime.now()
                        st.session_state.upload_count += 1
                        
                        # Display preview
                        with st.expander("Preview first 5 rows"):
                            st.dataframe(df.head(), use_container_width=True)
                        
                        required_cols = ['Student Name', 'Year', 'Subject', 'Gender', 'Attitude', 'Achievement', 'Target']
                        missing = [col for col in required_cols if col not in df.columns]
                        
                        if missing:
                            st.error(f"Missing columns: {', '.join(missing)}")
                        else:
                            if st.button("Generate All Comments", type="primary", use_container_width=True):
                                with st.spinner("Generating comments..."):
                                    results = []
                                    for _, row in df.iterrows():
                                        pronouns = get_pronouns(str(row['Gender']))
                                        comment = generate_comment(
                                            subject=str(row['Subject']),
                                            year=int(row['Year']),
                                            name=str(row['Student Name']),
                                            gender=str(row['Gender']),
                                            att=int(row['Attitude']),
                                            achieve=int(row['Achievement']),
                                            target=int(row['Target']),
                                            pronouns=pronouns
                                        )
                                        results.append({
                                            'Student Name': row['Student Name'],
                                            'Year': row['Year'],
                                            'Subject': row['Subject'],
                                            'Generated Comment': comment,
                                            'Length': len(comment)
                                        })
                                    
                                    results_df = pd.DataFrame(results)
                                    st.session_state.bulk_results = results_df
                else:
                    st.error(msg)

# ========== MAIN AREA ==========
if mode == "Single Student" and 'generated_comment' in st.session_state:
    st.subheader(f"Generated Comment for {st.session_state.student_info['name']}")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.code(st.session_state.generated_comment, language=None)
    with col2:
        st.metric("Character Count", len(st.session_state.generated_comment))
        if abs(len(st.session_state.generated_comment) - TARGET_CHARS) > 50:
            st.warning(f"Target: ~{TARGET_CHARS} chars")
    
    # Download buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            label="📄 Download as .txt",
            data=st.session_state.generated_comment,
            file_name=f"{st.session_state.student_info['name']}_{st.session_state.student_info['subject']}_comment.txt",
            mime="text/plain"
        )
    with col2:
        # Create simple DOCX
        doc = Document()
        doc.add_paragraph(st.session_state.generated_comment)
        bio = io.BytesIO()
        doc.save(bio)
        
        st.download_button(
            label="📝 Download as .docx",
            data=bio.getvalue(),
            file_name=f"{st.session_state.student_info['name']}_{st.session_state.student_info['subject']}_comment.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    with col3:
        if st.button("🔄 Generate Another"):
            del st.session_state.generated_comment
            st.rerun()

elif mode == "Bulk Upload" and 'bulk_results' in st.session_state:
    st.subheader("📊 Bulk Results")
    
    results_df = st.session_state.bulk_results
    st.dataframe(results_df[['Student Name', 'Year', 'Subject', 'Length', 'Generated Comment']], 
                 use_container_width=True, hide_index=True)
    
    # Summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Comments", len(results_df))
    with col2:
        avg_len = results_df['Length'].mean()
        st.metric("Avg. Length", f"{avg_len:.0f} chars")
    with col3:
        within_target = ((results_df['Length'] >= TARGET_CHARS-50) & 
                        (results_df['Length'] <= TARGET_CHARS+50)).sum()
        st.metric("Within Target", f"{within_target}/{len(results_df)}")
    
    # Download options
    st.subheader("📥 Export Options")
    
    col1, col2 = st.columns(2)
    with col1:
        csv_data = results_df.to_csv(index=False)
        st.download_button(
            label="📊 Download as CSV",
            data=csv_data,
            file_name=f"report_comments_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        if st.button("📝 Generate DOCX Report", use_container_width=True):
            doc = generate_docx(results_df)
            bio = io.BytesIO()
            doc.save(bio)
            
            st.download_button(
                label="📥 Download DOCX",
                data=bio.getvalue(),
                file_name=f"report_comments_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
    
    if st.button("🗑️ Clear Results", type="secondary"):
        del st.session_state.bulk_results
        if 'upload_df' in st.session_state:
            del st.session_state.upload_df
        st.rerun()

else:
    # Welcome/Instructions
    st.markdown("""
    ## 📋 Welcome to the Report Comment Generator
    
    This tool helps teachers generate consistent, curriculum-aligned report comments for:
    
    - **Year Groups:** 5, 7, 8
    - **Subjects:** English, Maths, Science
    - **Modes:** Single student or bulk upload
    
    ### 🚀 Quick Start
    
    1. **Select mode** in the sidebar (Single or Bulk)
    2. **Configure** student details and scores
    3. **Generate** and download comments
    
    ### 📁 Bulk Upload Format
    
    For bulk processing, prepare a CSV with these columns:
    
    | Student Name | Year | Subject | Gender | Attitude | Achievement | Target |
    |--------------|------|---------|--------|----------|-------------|--------|
    | John Smith   | 7    | English | Male   | 85       | 80          | 75     |
    | Emma Jones   | 8    | Maths   | Female | 90       | 85          | 80     |
    
    ### 🔒 Security Features
    
    - Rate limiting on uploads
    - Input sanitization
    - No data retention
    - File size limits
    
    ---
    
    *Developed for educational use • UK National Curriculum aligned*
    """)

# ========== FOOTER ==========
st.divider()
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.caption(f"© {datetime.now().year} • Secure Report Generator v2.0")
with col2:
    st.caption(f"Rate limit: {RATE_LIMIT_SECONDS}s")
with col3:
    if 'upload_count' in st.session_state:
        st.caption(f"Uploads: {st.session_state.upload_count}")
