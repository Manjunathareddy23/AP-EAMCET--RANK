import streamlit as st
import pandas as pd
import numpy as np
import io
from fpdf import FPDF

# Load Excel data
def load_data(uploaded_file=None):
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
    else:
        df = pd.read_excel("apc.xlsx")

    df.columns = df.iloc[0]  # First row becomes header
    df = df[1:].reset_index(drop=True)
    df.columns = df.columns.str.strip()

    if 'branch_code' in df.columns:
        df['branch_code'] = df['branch_code'].astype(str).str.strip()
    return df

# Get caste-gender rank columns
def get_rank_columns(df):
    return [col for col in df.columns if '_BOYS' in col or '_GIRLS' in col]

# Generate PDF with clean layout
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

    # Auto-fit column widths
    column_widths = {}
    for col in df.columns:
        max_width = max(df[col].astype(str).str.len().max(), len(col))
        column_widths[col] = min(max_width * 2.5, 40)

    # Header
    pdf.set_font('Arial', 'B', 7)
    for col in df.columns:
        pdf.cell(column_widths[col], 6, str(col)[:30], border=1, align='C')
    pdf.ln()

    # Data rows
    pdf.set_font('Arial', '', 6.5)
    for _, row in df.iterrows():
        for col in df.columns:
            text = str(row[col])[:30] if pd.notnull(row[col]) else ''
            pdf.cell(column_widths[col], 6, text, border=1, align='C')
        pdf.ln()

    return io.BytesIO(pdf.output(dest='S').encode('latin1'))

# Main Streamlit app
def main():
    st.set_page_config(page_title="AP EAPCET Predictor  – Manjunathareddy", layout="wide")
    st.title('🎯 AP EAPCET Rank Predictor – K.Manjunatha Reddy')

    st.markdown("📘 This tool helps you find colleges based on your **EAPCET rank**, caste & gender, and preferences.")

    # Optional file upload
    uploaded_file = st.file_uploader("📁 Upload Excel file (Optional)", type=['xlsx'])

    df = load_data(uploaded_file)
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
        lower, upper = max(0, rank - 5000), rank + 25000
        result_df = filtered_df[(filtered_df[caste_gender] >= lower) & (filtered_df[caste_gender] <= upper)]

        show_cols = [
            'INSTCODE', 'NAME OF THE INSTITUTION', 'INST_REG', 'DIST',
            'A_REG', 'branch_code', 'PLACE', caste_gender, 'COLLFEE'
        ]
        result_df = result_df[[col for col in show_cols if col in result_df.columns]]
        result_df = result_df.sort_values(by=caste_gender)

        if not result_df.empty:
            st.success(f"✅ Found **{len(result_df)}** matching colleges in the rank range [{lower} – {upper}]")
            st.dataframe(result_df, use_container_width=True)

            st.subheader("📥 Download Your Result as PDF")
            st.download_button(
                label="📄 Download PDF",
                data=generate_pdf(result_df),
                file_name="AP_EAPCET_Predictor_Result.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("❌ No colleges found for the given filters and rank.")

if __name__ == "__main__":
    main()
