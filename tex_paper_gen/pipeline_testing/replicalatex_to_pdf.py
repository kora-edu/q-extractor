import subprocess
import os
import json
from datetime import date
date = date.today()

in_dir = "replica_entries"
output_dir = os.path.join(os.path.dirname(__file__), "extracted_latex")
os.makedirs(output_dir, exist_ok=True)

latex_pdfs = {os.path.splitext(pdf)[0] for pdf in os.listdir(output_dir) if pdf.endswith(".pdf")}

latex_dict = {}

# only process .jsons that dont have a pdf yet(i.e haven't been converted)
for filename in os.listdir(in_dir):
    if filename.endswith(".json"):
        json_name_noext= os.path.splitext(filename)[0]
        if json_name_noext not in latex_pdfs:

            file_path = os.path.join(in_dir, filename)
            with open(file_path, 'r') as f:
                jbdata = json.load(f)

            questions = [
                {
                    "text": q["question"].strip('"'),
                    "type": "multiple_choice" if "options" in q else "written",
                    "points": 5,
                    "options": q.get("options", [])
                }
                for q in jbdata
            ]
            
            latex_dict[filename] = questions


def generate_latex_code(questions):
    latex_content = r"""
\documentclass[12pt,addpoints]{exam}
\usepackage{fontspec}
\usepackage{unicode-math}
\usepackage{amsmath}
\usepackage[a4paper,margin=1in]{geometry}
\usepackage{setspace}


\begin{document}
\title{json -> latex convert test}
\author{kora}
\date{}
\maketitle
\section*{Questions}
\begin{questions}
\pointsinrightmargin
\bracketedpoints
"""
    for q in questions:
        latex_content += rf"\question[{q['points']}] " + q['text'] + "\n"   
        latex_content += r"\fillwithlines{3cm}"
        latex_content += "\n"  
    latex_content += r"""
\end{questions}
\end{document}
"""
    return latex_content

def save_latex_file(content, filename):
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as file:  # save as UTF-8
        file.write(content)
    return filepath

def compile_latex(filename):
    filepath = os.path.join(output_dir, filename)
    subprocess.run(["lualatex", "-output-directory", output_dir, filepath], check=True)


def generate_exam_pdf(questions, fname):
    latex_content = generate_latex_code(questions)
    tex_filepath = save_latex_file(latex_content, fname)
    compile_latex(os.path.basename(tex_filepath)) 


for json in latex_dict:
    generate_exam_pdf(latex_dict[json], json)
