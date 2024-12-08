import subprocess
import os
import json
from datetime import date

data_path = 'output.json'
with open(data_path, 'r') as f:
    jbdata = json.load(f)

date = date.today()

questions = [
    {
        "text": q["question"].strip('"'),
        "type": "multiple_choice" if "options" in q else "written", #is multi if q's entry contains an "options" row
        "points": 5, #temporary, each q will be assigned accordingly by model
        "options": q.get("options", [])  #default to empty list if no options
    }
    for q in jbdata
]


output_dir = os.path.join(os.path.dirname(__file__), "extracted_latex")
os.makedirs(output_dir, exist_ok=True) 


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

def save_latex_file(content, filename="exam.tex"):
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as file:  # save as UTF-8
        file.write(content)
    return filepath

def compile_latex(filename="exam.tex"):
    filepath = os.path.join(output_dir, filename)
    subprocess.run(["lualatex", "-output-directory", output_dir, filepath], check=True)


def generate_exam_pdf(questions):
    latex_content = generate_latex_code(questions)
    tex_filepath = save_latex_file(latex_content)
    compile_latex(os.path.basename(tex_filepath)) 


generate_exam_pdf(questions)
