import os
import json
import openai
import re

# Set up the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize the client (OpenAI's Python library uses 'openai' directly as the client)
client = openai

def validate_entry(query, answer):
    """
    Uses GPT-4 to validate if the question and answer are appropriate for the dataset.
    Returns a dictionary with corrected 'query' and 'answer' if the entry is valid.
    """
    prompt = f"""
You are an AI assistant helping to curate a dataset for fine-tuning a language model.
Please analyze the following question and answer pair:

Question: "{query}"
Answer: "{answer}"

Determine if this pair is appropriate for inclusion in a fine-tuning dataset aimed at teaching mathematical problem-solving.
Exclude pairs that are irrelevant, nonsensical, or contain placeholder text like "The page you provided is blank".

If valid, return the entry in the format:
Corrected Question: <Your corrected question here>
Corrected Answer: <Your corrected answer here>
If invalid, respond with "Invalid".
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        # Check if the response is "Invalid"
        if content == "Invalid":
            return None

        # Parse the corrected question and answer
        corrected_question_match = re.search(r'Corrected Question:\s*(.*?)(?=Corrected Answer:)', content, re.DOTALL)
        corrected_answer_match = re.search(r'Corrected Answer:\s*(.*)', content, re.DOTALL)

        if corrected_question_match and corrected_answer_match:
            corrected_question = corrected_question_match.group(1).strip()
            corrected_answer = corrected_answer_match.group(1).strip()
            return {"query": corrected_question, "type": "NCEA", "answer": corrected_answer}
        else:
            print("Warning: Could not parse corrected question and answer. Using original.")
            return {"query": query, "type": "NCEA", "answer": answer}

    except Exception as e:
        print(f"An error occurred during validation: {e}")
        return None

def process_files(file_list, directory):
    """
    Processes the list of JSON files, validates entries, and combines them into one list.
    Only processes the first 10 entries of each file for testing purposes.
    """
    combined_data = []
    for file_name in file_list:
        file_path = os.path.join(directory, file_name)
        print(f"Processing {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            query = item.get('query', '')
            answer = item.get('answer', '')
            validated_entry = validate_entry(query, answer)
            if validated_entry:
                combined_data.append(validated_entry)
            else:
                print(f"Excluding invalid entry: {query[:60]}...")

    return combined_data

def main():
    directory = r"C:\Users\OKH20\OneDrive - University of Canterbury\Projects\KORA\KORAedu\q-extractor\seperateData"
    file_list = ["CMPLX_filtered.json", "DIFF_filtered.json", "INT_filtered.json"]
    output_file = "combined_cleaned_data.json"

    combined_data = process_files(file_list, directory)

    # Save the combined data to a new JSON file
    output_path = os.path.join(directory, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)

    print(f"Combined data saved to {output_path}")

if __name__ == "__main__":
    main()
