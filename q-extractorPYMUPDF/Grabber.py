import os
import openai
import json
import re
import base64
from io import BytesIO

import pathlib
from pdf2image import convert_from_path
#from PyPDF2 import PdfReader
# from marker.convert import convert_single_pdf
# from marker.models import load_all_models
#import pymupdf4llm

openai.api_key = os.getenv("OPENAI_API_KEY")


client = openai.Client()
# models = load_all_models()

#dont use this func anymore
def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file without skipping any pages.
    """
    # md_text = pymupdf4llm.to_markdown(pdf_path)
    # pathlib.Path("./output.md"+pdf_path+".pdf").write_bytes(md_text.encode())
    # return md_text
  
    # full_md_txt, images, out_meta = convert_single_pdf(pdf_path, models)
    # return full_md_txt
   

    #text = ""
    # try: 
    #     reader = PdfReader(pdf_path)
    #     num_pages = len(reader.pages)
    #     for i in range(num_pages):
    #         page_text = reader.pages[i].extract_text()
    #         if page_text:
    #             text += page_text
    #     # Replace multiple newlines and tabs with a single space
    #     text = re.sub(r'[\n\t]+', ' ', text)
    # except Exception as e:
    #     print(f"Error reading {pdf_path}: {e}")
    # return text

def encode_image_to_base64(image):
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return base64.b64encode(img_byte_arr.read()).decode('utf-8')

def pdf_to_base64_images(pdf_path, dpi=300):
    pages = convert_from_path(pdf_path, dpi=dpi)
    base64_images = [encode_image_to_base64(page) for page in pages]
    return base64_images

def extract_items(pdf_path, item_type):
    """
    Extract questions or answers from pdf pages using base64 encoded images for gpt4 vision api.
    """
    items = []
    base64_images = pdf_to_base64_images(pdf_path, dpi=300)

    if (item_type.__eq__("questions")): base64_images = base64_images[1:]    #prune 1st page of questions

    for base64_image in base64_images:
        prompt = (
            f"Extract all the {item_type} from the following page using OCR instead of plainly reading"
            f"including their associated numbering and ensuring accurate representation of LaTeX equations "
            f"with a high DPI OCR process (e.g., Q1a, Q1b, Q1c (i), etc.) If a question has multiple parts e.g Q1d (i), (ii) etc, the first answer for 1d is always the (i)"
            f"Provide each {item_type[:-1]} separated by '<END>'."
        )
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are an assistant that extracts {item_type} from OCR data within exam and marking criteria content"
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt,
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                },
                            },
                        ],
                    }
                ],
                temperature=0,
                n=1
            )
            
            # Process the response
            content = response.choices[0].message.content.strip()
            extracted_items = content.split('<END>')
            items.extend([item.strip() for item in extracted_items if item.strip()])
        
        except Exception as e:
            print(f"Error extracting {item_type} from page: {e}")

    return items

def validate_and_fix_data(json_file):
    """
    Validate and fix the data to ensure that questions and answers make sense.
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    fixed_data = []
    for idx, item in enumerate(data):
        query = item['query']
        answer = item['answer']
        prompt = (
            f"The following question and answer may contain errors or unclear explanations.\n\n"
            f"Question:\n{query}\n\n"
            f"Answer:\n{answer}\n\n"
            f"Please correct any errors, clarify any ambiguities, keep and clean up LaTeX formatting, and ensure that both the question and answer are appropriate and make sense for training a language model. "
            f"If a question contains multiple parts (e.g., labeled a, b, c or i, ii, iii etc), separate each part into its own query and answer under the original question in a 'parts' json section e.g 'parts:' i) 'query: ', 'answer:' ii) .. and so on ' , filling any context gaps / blanks with appropriate information/context / solutions"
            f"Remove all question markers like (a) or Question one"
            f"if an answer is simply an equation, leave that as the answer on its own; do not add to it"
            f"Corrected Question:\n<Your corrected question here, with LaTeX >\n\n"
            f"Corrected Answer:\n<Your corrected answer here, with LaTeX>"
        )

        try:
            response = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an assistant that corrects and clarifies question and answer pairs for training a language model.',
                    },
                    {'role': 'user', 'content': prompt}
                ],
                temperature=0,
                n=1,
                stop=None,
            )
            content = response.choices[0].message.content.strip()
            # Parse the corrected question and answer
            corrected_question_match = re.search(r'Corrected Question:\s*(.*?)(?=Corrected Answer:)', content, re.DOTALL)
            corrected_answer_match = re.search(r'Corrected Answer:\s*(.*)', content, re.DOTALL)

            if corrected_question_match and corrected_answer_match:
                corrected_question = corrected_question_match.group(1).strip()
                corrected_answer = corrected_answer_match.group(1).strip()
                fixed_data.append({
                    "query": corrected_question,
                    "type": "NCEA",
                    "answer": corrected_answer
                })
            else:
                print(f"Warning: Could not parse corrected question and answer for item {idx}. Using original.")
                fixed_data.append(item)
        except Exception as e:
            print(f"Error fixing item {idx}: {e}")
            fixed_data.append(item)

    # Save the fixed data to a new JSON file
    with open('exam_data_fixed.json', 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)

    print(f"Validation and fixing complete. Fixed data saved to 'exam_data_fixed.json'.")

def main():
    base_path = r'.\PapersPDF\NCEAL3CALC' 
    topics = ['91579_INT']
    data = []

    for topic in topics:
        exams_path = os.path.join(base_path, topic, 'exams')
        schedules_path = os.path.join(base_path, topic, 'schedules')

        exam_files = sorted([f for f in os.listdir(exams_path) if f.endswith('.pdf')])
        schedule_files = sorted([f for f in os.listdir(schedules_path) if f.endswith('.pdf')])

        for exam_file, schedule_file in zip(exam_files, schedule_files):
            exam_pdf_path = os.path.join(exams_path, exam_file)
            schedule_pdf_path = os.path.join(schedules_path, schedule_file)
            
            print(f"Processing {exam_file} and {schedule_file}")

            # exam_text = extract_text_from_pdf(exam_pdf_path)
            # schedule_text = extract_text_from_pdf(schedule_pdf_path)

            # if not exam_text or not schedule_text:
            #     print(f"Skipping {exam_file} due to empty text.")
            #     continue

            questions = extract_items(exam_pdf_path, 'questions')
            answers = extract_items(schedule_pdf_path, 'answers')

            if len(questions) != len(answers):
                print(f"Warning: Number of questions and answers do not match for {exam_file}.")
                min_length = min(len(questions), len(answers))
                questions = questions[:min_length]
                answers = answers[:min_length]

            for idx, (q, a) in enumerate(zip(questions, answers), start=1):
                # Extract the question number if present
                q_number_match = re.match(r'(Q\d+[a-zA-Z]?[:.)]?)', q)
                a_number_match = re.match(r'(A\d+[a-zA-Z]?[:.)]?)', a)

                q_number = q_number_match.group(1) if q_number_match else f'Q{idx}'
                a_number = a_number_match.group(1) if a_number_match else f'A{idx}'

                print(f"Reading question {q_number}: {q}")
                print(f"Reading answer {a_number}: {a}")

                data.append({
                    "query": q,
                    "type": "NCEA",
                    "answer": a
                })

    # Save to JSON
    with open('exam_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Data extraction complete. Output saved to exam_data.json.")

    # Validate and fix the extracted data
    validate_and_fix_data('exam_data.json')

if __name__ == "__main__":
    main()
