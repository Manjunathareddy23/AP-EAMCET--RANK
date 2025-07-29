import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF
import requests
from streamlit_lottie import st_lottie

# Load Excel data
def load_data():
    df = pd.read_excel('apc.xlsx')
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
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
        "Note: This is based on previous cutoffs. It may vary slightly. "
        "Please cross-check with official sources before taking any decision."
    )
    pdf.multi_cell(0, 5, note)
    pdf.ln(4)

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

    pdf.set_font('Arial', 'B', 8)
    for col in columns:
        pdf.cell(column_widths[col], 6, str(col)[:30], border=1, align='C')
    pdf.ln()

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

# Load Lottie animation from URL
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Main App
def main():
    st.set_page_config(layout="wide", page_title="AP EAPCET Predictor", page_icon="🎓")

    # Background and custom style
    st.markdown("""
        <style>
        html, body, .stApp {
            background: linear-gradient(-45deg, #1a2a6c, #b21f1f, #fdbb2d, #23a6d5);
            background-size: 400% 400%;
            animation: gradientMove 20s ease infinite;
            color: white !important;
        }
        @keyframes gradientMove {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        h1, h2, h3, h4, .css-10trblm, .css-1v0mbdj {
            color: white !important;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.6);
        }
        .stButton > button {
            background-color: #ff9800;
            color: white;
            border-radius: 12px;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .stButton > button:hover {
            background-color: #e65100;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Load Lottie animations
    laptop_anim = load_lottie_url("https://lottie.host/cda31063-89ea-47ef-8797-7d98d5c81f6d/b1EYvVdWSN.json")  # Laptop animation
    website_anim = load_lottie_url("https://lottie.host/6d0bb62b-0dc1-42f9-b7fa-9c41a38e0d03/QD6RwsYxfT.json")  # Website creation

    # Top bar layout: Animation | Title | Animation
    col1, col2, col3 = st.columns([1.2, 2.5, 1.2])
    with col1:
        if laptop_anim:
            st_lottie(laptop_anim, height=160, speed=1)
    with col2:
        st.title("🚀 AP EAPCET Rank Predictor")
        st.markdown("### 🎓 Crafted with ❤️ by **Manjunathareddy**")
        st.markdown("*Get a smart estimate of potential colleges based on your rank and preferences.*")
    with col3:
        if website_anim:
            st_lottie(website_anim, height=160, speed=1)

    df = load_data()
    rank_columns = get_rank_columns(df)

    with st.form("filter_form"):
        st.subheader("🎯 Filter Your Preferences")

        caste_gender = st.selectbox("🧑‍🎓 Select Caste & Gender:", sorted(rank_columns), placeholder="Choose Category")
        rank_col = caste_gender
        df[rank_col] = df[rank_col].replace(r'^\s*$', np.nan, regex=True)
        selected_rank = st.text_input("📌 Enter Your Rank", placeholder="e.g., 30000")

        branches = sorted(df['branch_code'].dropna().unique()) if 'branch_code' in df else []
        selected_branches = st.multiselect("🛠 Select Branches:", options=branches)

        districts = sorted(df['DIST'].dropna().unique()) if 'DIST' in df else []
        selected_dists = st.multiselect("📍 Select Districts:", options=districts)

        regions = sorted(df['A_REG'].dropna().unique()) if 'A_REG' in df else []
        selected_regions = st.multiselect("🌍 Select Regions (A_REG):", options=regions)

        submit = st.form_submit_button("🔍 Apply Filters")

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
            st.balloons()
            st.success(f"🎉 Found {len(result_df)} colleges for rank {rank} in range [{lower}, {upper}]")
            st.dataframe(result_df, use_container_width=True)

            st.subheader("📄 Download Your College List")
            st.download_button(
                label="📥 Download PDF",
                data=generate_pdf(result_df),
                file_name="Manjunathareddy_EAPCET_Predict_List.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("❌ No matching colleges found for your selected filters.")

if __name__ == "__main__":
    main()
