import streamlit as st
import pandas as pd
import os
import tempfile
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
import google.generativeai as genai

# Configure Gemini (API key from Streamlit secrets)
genai.configure(api_key=st.secrets["AIzaSyDMa8ZqsVt8e0ThJl2DfjJAhfBLhT35hhI"])

st.set_page_config(page_title="LITIGATION TRACKER", page_icon="📂")

st.title("📂 LITIGATION TRACKER")
st.write("Upload your GST litigation notices and extract key details into Excel.")

uploaded_files = st.file_uploader("Upload your PDFs here", type=["pdf"], accept_multiple_files=True)

# Output columns
columns = [
    "Entity Name",
    "GSTIN",
    "Type of Notice / Order (System Update)",
    "Description",
    "Ref ID",
    "Date Of Issuance",
    "Due Date",
    "Case ID Notice Type (ASMT-10 or ADT - 01 / SCN or Appeal)",
    "Financial Year",
    "Total Demand Amount as per Notice",
    "Source"
]

def extract_text_from_pdf(file):
    """Extract text from PDF, using OCR if scanned."""
    try:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        if text.strip():
            return text
    except:
        pass

    # If text is empty, do OCR
    images = convert_from_path(file)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img)
    return text

def extract_details_with_gemini(text, source_name):
    """Ask Gemini to extract structured fields based on context."""
    prompt = f"""
    You are an assistant that extracts litigation notice details into structured fields.
    From the following notice text, extract the following details:
    - Entity Name
    - GSTIN
    - Type of Notice / Order (System Update)
    - Description
    - Ref ID
    - Date Of Issuance
    - Due Date
    - Case ID Notice Type (ASMT-10 or ADT - 01 / SCN or Appeal)
    - Financial Year
    - Total Demand Amount as per Notice

    Return them strictly as JSON with keys exactly matching.

    Notice text:
    {text}
    """

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    try:
        resp = model.generate_content(prompt)
        data = eval(resp.text)  # safe because Gemini outputs JSON
    except Exception:
        data = {col: "" for col in columns}
    data["Source"] = source_name
    return data

if uploaded_files:
    if st.button("Process Notices"):
        results = []
        with st.spinner("Processing... Please wait ⏳"):
            for file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(file.read())
                    tmp_path = tmp.name

                text = extract_text_from_pdf(tmp_path)
                details = extract_details_with_gemini(text, file.name)
                results.append(details)

        df = pd.DataFrame(results, columns=columns)

        st.success("✅ Extraction complete!")
        st.dataframe(df)

        # Save to Excel
        output_path = "litigation_tracker_output.xlsx"
        df.to_excel(output_path, index=False)

        with open(output_path, "rb") as f:
            st.download_button("📥 Download Excel", f, file_name=output_path, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
