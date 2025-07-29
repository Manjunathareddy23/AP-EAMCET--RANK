import streamlit as st
import pandas as pd
import numpy as np
import io
import requests
from fpdf import FPDF
from streamlit_lottie import st_lottie
import plotly.express as px
import time

# ------------------------- LOTTIE HELPER -------------------------
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ------------------------- DATA LOADER -------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("apc.xlsx")
    df.columns = df.iloc[0]  # First row becomes header
    df = df[1:].reset_index(drop=True)
    df.columns = df.columns.str.strip()
    if 'branch_code' in df.columns:
        df['branch_code'] = df['branch_code'].astype(str).str.strip()
    return df

# ------------------------- PDF GENERATION -------------------------
def generate_pdf(df):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Vamsi Journey Predictor – AP EAMCET', ln=True, align='C')
    pdf.ln(4)
    pdf.set_font('Arial', '', 8)
    note = "Note: Based on previous cutoffs. Always verify with official sources."
    pdf.multi_cell(0, 5, note)
    pdf.ln(3)

    column_widths = {col: min(max(df[col].astype(str).str.len().max(), len(col)) * 2.5, 40) for col in df.columns}

    pdf.set_font('Arial', 'B', 7)
    for col in df.columns:
        pdf.cell(column_widths[col], 6, str(col)[:30], border=1, align='C')
    pdf.ln()

    pdf.set_font('Arial', '', 6.5)
    for _, row in df.iterrows():
        for col in df.columns:
            text = str(row[col])[:30] if pd.notnull(row[col]) else ''
            pdf.cell(column_widths[col], 6, text, border=1, align='C')
        pdf.ln()

    return io.BytesIO(pdf.output(dest='S').encode('latin1'))

# ------------------------- MAIN APP -------------------------
def main():
    st.set_page_config(page_title="AP EAMCET Predictor – Vamsi Journey", layout="wide")

    # CSS Styling for background and components
    st.markdown("""
        <style>
            .stApp {
                background-image: linear-gradient(to bottom, #e0f7fa, #ffffff);
                background-size: cover;
                font-family: 'Segoe UI', sans-serif;
            }
            .stButton>button {
                border-radius: 10px;
                background-color: #1e90ff;
                color: white;
                transition: all 0.3s ease-in-out;
                font-weight: bold;
            }
            .stButton>button:hover {
                transform: scale(1.05);
                background-color: #0056b3;
            }
            .css-1aumxhk, .stTextInput>div>div>input {
                border-radius: 10px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # Load animation
    lottie_url = "https://assets6.lottiefiles.com/packages/lf20_w51pcehl.json"
    lottie_json = load_lottie_url(lottie_url)
    if lottie_json:
        st_lottie(lottie_json, speed=1, height=200, key="header_anim")

    # App Title and Description
    st.title("🎓 AP EAMCET College Predictor")
    st.markdown("""
    <div style="background-color:#f9f9f9;padding:15px;border-radius:10px;
    box-shadow: 0 0 20px rgba(0, 123, 255, 0.2);margin-bottom:20px">
    <h4 style="color:#1e90ff;">Predict your eligible colleges based on your AP EAMCET rank, caste, gender, and region.</h4>
    </div>
    """, unsafe_allow_html=True)

    try:
        df = load_data()
        st.success("✅ Loaded inbuilt Excel file: apc.xlsx")
    except Exception as e:
        st.error(f"Failed to load the Excel file: {e}")
        return

    # Input widgets
    with st.form("input_form"):
        rank = st.number_input("Enter your AP EAMCET Rank", min_value=1, step=1)
        gender = st.selectbox("Select your Gender", ["MALE", "FEMALE"])
        caste = st.selectbox("Select your Caste", ["OC", "BC_A", "BC_B", "BC_C", "BC_D", "BC_E", "SC", "ST"])
        region = st.selectbox("Select your Region", ["AU", "OU", "SVU"])
        submit = st.form_submit_button("🎯 Predict Eligible Colleges")

    if submit:
        with st.spinner("🔍 Processing your inputs..."):
            time.sleep(1.2)
            caste_gender = f"{caste}_{gender}"

            if caste_gender not in df.columns:
                st.error(f"Rank data for selection '{caste_gender}' not found in dataset.")
                return

            df[caste_gender] = pd.to_numeric(df[caste_gender], errors='coerce')
            region_df = df[df["REG"] == region]
            result_df = region_df[region_df[caste_gender] >= rank].copy()

            if not result_df.empty:
                result_df["RANK_DIFF"] = result_df[caste_gender] - rank
                result_df.sort_values(by="RANK_DIFF", inplace=True)

                show_cols = [
                    'INSTCODE', 'NAME OF THE INSTITUTION', 'INST_REG', 'DIST',
                    'A_REG', 'branch_code', 'PLACE', caste_gender, 'COLLFEE', 'RANK_DIFF'
                ]
                result_df = result_df[[col for col in show_cols if col in result_df.columns]]

                st.success(f"✅ Found **{len(result_df)}** eligible colleges for rank {rank}")

                if "RANK_DIFF" in result_df.columns:
                    result_df.drop(columns=["RANK_DIFF"], inplace=True)

                st.dataframe(result_df, use_container_width=True)

                # 📥 Excel Download
                @st.cache_data
                def convert_df_to_excel(df):
                    return df.to_excel(index=False, engine='openpyxl')

                st.download_button(
                    "⬇️ Download Eligible Colleges (Excel)",
                    data=convert_df_to_excel(result_df),
                    file_name="eligible_colleges.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # 📥 PDF Download
                st.download_button(
                    "⬇️ Download PDF Summary",
                    data=generate_pdf(result_df),
                    file_name="eligible_colleges.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("⚠️ No eligible colleges found for your inputs.")

if __name__ == "__main__":
    main()
