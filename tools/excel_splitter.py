import zipfile
from io import BytesIO

import pandas as pd
import streamlit as st

from core.ui import render_hero

def page_excel_splitter():
    render_hero("Excel Splitter", "Split a big Excel file into smaller XLSX parts and download one ZIP.", ["XLSX", "ZIP", "No Jira needed"])

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"], key="excel_uploader")
    chunk_size = st.number_input("Rows per file", value=1000, min_value=1, step=1, key="chunk_size")

    if uploaded_file and st.button("Split Excel", type="primary", key="split_button"):
        try:
            with st.spinner("Processing file..."):
                df = pd.read_excel(uploaded_file, engine="openpyxl")
                base_name = uploaded_file.name.rsplit(".", 1)[0]
                zip_filename = f"{base_name}_split.zip"
                zip_buffer = BytesIO()

                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
                    for i in range(0, len(df), chunk_size):
                        chunk = df.iloc[i : i + chunk_size]
                        part_filename = f"{base_name}_{i // chunk_size + 1}.xlsx"
                        excel_buffer = BytesIO()
                        chunk.to_excel(excel_buffer, index=False, engine="openpyxl")
                        excel_buffer.seek(0)
                        z.writestr(part_filename, excel_buffer.read())

                zip_buffer.seek(0)
                st.session_state.zip_data = zip_buffer.read()
                st.session_state.zip_name = zip_filename
                st.session_state.split_ready = True
                st.session_state.split_rows = len(df)
                st.session_state.split_parts = (len(df) + chunk_size - 1) // chunk_size
        except Exception as e:
            st.error("Failed to split Excel file")
            st.code(str(e))

    if st.session_state.split_ready:
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{st.session_state.get("split_rows", 0)}</div><div class="metric-label">Rows</div></div>', unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric-card"><div class="metric-number">{st.session_state.get("split_parts", 0)}</div><div class="metric-label">Files created</div></div>', unsafe_allow_html=True)
        st.success("Done. ZIP is ready.")
        st.download_button(
            label="Download ZIP",
            data=st.session_state.zip_data,
            file_name=st.session_state.zip_name,
            mime="application/zip",
            key="download_zip",
            use_container_width=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)
