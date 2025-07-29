import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF
import requests
from streamlit_lottie import st_lottie

# ----- Load Excel data -----
def load_data():
    df = pd.read_excel('apc.xlsx')
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    df.columns = df.columns.str.strip()
    if 'branch_code' in df.columns:
        df['branch_code'] = df['branch_code'].astype(str).str.strip()
    return df

# ----- Identify caste-gender rank columns -----
def get_rank_columns(df):
    return [col for col in df.columns if any(x in col for x in ['_BOYS', '_GIRLS'])]

# ----- Generate PDF -----
def generate_pdf(df):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Manjunathareddy Journey Predictor - AP EAPCET', ln=True, align='C')
    pdf.ln(3)
    pdf.set_font('Arial', '', 8)
    note = (
        "Note: This is based on previous cutoffs. Please verify with official sources."
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

# ----- Load Lottie Animation -----
def load_lottie_url(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# ----- Main App -----
def main():
    st.set_page_config(layout="wide", page_title="AP EAMCET Predictor 2025", page_icon="🎓")

    # ----- Custom CSS Styling -----
    st.markdown("""
        <style>
        html, body, .stApp {
            background: linear-gradient(-45deg, #1a2a6c, #b21f1f, #fdbb2d, #23a6d5);
            background-size: 400% 400%;
            animation: gradientMove 20s ease infinite;
            color: white !important;
            font-family: 'Segoe UI', sans-serif;
        }
        @keyframes gradientMove {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
        }
        .stButton > button {
            background-color: #28a745;
            color: white;
            border-radius: 10px;
            font-weight: bold;
            padding: 0.6rem 1.2rem;
        }
        .stButton > button:hover {
            background-color: #1e7e34;
        }
        .block-container {
            padding-top: 2rem;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            text-align: center;
            padding: 10px;
            font-size: 13px;
            color: #fff;
            background-color: rgba(0,0,0,0.3);
        }
        </style>
    """, unsafe_allow_html=True)

    # ----- Load Animations -----
    edu_animation = load_lottie_url("https://lottie.host/cc7ec4b6-ec09-4f64-9a10-c019ba89caa9/Zvl8COzIYw.json")
    particles = load_lottie_url("https://lottie.host/0c8c6e7d-fc5d-490e-a2c6-4df6f2d3cf3b/26tpqHvXxy.json")

    if particles:
        st_lottie(particles, height=120, speed=0.3, loop=True, quality="low", key="particles")

    # ----- Top Title Section -----
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("## 🎯 AP EAMCET Rank Predictor 2025")
        st.markdown("#### 🔍 Smart College Finder based on your rank & preferences")
    with col2:
        if edu_animation:
            st_lottie(edu_animation, height=140)

    # ----- Data Load -----
    df = load_data()
    rank_columns = get_rank_columns(df)

    # ----- Sidebar-like Form for Input -----
    with st.form("filter_form"):
        st.markdown("### 📝 Enter Your Details")

        caste_gender = st.selectbox("🎓 Caste & Gender Rank Column", sorted(rank_columns))
        selected_rank = st.text_input("🏷️ Enter Your Rank", placeholder="e.g. 35000")

        branches = sorted(df['branch_code'].dropna().unique()) if 'branch_code' in df else []
        selected_branches = st.multiselect("💼 Preferred Branches", options=branches)

        districts = sorted(df['DIST'].dropna().unique()) if 'DIST' in df else []
        selected_dists = st.multiselect("📍 Preferred Districts", options=districts)

        regions = sorted(df['A_REG'].dropna().unique()) if 'A_REG' in df else []
        selected_regions = st.multiselect("🌐 Preferred Region (AU/SVU/OU)", options=regions)

        submit = st.form_submit_button("🔍 Predict Colleges")

    # ----- Main Output Panel -----
    if submit:
        if not selected_rank or not selected_rank.strip().isdigit():
            st.error("❗ Please enter a valid numeric rank.")
            return

        rank = int(selected_rank.strip())
        df[caste_gender] = df[caste_gender].replace(r'^\s*$', np.nan, regex=True)
        filtered_df = df.copy()

        if selected_branches:
            filtered_df = filtered_df[filtered_df['branch_code'].isin(selected_branches)]
        if selected_dists:
            filtered_df = filtered_df[filtered_df['DIST'].isin(selected_dists)]
        if selected_regions:
            filtered_df = filtered_df[filtered_df['A_REG'].isin(selected_regions)]

        filtered_df[caste_gender] = pd.to_numeric(filtered_df[caste_gender], errors='coerce')
        filtered_df = filtered_df.dropna(subset=[caste_gender])

        lower = max(0, rank - 20000)
        upper = rank + 30000
        result_df = filtered_df[(filtered_df[caste_gender] >= lower) & (filtered_df[caste_gender] <= upper)]

        show_cols = [
            'INSTCODE', 'NAME OF THE INSTITUTION', 'INST_REG', 'DIST', 'A_REG',
            'branch_code', 'PLACE', caste_gender, 'COLLFEE'
        ]
        result_df = result_df[[col for col in show_cols if col in result_df.columns]]
        result_df = result_df.sort_values(by=caste_gender)

        if not result_df.empty:
            st.success(f"✅ Found **{len(result_df)}** matching colleges for rank **{rank}**")
            st.dataframe(result_df, use_container_width=True)

            st.markdown("### 📥 Download Your Personalized College Report")
            st.download_button(
                label="📄 Download PDF Report",
                data=generate_pdf(result_df),
                file_name="AP_EAMCET_College_Prediction.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("⚠️ No colleges found for the given inputs.")

    # ----- Footer -----
    st.markdown(
        '<div class="footer">Designed by K.Manjunatha Reddy | 📞 6300138360 | ✉️ <a style="color: #fff;" href="mailto:manjukummathi@gmail.com">manjukummathi@gmail.com</a></div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
