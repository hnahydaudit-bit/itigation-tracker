import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import google.generativeai as genai
import tempfile
import os

# 🔑 Configure Gemini (API key from Streamlit Cloud secrets)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 🎨 Page setup
st.set_page_config(page_title="LITIGATION TRACKER", page_icon="📂")

st.title("📂 LITIGATION TRACKER")

# ---------- Helper Functions ----------

def extract_text_from_pdf(file_path):
    """Extract text from PDF using PyMuPDF (handles scanned + text PDFs)."""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text("text")
    return text.strip()

def extract_with_ai(text, filename):
    """Send extracted text to Gemini and ask for structured fields."""
    prompt = f"""
    You are an AI that extracts GST litigation notice details.

    Extract the following fields from the text below. 
    If a field is not present, leave it blank.

    Fields:
    - Entity Name
    - GSTIN
    - Type of Notice / Order (System Update)
    - Description
    - Ref ID
    - Date Of Issuance
    - Due Date
    - Case ID
    - Notice Type (ASMT-10 or ADT - 01 / SCN or Appeal)
    - Financial Year
    - Total Demand Amount as per Notice

    Return ONLY a JSON object with these keys.

    Text:
    {text}
    """

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        resp = model.generate_content(prompt)
        data = resp.candidates[0].content.parts[0].text

        # Clean response
        import json, re
        match = re.search(r"\{.*\}", data, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
        else:
            parsed = {}

        # Ensure all columns exist
        columns = [
            "Entity Name",
            "GSTIN",
            "Type of Notice / Order (System Update)",
            "Description",
            "Ref ID",
            "Date Of Issuance",
            "Due Date",
            "Case ID",
            "Notice Type (ASMT-10 or ADT - 01 / SCN or Appeal)",
            "Financial Year",
            "Total Demand Amount as per Notice",
            "Source"
        ]
        row = {col: parsed.get(col, "") for col in columns}
        row["Source"] = filename
        return row

    except Exception as e:
        return {"Source": filename, "Error": str(e)}

# ---------- Streamlit UI ----------

uploaded_files = st.file_uploader(
    "📤 Upload your Notice PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.info("⏳ Processing... please wait.")
    results = []

    for uploaded in uploaded_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        text = extract_text_from_pdf(tmp_path)
        row = extract_with_ai(text, uploaded.name)
        results.append(row)

        os.remove(tmp_path)

    df = pd.DataFrame(results)
    st.success("✅ Extraction complete!")

    st.dataframe(df)

    # Download Excel
    out_path = "litigation_tracker_output.xlsx"
    df.to_excel(out_path, index=False)

    with open(out_path, "rb") as f:
        st.download_button(
            label="📥 Download your Excel",
            data=f,
            file_name="Litigation_Tracker_Output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

