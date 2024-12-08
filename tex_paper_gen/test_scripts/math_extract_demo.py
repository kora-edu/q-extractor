#from https://huggingface.co/spaces/Qwen/Qwen2-Math-Demo/tree/main
import gradio as gr
import os

os.system('pip install dashscope -U')
import tempfile
from pathlib import Path
import secrets
import dashscope
from dashscope import MultiModalConversation, Generation
from PIL import Image


# 设置API密钥
YOUR_API_TOKEN = os.getenv('YOUR_API_TOKEN')
dashscope.api_key = YOUR_API_TOKEN
math_messages = []
def process_image(image, shouldConvert=False):
    # 获取上传文件的目录
    global math_messages
    math_messages = [] # reset when upload image
    uploaded_file_dir = os.environ.get("GRADIO_TEMP_DIR") or str(
        Path(tempfile.gettempdir()) / "gradio"
    )
    os.makedirs(uploaded_file_dir, exist_ok=True)
    
    # 创建临时文件路径
    name = f"tmp{secrets.token_hex(20)}.jpg"
    filename = os.path.join(uploaded_file_dir, name)
    # 保存上传的图片
    if shouldConvert:
        new_img = Image.new('RGB', size=(image.width, image.height), color=(255, 255, 255))
        new_img.paste(image, (0, 0), mask=image)
        image = new_img
    image.save(filename)
    
    # 调用qwen-vl-max-0809模型处理图片
    messages = [{
        'role': 'system',
        'content': [{'text': 'You are a helpful assistant.'}]
    }, {
        'role': 'user',
        'content': [
            {'image': f'file://{filename}'},
            {'text': 'Please describe the math-related content in this image, ensuring that any LaTeX formulas are correctly transcribed. Non-mathematical details do not need to be described.'}
        ]
    }]
    
    response = MultiModalConversation.call(model='qwen-vl-max-0809', messages=messages)
    
    # 清理临时文件
    os.remove(filename)
    
    return response.output.choices[0]["message"]["content"]

def get_math_response(image_description, user_question):
    global math_messages
    if not math_messages:
        math_messages.append({'role': 'system', 'content': 'You are a helpful math assistant.'})
    math_messages = math_messages[:1]
    if image_description is not None:
        content = f'Image description: {image_description}\n\n'
    else:
        content = ''
    query = f"{content}User question: {user_question}"
    math_messages.append({'role': 'user', 'content': query})
    response = Generation.call(	
        model="qwen2-math-72b-instruct",
        messages=math_messages,	
        result_format='message',
        stream=True
    )
    answer = None
    for resp in response:
        if resp.output is None:
            continue
        answer = resp.output.choices[0].message.content
        yield answer.replace("\\", "\\\\")
    print(f'query: {query}\nanswer: {answer}')
    if answer is None:
        math_messages.pop()
    else:
        math_messages.append({'role': 'assistant', 'content': answer})


def math_chat_bot(image, sketchpad, question, state):
    current_tab_index = state["tab_index"]
    image_description = None
    # Upload
    if current_tab_index == 0:
        if image is not None:
            image_description = process_image(image)
    # Sketch
    elif current_tab_index == 1:
        print(sketchpad)
        if sketchpad and sketchpad["composite"]:
            image_description = process_image(sketchpad["composite"], True)
    yield from get_math_response(image_description, question)

css = """
#qwen-md .katex-display { display: inline; }
#qwen-md .katex-display>.katex { display: inline; }
#qwen-md .katex-display>.katex>.katex-html { display: inline; }
"""

def tabs_select(e: gr.SelectData, _state):
    _state["tab_index"] = e.index


# 创建Gradio接口
with gr.Blocks(css=css) as demo:
    gr.HTML("""\
<p align="center"><img src="https://modelscope.oss-cn-beijing.aliyuncs.com/resource/qwen.png" style="height: 60px"/><p>"""
            """<center><font size=8>📖 Qwen2-Math Demo</center>"""
            """\
<center><font size=3>This WebUI is based on Qwen2-VL for OCR and Qwen2-Math for mathematical reasoning. You can input either images or texts of mathematical or arithmetic problems.</center>"""
            )
    state = gr.State({"tab_index": 0})
    with gr.Row():
        with gr.Column():
            with gr.Tabs() as input_tabs:
                with gr.Tab("Upload"):
                    input_image = gr.Image(type="pil", label="Upload"),
                with gr.Tab("Sketch"):
                    input_sketchpad = gr.Sketchpad(type="pil", label="Sketch", layers=False)
            input_tabs.select(fn=tabs_select, inputs=[state])
            input_text = gr.Textbox(label="input your question")
            with gr.Row():
                with gr.Column():
                    clear_btn = gr.ClearButton(
                        [*input_image, input_sketchpad, input_text])
                with gr.Column():
                    submit_btn = gr.Button("Submit", variant="primary")
        with gr.Column():
            output_md = gr.Markdown(label="answer",
                                    latex_delimiters=[{
                                        "left": "\\(",
                                        "right": "\\)",
                                        "display": True
                                    }, {
                                        "left": "\\begin\{equation\}",
                                        "right": "\\end\{equation\}",
                                        "display": True
                                    }, {
                                        "left": "\\begin\{align\}",
                                        "right": "\\end\{align\}",
                                        "display": True
                                    }, {
                                        "left": "\\begin\{alignat\}",
                                        "right": "\\end\{alignat\}",
                                        "display": True
                                    }, {
                                        "left": "\\begin\{gather\}",
                                        "right": "\\end\{gather\}",
                                        "display": True
                                    }, {
                                        "left": "\\begin\{CD\}",
                                        "right": "\\end\{CD\}",
                                        "display": True
                                    }, {
                                        "left": "\\[",
                                        "right": "\\]",
                                        "display": True
                                    }],
                                    elem_id="qwen-md")
        submit_btn.click(
            fn=math_chat_bot,
            inputs=[*input_image, input_sketchpad, input_text, state],
            outputs=output_md)
demo.launch()