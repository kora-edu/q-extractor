import os
import openai
import json
import re
from PyPDF2 import PdfReader

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

client = openai.Client()

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file without skipping any pages.
    """
    text = ""
    try:
        reader = PdfReader(pdf_path)
        num_pages = len(reader.pages)
        for i in range(num_pages):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text += page_text
        # Replace multiple newlines and tabs with a single space
        text = re.sub(r'[\n\t]+', ' ', text)
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
    return text

def extract_items(text, item_type):
    """
    Use OpenAI's GPT-4 to extract questions or answers from text without filtering.
    """
    items = []
    prompt = (
        f"Extract all the {item_type} from the following text, including their associated numbering "
        f"(e.g., Q1a, Q1b, etc.):\n\n{text}\n\n"
        f"Provide each {item_type[:-1]} separated by '<END>'."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    'role': 'system',
                    'content': f'You are an assistant that extracts {item_type} from text.',
                },
                {'role': 'user', 'content': prompt},
            ],
            temperature=0,
            n=1,
            stop=None,
        )
        content = response.choices[0].message.content.strip()
        extracted_items = content.split('<END>')
        items.extend([item.strip() for item in extracted_items if item.strip()])
    except Exception as e:
        print(f"Error extracting {item_type}: {e}")

    return items

def validate_and_fix_data(json_file):
    """
    Validate and fix the data using OpenAI's GPT-4 to ensure that questions and answers make sense.
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
            f"Please correct any errors, clarify any ambiguities, remove LaTeX formatting, and ensure that both the question and answer are appropriate and make sense for training a language model. "
            f"If a question contains multiple parts (e.g., labeled a, b, c), separate each part into its own distinct question entry."
            f"Remove all question markers like (a) or Question one, and replace mathematical symbols like '\\sqrt' and '\\frac' with plain text equivalents (i.e. / or sqrt) in the following format:\n\n"
            f"Corrected Question:\n<Your corrected question here, with LaTeX removed>\n\n"
            f"Corrected Answer:\n<Your corrected answer here, with LaTeX removed>"
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
    base_path = r'C:\Users\OKH20\OneDrive - University of Canterbury\Projects\KORA\KORAedu\q-extractor\q-extractorPYMUPDF\PapersPDF\NCEAL3CALC'  # Update this path to your actual path
    topics = ['91579_INT']  # Only process the first set of files
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

            exam_text = extract_text_from_pdf(exam_pdf_path)
            schedule_text = extract_text_from_pdf(schedule_pdf_path)

            if not exam_text or not schedule_text:
                print(f"Skipping {exam_file} due to empty text.")
                continue

            questions = extract_items(exam_text, 'questions')
            answers = extract_items(schedule_text, 'answers')

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
