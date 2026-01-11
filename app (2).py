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
        achievement_bank as maths_achievement_bank,
        target_bank as maths_target_bank,
        closer_bank as maths_closer_bank
    )
    from statements_year5_Science import (
        opening_phrases as sci_opening_phrases,
        attitude_bank as sci_attitude_bank,
        achievement_bank as sci_achievement_bank,
        target_bank as sci_target_bank,
        closer_bank as sci_closer_bank
    )

    # Years 7 & 8 English & Science already imported previously
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
    from statements_year7_science import (
        opening_phrases as opening_7_sci,
        attitude_bank as attitude_7_sci,
        science_bank as science_7_sci,
        target_bank as target_7_sci,
        closer_bank as closer_7_sci
    )
    from statements_year8_science import (
        opening_phrases as opening_8_sci,
        attitude_bank as attitude_8_sci,
        science_bank as science_8_sci,
        target_bank as target_8_sci,
        closer_bank as closer_8_sci
    )

    # Optional: Year 7 & 8 Maths can be added similarly
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
        # Years 7 & 8 handled exactly as in your previous code
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
        else:
            # Science Years 7 & 8
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

# ========== APP LAYOUT ==========
st.title("📚 Multi-Subject Report Comment Generator")
st.caption(f"~{TARGET_CHARS} characters per comment • Secure • No data retention")
