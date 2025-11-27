import streamlit as st
import pandas as pd
import os
from database import Database

st.set_page_config(page_title="Swine Breeding Monitor", layout="wide")

st.title("🐷 Swine Breeding Behavior Detection System")

# Sidebar
st.sidebar.header("Settings")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)
limit = st.sidebar.number_input("Max Logs to Show", min_value=10, max_value=1000, value=50)

# Database Connection
db = Database()

# Fetch Data
st.subheader("Detection Logs")
logs = db.get_logs(limit=limit)

if not logs:
    st.info("No detections recorded yet.")
else:
    # Convert to DataFrame
    df = pd.DataFrame(logs, columns=["ID", "Timestamp", "Image Path", "Confidence", "Is Mounting", "Details"])
    
    # Display Table
    st.dataframe(df.style.highlight_max(axis=0))

    # Image Gallery
    st.subheader("Latest Captures")
    
    cols = st.columns(3)
    for index, row in df.iterrows():
        image_path = row["Image Path"]
        timestamp = row["Timestamp"]
        confidence = row["Confidence"]
        
        col = cols[index % 3]
        with col:
            if os.path.exists(image_path):
                st.image(image_path, caption=f"{timestamp} (Conf: {confidence:.2f})", use_container_width=True)
            else:
                st.warning(f"Image not found: {image_path}")

# Auto-refresh logic (simple workaround using rerun)
if st.button("Refresh Logs"):
    st.rerun()
