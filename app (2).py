# =========================================
# MULTI-SUBJECT REPORT COMMENT GENERATOR - Secure Streamlit Version
# Supports English, Maths, Science for Years 5, 7 & 8
# =========================================

import random
import streamlit as st
from docx import Document
import tempfile
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import io
import re

# ========== SECURITY & PRIVACY SETTINGS ==========
TARGET_CHARS = 499
MAX_FILE_SIZE_MB = 5
MAX_ROWS_PER_UPLOAD = 100
RATE_LIMIT_SECONDS = 10

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="🔒 Secure Report Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== SECURITY INITIALIZATION ==========
if 'app_initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.app_initialized = True
    st.session_state.upload_count = 0
    st.session_state.last_upload_time = datetime.now()
    st.session_state.generated_files = []

# ========== IMPORT STATEMENTS ==========
# Year 5
from statements_year5_English import *
from statements_year5_Maths import *
from statements_year5_Science import *

# Year 7
from statements_year7_English import *
from statements_year7_Maths import *
from statements_year7_science import *

# Year 8
from statements_year8_English import *
from statements_year8_Maths import *
from statements_year8_science import *

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
        try:
            os.unlink(temp_path)
        except:
            pass

# ========== HELPER FUNCTIONS ==========
def get_pronouns(gender):
    gender = gender.lower()
    if gender == "male":
        return "he", "his"
    elif gender == "female":
        return "she", "her"
    return "they", "their"

def lowercase_first(text):
    return text[0].lower() + text[1:] if text else ""

def truncate_comment(comment, target=TARGET_CHARS):
    if len(comment) <= target:
        return comment
    truncated = comment[:target].rstrip(" ,;.")
    if "." in truncated:
        truncated = truncated[:truncated.rfind(".")+1]
    return truncated

def fix_pronouns_in_text(text, pronoun, possessive):
    if not text:
        return text
    text = re.sub(r'\bhe\b', pronoun, text, flags=re.IGNORECASE)
    text = re.sub(r'\bHe\b', pronoun.capitalize(), text)
    text = re.sub(r'\bhis\b', possessive, text, flags=re.IGNORECASE)
    text = re.sub(r'\bHis\b', possessive.capitalize(), text)
    text = re.sub(r'\bhim\b', pronoun, text, flags=re.IGNORECASE)
    text = re.sub(r'\bHim\b', pronoun.capitalize(), text)
    text = re.sub(r'\bhimself\b', f"{pronoun}self", text, flags=re.IGNORECASE)
    text = re.sub(r'\bherself\b', f"{pronoun}self", text, flags=re.IGNORECASE)
    return text

# ========== COMMENT GENERATION ==========
def generate_comment(subject, year, name, gender, att, achieve, target, pronouns, attitude_target=None):
    p, p_poss = pronouns
    name = sanitize_input(name)

    # Determine bank variables dynamically
    subject_lower = subject.lower()
    bank_prefix = f"{subject_lower}_{year}"

    try:
        opening = random.choice(globals()[f"opening_{bank_prefix}"])
        attitude_text = fix_pronouns_in_text(globals()[f"attitude_{bank_prefix}"][att], p, p_poss)
        achievement_text = fix_pronouns_in_text(globals()[f"{subject_lower}_bank_{bank_prefix}"][achieve], p, p_poss)
        target_text = fix_pronouns_in_text(globals()[f"target_{bank_prefix}"][target], p, p_poss)
        target_write_text = globals().get(f"target_write_{bank_prefix}", {}).get(target, "")
        closer_sentence = random.choice(globals()[f"closer_{bank_prefix}"])
    except KeyError as e:
        st.error(f"Missing bank for {subject} Year {year}: {e}")
        return ""

    attitude_sentence = f"{opening} {name} {attitude_text}."
    reading_sentence = f"{p} {achievement_text}." if subject_lower != "science" else f"{achievement_text}."
    reading_target_sentence = f"For the next term, {p} should {lowercase_first(target_text)}."
    writing_target_sentence = f"Additionally, {p} should {lowercase_first(target_write_text)}." if target_write_text else ""

    if attitude_target:
        attitude_target_sentence = f" {lowercase_first(attitude_target.strip())}."
    else:
        attitude_target_sentence = ""

    comment_parts = [
        attitude_sentence + attitude_target_sentence,
        reading_sentence,
        reading_target_sentence,
        writing_target_sentence,
        closer_sentence
    ]

    comment = " ".join([c for c in comment_parts if c]).strip()
    comment = truncate_comment(comment)
    if not comment.endswith('.'):
        comment += '.'
    return comment

# ========== STREAMLIT LAYOUT ==========
with st.sidebar:
    st.title("📚 Navigation")
    app_mode = st.radio("Choose Mode", ["Single Student", "Batch Upload", "Privacy Info"])
    st.markdown("---")
    st.markdown("### 🔒 Privacy Features")
    st.info("- No data stored on servers\n- All processing in memory\n- Auto-deletion of temp files\n- Input sanitization\n- Rate limiting enabled")
    if st.button("🔄 Clear All Data", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.session_state.app_initialized = True
        st.session_state.upload_count = 0
        st.session_state.last_upload_time = datetime.now()
        st.success("All data cleared!")
        st.rerun()
    st.markdown("---")
    st.caption("v3.0 • Teacher-Focused Edition")

col1, col2 = st.columns([1, 4])
with col1:
    try:
        st.image("logo.png", use_column_width=True)
    except:
        st.markdown("<div style='text-align:center;font-size:72px;'>📚</div>", unsafe_allow_html=True)
with col2:
    st.title("Multi-Subject Report Comment Generator")
    st.caption("~499 characters per comment • Secure • No data retention")

# Continue with your existing "Single Student" and "Batch Upload" logic...
# ✅ Use `generate_comment(subject, year, name, gender, att, achieve, target, pronouns, attitude_target)` exactly as before
# ✅ All download and privacy sections remain identical
