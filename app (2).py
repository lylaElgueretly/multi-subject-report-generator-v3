# =========================================
# MULTI-SUBJECT REPORT COMMENT GENERATOR - Secure Streamlit Version
# Supports English, Math, Science, Years 5, 7 & 8
# =========================================

import random
import streamlit as st
from docx import Document
import tempfile, os, time, io, re
from datetime import datetime, timedelta
import pandas as pd

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

# ========== SESSION INIT ==========
if 'app_initialized' not in st.session_state:
    st.session_state.clear()
    st.session_state.app_initialized = True
    st.session_state.upload_count = 0
    st.session_state.last_upload_time = datetime.now()
    st.session_state.generated_files = []

# ========== IMPORT STATEMENTS ==========
subjects = ["English", "Math", "Science"]
years = [5, 7, 8]

opening_banks = {}
attitude_banks = {}
reading_banks = {}
writing_banks = {}
reading_target_banks = {}
writing_target_banks = {}
closer_banks = {}

# Dynamically import statement files
for subj in subjects:
    opening_banks[subj] = {}
    attitude_banks[subj] = {}
    reading_banks[subj] = {}
    writing_banks[subj] = {}
    reading_target_banks[subj] = {}
    writing_target_banks[subj] = {}
    closer_banks[subj] = {}
    for yr in years:
        try:
            mod = __import__(f"statements_year{yr}_{subj}", fromlist=[
                'opening_phrases','attitude_bank','reading_bank','writing_bank',
                'reading_target_bank','writing_target_bank','closer_bank'
            ])
            opening_banks[subj][yr] = getattr(mod,'opening_phrases',[])
            attitude_banks[subj][yr] = getattr(mod,'attitude_bank',{})
            reading_banks[subj][yr] = getattr(mod,'reading_bank',{})
            writing_banks[subj][yr] = getattr(mod,'writing_bank',{})
            reading_target_banks[subj][yr] = getattr(mod,'reading_target_bank',{})
            writing_target_banks[subj][yr] = getattr(mod,'writing_target_bank',{})
            closer_banks[subj][yr] = getattr(mod,'closer_bank',[])
        except ImportError:
            st.warning(f"Missing statement file: Year {yr} {subj}, some comments may fail.")
            opening_banks[subj][yr] = []
            attitude_banks[subj][yr] = {}
            reading_banks[subj][yr] = {}
            writing_banks[subj][yr] = {}
            reading_target_banks[subj][yr] = {}
            writing_target_banks[subj][yr] = {}
            closer_banks[subj][yr] = []

# ========== SECURITY FUNCTIONS ==========
def validate_upload_rate():
    delta = datetime.now() - st.session_state.last_upload_time
    if delta < timedelta(seconds=RATE_LIMIT_SECONDS):
        st.error(f"Please wait {RATE_LIMIT_SECONDS - delta.seconds} seconds before uploading again")
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
        df = pd.read_csv(temp_path, nrows=MAX_ROWS_PER_UPLOAD+1)
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

def get_pronouns(gender):
    g = gender.lower()
    if g == "male": return "he","his"
    if g == "female": return "she","her"
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

# ========== COMMENT GENERATION ==========
def generate_comment(subject, year, name, gender, att, achieve, target, pronouns, attitude_target=None):
    p, p_poss = pronouns
    name = sanitize_input(name)

    opening = random.choice(opening_banks[subject][year]) if opening_banks[subject][year] else ""
    attitude_text = fix_pronouns_in_text(attitude_banks[subject][year].get(att,""), p, p_poss)
    attitude_sentence = f"{opening} {name} {attitude_text}".strip()
    if attitude_sentence and not attitude_sentence.endswith('.'): attitude_sentence += '.'

    reading_text = fix_pronouns_in_text(reading_banks[subject][year].get(achieve,""), p, p_poss)
    if reading_text and reading_text[0].islower(): reading_text = f"{p} {reading_text}"
    reading_sentence = f"In reading, {reading_text}" if subject=="English" else reading_text
    if reading_sentence and not reading_sentence.endswith('.'): reading_sentence += '.'

    writing_text = fix_pronouns_in_text(writing_banks[subject][year].get(achieve,""), p, p_poss)
    if writing_text and writing_text[0].islower(): writing_text = f"{p} {writing_text}"
    writing_sentence = f"In writing, {writing_text}" if subject=="English" else ""

    reading_target_text = fix_pronouns_in_text(reading_target_banks[subject][year].get(target,""), p, p_poss)
    reading_target_sentence = f"For the next term, {p} should {lowercase_first(reading_target_text)}" if subject=="English" else f"For the next term, {p} should {lowercase_first(reading_target_text)}"
    if reading_target_sentence and not reading_target_sentence.endswith('.'): reading_target_sentence += '.'

    writing_target_text = fix_pronouns_in_text(writing_target_banks[subject][year].get(target,""), p, p_poss)
    writing_target_sentence = f"Additionally, {p} should {lowercase_first(writing_target_text)}" if subject=="English" else ""

    closer_sentence = random.choice(closer_banks[subject][year]) if closer_banks[subject][year] else ""

    if attitude_target:
        attitude_target_sentence = f" {lowercase_first(sanitize_input(attitude_target))}"
        if not attitude_target_sentence.endswith('.'): attitude_target_sentence += '.'
    else:
        attitude_target_sentence = ""

    comment_parts = [attitude_sentence + attitude_target_sentence,
                     reading_sentence,
                     writing_sentence,
                     reading_target_sentence,
                     writing_target_sentence,
                     closer_sentence]

    comment = " ".join([c for c in comment_parts if c])
    if not comment.endswith('.'): comment += '.'
    comment = truncate_comment(comment, TARGET_CHARS)
    if not comment.endswith('.'): comment = comment.rstrip(' ,;') + '.'

    return comment

# =========================================
# --- Streamlit UI remains largely unchanged ---
# Update dropdowns for Subjects and Years

# In Single Student mode:
# subject = st.selectbox("Subject", subjects)
# year = st.selectbox("Year", years)

# In CSV validation info:
# Subject: English/Math/Science
# Year: 5,7,8

# The rest of the app (Batch Upload, Download, Privacy, Footer) remains unchanged
# All calls to generate_comment() now work for any subject/year combination

