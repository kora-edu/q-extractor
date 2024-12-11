import json
import re

def convert_latex_notation(text):
    # Convert inline math \( \)
    text = re.sub(r'\\\\?\(([^()]+)\\\\?\)', r'$$\1$$', text)
    
    # Convert block math \[ \]
    text = re.sub(r'\\\\?\[([^[\]]+)\\\\?\]', r'$$\1$$', text)
    
    return text

def convert_file(input_file, output_file):
    # Read the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Recursively convert LaTeX notation in the entire JSON structure
    def convert_recursively(obj):
        if isinstance(obj, dict):
            return {k: convert_recursively(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_recursively(item) for item in obj]
        elif isinstance(obj, str):
            return convert_latex_notation(obj)
        return obj
    
    # Apply conversion
    converted_data = convert_recursively(data)
    
    # Write the converted data to a new file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=4)

# Debug function to help diagnose conversion issues
def debug_convert_file(input_file, output_file):
    # Read the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    def convert_recursively(obj):
        if isinstance(obj, dict):
            return {k: convert_recursively(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_recursively(item) for item in obj]
        elif isinstance(obj, str):
            try:
                converted = convert_latex_notation(obj)
                print(f"Original: {repr(obj)}")
                print(f"Converted: {repr(converted)}")
                return converted
            except Exception as e:
                print(f"Error converting: {repr(obj)}")
                print(f"Error details: {e}")
                return obj
        return obj
    
    # Apply conversion
    converted_data = convert_recursively(data)
    
    # Write the converted data to a new file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=4)

# Uncomment to use
convert_file('JBDATA5.json', 'output.json')