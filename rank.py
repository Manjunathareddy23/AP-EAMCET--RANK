import streamlit as st
import pandas as pd
import numpy as np
import io
import requests
from fpdf import FPDF
from streamlit_lottie import st_lottie
import plotly.express as px

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

# ------------------------- RANK COLUMNS -------------------------
def get_rank_columns(df):
    return [col for col in df.columns if '_BOYS' in col or '_GIRLS' in col]

# ------------------------- PDF GENERATION -------------------------
def generate_pdf(df):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Vamsi Journey Predictor – AP EAPCET', ln=True, align='C')
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
    st.set_page_config(page_title="AP EAPCET Predictor – ManjunathaReddy", layout="wide")

    lottie_url = "https://assets6.lottiefiles.com/packages/lf20_w51pcehl.json"
    lottie_json = load_lottie_url(lottie_url)
    if lottie_json:
        st_lottie(lottie_json, speed=1, height=200, key="header_anim")

    st.title("🎯 AP EAPCET Rank Predictor – K.Manjunatha Reddy")
    st.markdown("""
    <div style="background-color:#f9f9f9;padding:15px;border-radius:10px;
    box-shadow: 0 0 20px rgba(0, 123, 255, 0.2);margin-bottom:20px">
    <h4 style="color:#1e90ff;">This app helps you predict possible colleges using your AP EAPCET rank based on previous data.<br>
    Apply filters and download your personalized result as PDF.</h4>
    </div>
    """, unsafe_allow_html=True)

    try:
        df = load_data()
        st.success("✅ Loaded inbuilt Excel file: `apc.xlsx`")
    except Exception as e:
        st.error(f"Failed to load the Excel file: {e}")
        return

    rank_columns = get_rank_columns(df)

    with st.form("filter_form"):
        st.subheader("🎛️ Filter Your Preferences")

        caste_gender = st.selectbox("🎓 Select Caste & Gender Rank Column:", sorted(rank_columns), index=0)
        selected_rank = st.text_input("🏅 Enter Your Rank (Required):", placeholder="e.g., 30000")

        branch_options = sorted(df['branch_code'].dropna().unique())
        selected_branches = st.multiselect("🏢 Branch(es):", branch_options)

        dist_options = sorted(df['DIST'].dropna().unique())
        selected_dists = st.multiselect("📍 District(s):", dist_options)

        region_options = sorted(df['A_REG'].dropna().unique())
        selected_regions = st.multiselect("🌍 Region(s):", region_options)

        submitted = st.form_submit_button("🔍 Apply Filters")

    if submitted:
        if not selected_rank or not selected_rank.strip().isdigit():
            st.error("⚠️ Please enter a valid numeric rank.")
            return

        rank = int(selected_rank.strip())
        df[caste_gender] = pd.to_numeric(df[caste_gender], errors='coerce')

        filtered_df = df.copy()
        if selected_branches:
            filtered_df = filtered_df[filtered_df['branch_code'].isin(selected_branches)]
        if selected_dists:
            filtered_df = filtered_df[filtered_df['DIST'].isin(selected_dists)]
        if selected_regions:
            filtered_df = filtered_df[filtered_df['A_REG'].isin(selected_regions)]

        filtered_df = filtered_df.dropna(subset=[caste_gender])

        # Smart rank range adjustment
        lower, upper = max(0, rank - 10000), rank + 40000
        result_df = filtered_df[(filtered_df[caste_gender] >= lower) & (filtered_df[caste_gender] <= upper)]

        # Sort by proximity to user's rank
        result_df["RANK_DIFF"] = abs(result_df[caste_gender] - rank)
        result_df = result_df.sort_values(by="RANK_DIFF")

        show_cols = [
            'INSTCODE', 'NAME OF THE INSTITUTION', 'INST_REG', 'DIST',
            'A_REG', 'branch_code', 'PLACE', caste_gender, 'COLLFEE'
        ]
        result_df = result_df[[col for col in show_cols if col in result_df.columns]]

        if not result_df.empty:
            st.success(f"✅ Found **{len(result_df)}** matching colleges for your rank ({rank})")
            st.dataframe(result_df.drop(columns=["RANK_DIFF"]), use_container_width=True)

            # 📊 Visualizations
            st.subheader("📊 Visual Insights")

            if 'DIST' in result_df.columns:
                dist_data = result_df['DIST'].value_counts().reset_index()
                dist_data.columns = ['District', 'College Count']
                fig = px.bar(dist_data, x='District', y='College Count', color='District',
                             title='Colleges Matching Your Rank by District',
                             template='plotly_dark', height=400)
                st.plotly_chart(fig, use_container_width=True)

            if 'branch_code' in result_df.columns:
                branch_data = result_df['branch_code'].value_counts().reset_index()
                branch_data.columns = ['Branch', 'Count']
                fig2 = px.pie(branch_data, values='Count', names='Branch',
                              title='Branch Distribution of Matching Colleges', hole=0.3)
                st.plotly_chart(fig2, use_container_width=True)

            # 📥 PDF Download
            st.subheader("📥 Download Your Result as PDF")
            st.download_button(
                label="📄 Download PDF",
                data=generate_pdf(result_df),
                file_name="AP_EAPCET_Predictor_Result.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("❌ No colleges found. Try relaxing your filters or widening your rank range.")

if __name__ == "__main__":
    main()
