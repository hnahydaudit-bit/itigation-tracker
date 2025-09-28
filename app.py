import streamlit as st
import pandas as pd
import google.generativeai as genai
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import tempfile

# -------------------------------
# 🔑 Configure Gemini (put your key in Streamlit Secrets)
# -------------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# -------------------------------
# 📄 PDF Text Extraction
# -------------------------------
def extract_text_from_pdf(file_path):
    """Extract text from text PDFs or OCR from scanned PDFs using PyMuPDF + Tesseract."""
    text = ""
    pdf = fitz.open(file_path)

    for page_num in range(len(pdf)):
        page = pdf[page_num]

        # Try normal text extraction
        page_text = page.get_text("text")
        if page_text.strip():
            text += page_text + "\n"
        else:
            # Fallback to OCR if no text
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img)
            text += ocr_text + "\n"

    pdf.close()
    return text

# -------------------------------
# 🧠 AI Extraction
# -------------------------------
def extract_notice_details(text, filename):
    """Send extracted text to Gemini and structure it into required fields."""
    prompt = f"""
    You are an AI assistant for GST litigation document analysis.
    Extract the following details from the given document text.
    If something is missing, leave it blank. Be accurate and concise.

    Required columns:
    - Entity Name
    - GSTIN
    - Type of Notice / Order (System Update)
    - Description
    - Ref ID
    - Date Of Issuance
    - Due Date
    - Case ID
    - Notice Type (ASMT-10 or ADT-01 / SCN or Appeal)
    - Financial Year
    - Total Demand Amount as per Notice
    - Source (file name)

    Document text:
    {text}
    """

    model = genai.GenerativeModel("models/gemini-2.5-flash")
    response = model.generate_content(prompt)

    try:
        output = response.text.strip()

        # Parse Gemini output into dict (naive way)
        data = {
            "Entity Name": "",
            "GSTIN": "",
            "Type of Notice / Order (System Update)": "",
            "Description": "",
            "Ref ID": "",
            "Date Of Issuance": "",
            "Due Date": "",
            "Case ID": "",
            "Notice Type (ASMT-10 or ADT

