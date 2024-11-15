import subprocess
import os
import json

data_path = 'JBdata5.json'
with open(data_path, 'r') as f:
    jbdata = json.load(f)


questions = [
    {
        "text": q["query"],
        "type": "multiple_choice" if "options" in q else "written",
        "options": q.get("options", [])  # Default to empty list if no options
    }
    for q in jbdata
]

output_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(output_dir, exist_ok=True) 

# def generate_latex_code(questions):
#     latex_content = r"""
# \documentclass{exam}
# \usepackage{amsmath}
# \begin{document}
# \title{Automated Exam Paper}
# \maketitle
# \begin{questions}
# """
#     for q in questions:
#         latex_content += r"\question " + q['text'] + "\n"
#         if q['type'] == 'multiple_choice':
#             latex_content += r"\begin{choices}"
#             for option in q['options']:
#                 latex_content += r"\choice " + option + "\n"
#             latex_content += r"\end{choices}"
#         elif q['type'] == 'written':
#             latex_content += r"\vspace{3cm}"  # Space for answer
#         latex_content += "\n"  # Newline for each question
#     latex_content += r"""
# \end{questions}
# \end{document}
# """
#     return latex_content

def generate_latex_code(questions):
    latex_content = r"""
\documentclass{article}
\usepackage{fontspec}
\usepackage{unicode-math}
\usepackage{amsmath}
\usepackage[a4paper,margin=1in]{geometry}
\setlength{\parskip}{1em}  % Add spacing between questions
\begin{document}
\title{json -> latex convert test}
\author{}
\date{}
\maketitle
\section*{Questions}
\begin{enumerate}
"""
    for q in questions:
        # Add question text
        latex_content += r"\item " + q['text'] + "\n"
        # Add space for written answers (default)
        latex_content += r"\vspace{3cm}"  # Space for answer
        latex_content += "\n"  # Newline for each question
    latex_content += r"""
\end{enumerate}
\end{document}
"""
    return latex_content

def save_latex_file(content, filename="exam.tex"):
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as file:  # Save as UTF-8
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
