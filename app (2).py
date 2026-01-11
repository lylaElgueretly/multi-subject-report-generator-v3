# =========================================
# MULTI-SUBJECT REPORT COMMENT GENERATOR - Secure Streamlit Version
# Supports English, Math, Science, Years 5, 7 & 8
# Enhanced with security, privacy, and UX features
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
try:
    # English
    from statements_year5_English import opening_phrases as opening_5_eng, attitude_bank as attitude_5_eng, reading_bank as reading_5_eng, writing_bank as writing_5_eng, reading_target_bank as target_5_eng, writing_target_bank as target_write_5_eng, closer_bank as closer_5_eng
    from statements_year7_English import opening_phrases as opening_7_eng, attitude_bank as attitude_7_eng, reading_bank as reading_7_eng, writing_bank as writing_7_eng, reading_target_bank as target_7_eng, writing_target_bank as target_write_7_eng, closer_bank as closer_7_eng
    from statements_year8_English import opening_phrases as opening_8_eng, attitude_bank as attitude_8_eng, reading_bank as reading_8_eng, writing_bank as writing_8_eng, reading_target_bank as target_8_eng, writing_target_bank as target_write_8_eng, closer_bank as closer_8_eng

    # Math
    from statements_year5_Math import opening_phrases as opening_5_math, attitude_bank as attitude_5_math, reading_bank as reading_5_math, writing_bank as writing_5_math, reading_target_bank as target_5_math, writing_target_bank as target_write_5_math, closer_bank as closer_5_math
    from statements_year7_Math import opening_phrases as opening_7_math, attitude_bank as attitude_7_math, reading_bank as reading_7_math, writing_bank as writing_7_math, reading_target_bank as target_7_math, writing_target_bank as target_write_7_math, closer_bank as closer_7_math
    from statements_year8_Math import opening_phrases as opening_8_math, attitude_bank as attitude_8_math, reading_bank as reading_8_math, writing_bank as writing_8_math, reading_target_bank as target_8_math, writing_target_bank as target_write_8_math, closer_bank as closer_8_math

    # Science
    from statements_year5_Science import opening_phrases as opening_5_sci, attitude_bank as attitude_5_sci, science_bank as science_5_sci, target_bank as target_5_sci, closer_bank as closer_5_sci
    from statements_year7_Science import opening_phrases as opening_7_sci, attitude_bank as attitude_7_sci, science_bank as science_7_sci, target_bank as target_7_sci, closer_bank as closer_7_sci
    from statements_year8_Science import opening_phrases as opening_8_sci, attitude_bank as attitude_8_sci, science_bank as science_8_sci, target_bank as target_8_sci, closer_bank as closer_8_sci
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
    if gender == "female": return "she","her"
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
def generate_comment(subject, year, name, gender, att, achieve, target, pronouns, attitude_target=None):
    p, p_poss = pronouns
    name = sanitize_input(name)

    # Select banks
    if subject=="English":
        if year==5: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_5_eng, attitude_5_eng, reading_5_eng, writing_5_eng, target_5_eng, target_write_5_eng, closer_5_eng
        elif year==7: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_7_eng, attitude_7_eng, reading_7_eng, writing_7_eng, target_7_eng, target_write_7_eng, closer_7_eng
        elif year==8: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_8_eng, attitude_8_eng, reading_8_eng, writing_8_eng, target_8_eng, target_write_8_eng, closer_8_eng
    elif subject=="Math":
        if year==5: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_5_math, attitude_5_math, reading_5_math, writing_5_math, target_5_math, target_write_5_math, closer_5_math
        elif year==7: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_7_math, attitude_7_math, reading_7_math, writing_7_math, target_7_math, target_write_7_math, closer_7_math
        elif year==8: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_8_math, attitude_8_math, reading_8_math, writing_8_math, target_8_math, target_write_8_math, closer_8_math
    elif subject=="Science":
        if year==5: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_5_sci, attitude_5_sci, science_5_sci, None, target_5_sci, None, closer_5_sci
        elif year==7: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_7_sci, attitude_7_sci, science_7_sci, None, target_7_sci, None, closer_7_sci
        elif year==8: opening, attitude, reading, writing, reading_target, writing_target, closer = opening_8_sci, attitude_8_sci, science_8_sci, None, target_8_sci, None, closer_8_sci

    # Compose comment
    opening_phrase = random.choice(opening) if opening else ""
    closer_phrase = random.choice(closer) if closer else ""
    attitude_text = fix_pronouns_in_text(attitude.get(att,""), p, p_poss)
    attitude_sentence = f"{opening_phrase} {name} {attitude_text}".strip()
    if attitude_sentence and not attitude_sentence.endswith('.'): attitude_sentence += '.'

    reading_text = fix_pronouns_in_text(reading.get(achieve,""), p, p_poss)
    if reading_text and reading_text[0].islower(): reading_text = f"{p} {reading_text}"
    reading_sentence = f"In reading, {reading_text}" if subject=="English" else reading_text
    if reading_sentence and not reading_sentence.endswith('.'): reading_sentence += '.'

    if writing:
        writing_text = fix_pronouns_in_text(writing.get(achieve,""), p, p_poss)
        if writing_text and writing_text[0].islower(): writing_text = f"{p} {writing_text}"
        writing_sentence = f"In writing, {writing_text}"
        if writing_sentence and not writing_sentence.endswith('.'): writing_sentence += '.'
    else: writing_sentence = ""

    reading_target_text = fix_pronouns_in_text(reading_target.get(target,""), p, p_poss)
    reading_target_sentence = f"For the next term, {p} should {lowercase_first(reading_target_text)}" if reading_target_text else ""
    if reading_target_sentence and not reading_target_sentence.endswith('.'): reading_target_sentence += '.'

    writing_target_text = fix_pronouns_in_text(writing_target.get(target,""), p, p_poss) if writing_target else ""
    writing_target_sentence = f"Additionally, {p} should {lowercase_first(writing_target_text)}" if writing_target_text else ""
    if writing_target_sentence and not writing_target_sentence.endswith('.'): writing_target_sentence += '.'

    attitude_target_sentence = ""
    if attitude_target:
        attitude_target_sentence = f" {lowercase_first(sanitize_input(attitude_target))}"
        if not attitude_target_sentence.endswith('.'): attitude_target_sentence += '.'

    comment_parts = [
        attitude_sentence + attitude_target_sentence,
        reading_sentence,
        writing_sentence,
        reading_target_sentence,
        writing_target_sentence,
        closer_phrase
    ]

    comment = " ".join([c for c in comment_parts if c])
    if not comment.endswith('.'): comment += '.'
    comment = truncate_comment(comment, TARGET_CHARS)
    if not comment.endswith('.'): comment = comment.rstrip(' ,;') + '.'
    return comment

# ========== THE REST OF THE APP UI ==========
# Your original Streamlit layout, forms, CSV handling, download section,
# privacy info, and footer remain unchanged. They will now call
# this updated generate_comment() function, and it fully supports
# English, Math, Science for Years 5, 7, 8.
