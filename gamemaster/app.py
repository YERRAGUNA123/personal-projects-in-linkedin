# app.py
import gradio as gr
from dungeon_core import get_story_and_options, generate_image

state = {
    "history": "You wake up in a dark dungeon with only a torch and a rusty sword.",
    "choices": [],
    "image_path": ""
}

def advance(choice=None):
    if choice:
        state["history"] += f"\n\nYou chose: {choice}"
    
    story, choices = get_story_and_options(state["history"])
    state["history"] += f"\n\n{story}"
    image_path = generate_image(story[:200])
    state["choices"] = choices
    state["image_path"] = image_path
    return state["history"], image_path, gr.update(choices=choices)

with gr.Blocks() as demo:
    gr.Markdown("## 🧙 AI Dungeon Master (Gradio Edition)")

    story_box = gr.Textbox(label="Story So Far", lines=15)
    image_output = gr.Image(label="Scene")
    choices_buttons = gr.Radio(choices=[], label="Choose your action")
    submit_btn = gr.Button("Continue")

    submit_btn.click(fn=advance, inputs=choices_buttons, outputs=[story_box, image_output, choices_buttons])
    demo.load(fn=lambda: advance(), outputs=[story_box, image_output, choices_buttons])

demo.launch()
