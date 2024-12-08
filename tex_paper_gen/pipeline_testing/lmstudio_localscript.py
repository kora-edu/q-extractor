import json
from openai import OpenAI
import os
import re

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model = "lmstudio-community/qwen2.5-14b-instruct"

def query_model(input_text):
    """Send a query to the local AI model and return the response."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": input_text}]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying the model: {e}")
        return None

def extract_json_from_response(response):
    """Extract JSON content from a model response."""
    try:
        # Use regex to find the JSON part in the response
        match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
        if match:
            json_content = match.group(1).strip()
            return json.loads(json_content)
        else:
            print("No JSON content found in the response.")
            return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse the JSON content: {e}")
        error_position = e.pos  # Get the position of the error
        print(f"Error at line {e.lineno}, column {e.colno}, character {error_position}")
        if response:
            print(f"Problematic content near: {response[max(0, error_position-20):error_position+20]}")
        return None

def generate_questions():
    """Generate NCEA questions using the model."""
    prompt = (
        "Could you generate 'NCEA' questions (the school system based in New Zealand) "
        "surrounding their covered topics around calculus and provide these questions as a JSON "
        "similar to what I've attached, alongside a respective answer for each? "
        "Also update the tags to NCEA-Integration, NCEA-Differentiation, NCEA-Complex, NCEA-Other, "
        "based on what sort of question you generate for it. Make sure to use the same LaTeX formatting."
    )

    response = query_model(prompt)
    if not response:
        return None

    return extract_json_from_response(response)

def save_to_file(data, output_path):
    """Save the generated questions to a file."""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Questions saved to {output_path}")
    except Exception as e:
        print(f"Error saving to file: {e}")

if __name__ == "__main__":
    input_file = "JBDATA5.json"
    output_file = "output.json"

    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
    else:
        questions = generate_questions()
        if questions:
            save_to_file(questions, output_file)
        else:
            print("No questions were generated.")
