import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF
import requests
import json

# Load Excel file
def load_data():
    df = pd.read_excel('apc.xlsx')
    df.columns = df.iloc[0]
    df = df[1:]
    df = df.reset_index(drop=True)
    df.columns = df.columns.str.strip()
    if 'branch_code' in df.columns:
        df['branch_code'] = df['branch_code'].astype(str).str.strip()
    return df

# Identify caste-gender rank columns
def get_rank_columns(df):
    return [col for col in df.columns if any(x in col for x in ['_BOYS', '_GIRLS'])]

# Generate PDF
def generate_pdf(df):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Manjunathareddy Journey Predictor - AP EAPCET', ln=True, align='C')
    pdf.ln(3)
    pdf.set_font('Arial', '', 8)
    note = (
        "Note: This is based on previous cutoffs. It may vary slightly in some cases. "
        "Before proceeding, please cross-check the information with official sources."
    )
    pdf.multi_cell(0, 5, note)
    pdf.ln(4)

    # Set column widths
    column_widths = {
        'INSTCODE': 20, 'NAME OF THE INSTITUTION': 60, 'INST_REG': 20,
        'DIST': 25, 'A_REG': 20, 'branch_code': 20, 'PLACE': 25, 'COLLFEE': 20,
    }

    rank_col = [col for col in df.columns if col.endswith('_BOYS') or col.endswith('_GIRLS')]
    if rank_col:
        column_widths[rank_col[0]] = 25

    columns = df.columns.tolist()
    for col in columns:
        if col not in column_widths:
            column_widths[col] = 25

    # Header
    pdf.set_font('Arial', 'B', 8)
    for col in columns:
        pdf.cell(column_widths[col], 6, str(col)[:30], border=1, align='C')
    pdf.ln()

    # Rows
    pdf.set_font('Arial', '', 7)
    for _, row in df.iterrows():
        for col in columns:
            text = str(row[col]) if pd.notnull(row[col]) else ''
            if len(text) > 50:
                text = text[:47] + '...'
            pdf.cell(column_widths[col], 6, text, border=1, align='C')
        pdf.ln()

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return io.BytesIO(pdf_bytes)

# Load Lottie Animation
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Streamlit App
def main():
    st.set_page_config(layout="wide", page_title="AP EAPCET Predictor", page_icon="🎓")

    # Custom CSS
    st.markdown("""
        <style>
        body {
            background-color: #f4faff;
        }
        .css-18e3th9 {
            background-color: #e6f7ff;
        }
        .css-1d391kg {
            padding: 2rem;
        }
        h1 {
            color: #1e88e5;
        }
        .stButton>button {
            background-color: #1e88e5;
            color: white;
            border-radius: 10px;
        }
        .stButton>button:hover {
            background-color: #1565c0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Load Animation
    from streamlit_lottie import st_lottie
    lottie_url = "https://lottie.host/0f361eb4-9355-4f13-8d4c-7552825a8434/Wh6q8WWZWR.json"  # education animation
    lottie_json = load_lottie_url(lottie_url)

    # Layout with animation
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title('AP EAPCET Rank Predictor – By Manjunathareddy 🚀')
        st.markdown("Find potential colleges based on your rank and preferences using previous year cutoffs.")
    with col2:
        if lottie_json:
            st_lottie(lottie_json, height=180, speed=1, key="edu")

    df = load_data()
    rank_columns = get_rank_columns(df)

    with st.form(key='filter_form'):
        st.subheader("🎯 Filter Your Preferences")
        caste_gender = st.selectbox('Select Caste & Gender:', sorted(rank_columns), placeholder="Select Caste")
        rank_col = caste_gender
        df[rank_col] = df[rank_col].replace(r'^\s*$', np.nan, regex=True)
        selected_rank = st.text_input('Enter Your Rank (Required)', placeholder="e.g., 30000")

        branch_options = sorted(df['branch_code'].dropna().unique()) if 'branch_code' in df else []
        selected_branches = st.multiselect("Select Branch(es):", options=branch_options)

        dist_options = sorted(df['DIST'].dropna().unique()) if 'DIST' in df else []
        selected_dists = st.multiselect("Select District(s):", options=dist_options)

        region_options = sorted(df['A_REG'].dropna().unique()) if 'A_REG' in df else []
        selected_regions = st.multiselect("Select Region(s) (A_REG):", options=region_options)

        submit = st.form_submit_button("Apply Filters")

    if submit:
        if not selected_rank or not selected_rank.strip().isdigit():
            st.error("⚠️ Please enter a valid rank.")
            return

        rank = int(selected_rank.strip())
        filtered_df = df.copy()

        if selected_branches:
            filtered_df = filtered_df[filtered_df['branch_code'].isin(selected_branches)]
        if selected_dists:
            filtered_df = filtered_df[filtered_df['DIST'].isin(selected_dists)]
        if selected_regions:
            filtered_df = filtered_df[filtered_df['A_REG'].isin(selected_regions)]

        filtered_df[rank_col] = pd.to_numeric(filtered_df[rank_col], errors='coerce')
        filtered_df = filtered_df.dropna(subset=[rank_col])

        lower = max(0, rank - 20000)
        upper = rank + 30000
        result_df = filtered_df[(filtered_df[rank_col] >= lower) & (filtered_df[rank_col] <= upper)]

        show_cols = [
            'INSTCODE', 'NAME OF THE INSTITUTION', 'INST_REG', 'DIST', 'A_REG',
            'branch_code', 'PLACE', rank_col, 'COLLFEE'
        ]
        result_df = result_df[[col for col in show_cols if col in result_df.columns]]
        result_df = result_df.sort_values(by=rank_col)

        if not result_df.empty:
            st.success(f"✅ Found {len(result_df)} colleges for rank {rank} in range [{lower}, {upper}]")
            st.dataframe(result_df, use_container_width=True)

            st.subheader("📄 Download Results as PDF")
            st.download_button(
                label="📥 Download PDF",
                data=generate_pdf(result_df),
                file_name="Manjunathareddy_EAPCET_Predict_List.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("❌ No matching colleges found for your filters.")

if __name__ == '__main__':
    main()
