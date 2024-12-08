import json

#assisting model to trigger tag during inference (on top of using kto_tag)
input_file = "JBdata5.json"
output_file = "JBdata5_updated.json"


try:
    with open(input_file, "r", encoding="utf-8") as file:
        data = json.load(file)
except FileNotFoundError:
    print(f"Error: {input_file} not found.")
    exit()
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}")
    exit()

#prepending the value of type row to the query
for entry in data:
    if "query" in entry and "type" in entry:
        type_tag = entry["type"]
        entry["query"] = f"[{type_tag}] {entry['query']}"

# Save the updated dataset to a new file
with open(output_file, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print(f"Updated dataset has been saved to {output_file}")
