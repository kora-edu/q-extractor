from marker.convert import convert_single_pdf
from marker.models import load_all_models
import re
import json

# Paths for question and answer PDFs
question_pdf_path = './pdfs/questions.pdf'
answer_pdf_path = './pdfs/answers.pdf'

# Regular expression to match question numbers like "1a", "1b", etc.
question_pattern = re.compile(r"(\d+[a-z]*)")

# Load Marker models
models = load_all_models()

# Function to process the PDF with Marker and extract structured text
def extract_text_from_pdf_with_marker(pdf_path):
    full_text, images, out_meta = convert_single_pdf(pdf_path, models)
    return full_text

# Extract structured text from questions and answers PDFs using Marker
question_text_data = extract_text_from_pdf_with_marker(question_pdf_path)
answer_text_data = extract_text_from_pdf_with_marker(answer_pdf_path)
