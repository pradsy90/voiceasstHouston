import streamlit as st
import time
import sys
import os

# ⚓ Step 1: Get the transcript file path from command line args
TRANSCRIPT_PATH = None
for arg in sys.argv:
    if arg.startswith("--transcriptfile="):
        TRANSCRIPT_PATH = arg.split("=", 1)[1]

# 🕵️ Step 2: Retry logic if transcript not found yet
max_retries = 10
retry_interval = 1
retry_count = 0

while (not TRANSCRIPT_PATH or not os.path.isfile(TRANSCRIPT_PATH)) and retry_count < max_retries:
    st.warning(f"⏳ Waiting for transcript file... Attempt {retry_count + 1}")
    time.sleep(retry_interval)
    retry_count += 1

if not TRANSCRIPT_PATH or not os.path.isfile(TRANSCRIPT_PATH):
    st.error("❌ Transcript file not found even after retries.")
    st.stop()

# 🖼️ Step 3: Streamlit App Page Config
st.set_page_config(page_title="Hey Julie - Live Transcript", layout="wide")
st.title("🧠 Hey Julie - Live Chat & Timer")

# 🕒 Step 4: Timer Init
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

# 📐 Layout: Two columns
col1, col2 = st.columns([1, 3])

# Add PID (from os)
pid = os.getpid()

# 🔁 Step 5: Live Loop
while True:
    elapsed = int(time.time() - st.session_state.start_time)
    with col1:
        st.markdown("⏳ **Elapsed Time**")
        st.metric("Seconds", value=elapsed)

    try:
        with open(TRANSCRIPT_PATH, 'r', encoding='utf-8') as f:
            data = f.read()
    except UnicodeDecodeError:
        try:
            with open(TRANSCRIPT_PATH, 'r', encoding='latin-1') as f:
                data = f.read()
        except Exception as e:
            data = f"☠️ Could not decode transcript (even Latin-1): {e}"
    except Exception as e:
        data = f"⚠️ Error reading transcript: {e}"

    if not data.strip():
        data = "📭 No data yet..."

    with col2:
        st.markdown("💬 **Live Chat Transcript**")
        st.text_area("Transcript Log", value=data, height=600, key="transcript_display")

    time.sleep(2)
    st.rerun()
