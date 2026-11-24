import streamlit as st
import time

st.set_page_config(page_title="Test Streamlit", layout="wide")
st.title("🏴‍☠️ Captain Julie’s Streamlit Port Test")

counter = st.empty()
start_time = time.time()

for i in range(60):  # show for ~2 minutes
    counter.write(f"⏳ Seconds passed: {int(time.time() - start_time)}")
    time.sleep(2)