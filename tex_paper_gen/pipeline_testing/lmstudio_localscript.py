import json
from openai import OpenAI
import os
import re
import datetime 

# Point to the local server
client = OpenAI(base_url="https://24c3-2404-440c-2779-7100-3029-158c-af75-e2b1.ngrok-free.app/v1", api_key="lm-studio")
model = "lmstudio-community/qwen2.5-14b-instruct"
file_out =""

exam_schema = {  #strucutred output for valid json object
    "type": "json_schema",
    "json_schema": {
        "name": "exam_questions",
        "schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "type": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["question", "answer", "tags"]
            },
            "minItems": 1
        }
    }
}


def query_model(input_text):
    """Send a query to the local AI model and return the response."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": input_text}],
            response_format=exam_schema
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error querying the model: {e}")
        return None


# def extract_json_from_response(response):
#     """Extract json content from model response"""
#     try:
#         match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
#         if match:
#             json_content = match.group(1).strip()
#             return json.loads(response)
#         else:
#             print("No JSON content found in the response.")
#             save_failed_response(response, "failed_output")
#             return None
#     except json.JSONDecodeError as e:
#         save_failed_response(response, "failed_output")
#         print(f"Failed to parse the JSON content: {e}")
#         error_position = e.pos 
#         print(f"Error at line {e.lineno}, column {e.colno}, character {error_position}")
#         if response:
#             print(f"Problematic content near: {response[max(0, error_position-20):error_position+20]}")
#         return None

def generate_questions():
    """Generate NCEA questions using the model with the input file."""
    prompt = (
    "Generate 10 'NCEA' math questions (school system in New Zealand) "
    "based on topics including calculus and complex numbers."
    "For each question, provide the correct answer and tag it with NCEA-Integration, NCEA-Differentiation, or NCEA-Complex based on its content."
    "Your response must be LuaLaTeX compatible. Use \\text{} for text segments (e.g., \\text{This is a text segment})."
    "For inline equations, use $...$ delimiters and for display equations, use \\[ ... \\]."
    "Example of inline equation: The function is given by $f(x) = 2x + \\text{constant}$."
     "- Correct Display equation example: \\[ I = \\int_0^1 x^2 dx \\]\n"
)

    response = query_model(prompt)
    if not response:
        return None

   # return extract_json_from_response(response)
    return response

def save_to_file(data):
    global file_out
    try:
        file_out = f"replica_entries/{datetime.datetime.now().date()}_{datetime.datetime.now().time().strftime('%H.%M.%S')}.json"
        
        with open(file_out, "w", encoding="utf-8") as f:
            f.write(data)
        print(f"Questions saved to {file_out}")
    except Exception as e:
        print(f"Error saving to file: {e}")


# def save_failed_response(content):
#     """Save the raw content to a uniquely named text file if processing fails."""
#     try:
        #output_path = f"replica_entires/{datetime.datetime.now().date()}_{datetime.datetime.now().time().strftime('%H.%M.%S')}.json"
#         with open(output_path, "w", encoding="utf-8") as f:
#             f.write(content)
#         print(f"Failed content saved to {output_path}")
#     except Exception as e:
#         print(f"Error saving failed content to file: {e}")


def fixup_result():
    global file_out
    if not os.path.exists(file_out):
        print(f"Output file '{file_out}' not found")
        return

    try:
        with open(file_out, "r", encoding="utf-8") as f:
            content = f.read()

        prompt = (
            "The following JSON contains math questions and answers with LaTeX syntax. "
            "Please validate all LaTeX syntax (do NOT change the type row), correct any errors, ensuring it is JSON-compatible "
            "(e.g., escape backslashes properly). Make absolutely sure to add wrapping to any and every math / equations / symbols with $ $. Do not alter the structure of the JSON.\n\n"
            f"{content}"
        )


        fixed_response = query_model(prompt)
        if not fixed_response:
            print("Failed to fix the result.")
            return

        # Save the fixed response back to the file
        with open(file_out, "w", encoding="utf-8") as f:
            f.write(fixed_response)
        print("Latex errors fixed and updated in the output file.")

    except Exception as e:
        print(f"Error in fixup_result: {e}")



if __name__ == "__main__":
    input_file = "JBDATA5.json"

    if not os.path.exists(input_file):
        print(f"Input file '{input_file}' not found.")
    else:
        questions = generate_questions()
        if questions:
            save_to_file(questions)
            fixup_result()
        else:
            print("No questions were generated")
