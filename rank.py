import streamlit as st
import pandas as pd
import time
from PIL import Image
import base64

# Set Streamlit page configuration
st.set_page_config(page_title="AP EAMCET Rank vs College Predictor", layout="wide")

# Custom CSS for gradient background and animations
st.markdown("""
    <style>
    body {
        background: linear-gradient(to right, #2193b0, #6dd5ed);
        color: white;
    }
    .stButton>button {
        background-color: #00c6ff;
        color: white;
        border: none;
        padding: 0.6em 1.2em;
        font-size: 16px;
        border-radius: 8px;
        transition: background-color 0.3s;
    }
    .stButton>button:hover {
        background-color: #005bea;
    }
    </style>
""", unsafe_allow_html=True)

# Lottie animation
st.markdown("""
    <div style="display: flex; justify-content: center;">
        <lottie-player src="https://assets10.lottiefiles.com/packages/lf20_b88nh30c.json"  background="transparent"  speed="1"  style="width: 300px; height: 300px;"  loop  autoplay></lottie-player>
    </div>
""", unsafe_allow_html=True)

# Title and description
st.title("🎯 AP EAMCET Rank vs College Predictor")
st.markdown("""
    🔍 Find out which colleges you can get based on your **rank**, **caste**, **gender**, and **branch** preference using **2023 cutoff data**.
""")

# Load Excel data
@st.cache_data
def load_data():
    df = pd.read_excel("apc.xlsx", dtype=str)

    # Clean column names
    df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_").str.replace("-", "_")

    # Ensure data starts from the right row
    if df.iloc[0].isnull().sum() > 3:
        df.columns = df.iloc[1]
        df = df[2:].reset_index(drop=True)
        df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_").str.replace("-", "_")

    # Standardize branch_code
    if 'BRANCH_CODE' in df.columns:
        df['BRANCH_CODE'] = df['BRANCH_CODE'].astype(str).str.strip()

    return df

df = load_data()

# Get caste-gender rank columns dynamically
def get_rank_columns(df):
    return [col for col in df.columns if any(x in col for x in ['_BOYS', '_GIRLS', '_MALE', '_FEMALE'])]

rank_columns = get_rank_columns(df)

# Sidebar user inputs
st.sidebar.header("Enter Your Details")
rank = st.sidebar.number_input("Your AP EAMCET Rank", min_value=1, step=1)
caste_gender_column = st.sidebar.selectbox("Select Caste & Gender", options=sorted(rank_columns))
branch = st.sidebar.selectbox("Preferred Branch", sorted(df['BRANCH'].unique()))

# Filter logic on button click
if st.sidebar.button("🎓 Predict Colleges"):
    with st.spinner("Analyzing data and predicting colleges..."):
        time.sleep(2)
        df_filtered = df[df['BRANCH'] == branch]

        if caste_gender_column not in df_filtered.columns:
            st.error(f"Rank data for selection '{caste_gender_column}' not found in dataset.")
            st.write("Available columns:", df_filtered.columns.tolist())
        else:
            df_filtered[caste_gender_column] = pd.to_numeric(df_filtered[caste_gender_column], errors='coerce')
            df_filtered = df_filtered[df_filtered[caste_gender_column] >= rank]

            if df_filtered.empty:
                st.warning("No colleges found matching your input. Try a different branch or rank.")
            else:
                st.success(f"✅ Found {len(df_filtered)} college(s) matching your criteria")
                st.dataframe(df_filtered[["INSTITUTE", "PLACE", "DIST", "BRANCH", caste_gender_column]].sort_values(by=caste_gender_column))

                # Option to download results
                def get_table_download_link(df):
                    towrite = df.to_csv(index=False)
                    b64 = base64.b64encode(towrite.encode()).decode()
                    return f'<a href="data:file/csv;base64,{b64}" download="predicted_colleges.csv">📥 Download Results as CSV</a>'

                st.markdown(get_table_download_link(df_filtered), unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Designed with ❤️ by K.Manjunatha Reddy")
st.markdown("📧 Email: manjukaif@gmail.com | 📱 Contact: +91 6300138360")
