import modules.script_callbacks as script_callbacks
import gradio as gr
import json
import os
from llm_api import generate_prompts

# Path for config file
# Using realpath to handle symlinks correctly
script_path = os.path.realpath(__file__)
base_dir = os.path.dirname(os.path.dirname(script_path))
config_path = os.path.join(base_dir, "config.json")

def load_config():
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"[AIPI] Config loaded successfully from {config_path}")
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"[AIPI] Error loading config from {config_path}: {e}")
    else:
        print(f"[AIPI] Config file not found at {config_path}")
        # Diagnostic: show what is in the base_dir
        if os.path.exists(base_dir):
            try:
                files = os.listdir(base_dir)
                print(f"[AIPI] Files in {base_dir}: {files}")
            except Exception as e:
                print(f"[AIPI] Could not list files in {base_dir}: {e}")
        else:
            print(f"[AIPI] Base directory does not exist: {base_dir}")
    return {}

def save_config(llm_type, gemini_key, openai_key):
    try:
        config = load_config()
        config["llm_type"] = llm_type
        config["gemini_key"] = gemini_key
        config["openai_key"] = openai_key
        # Ensure directory exists
        config_dir = os.path.dirname(config_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            print(f"[AIPI] Created directory: {config_dir}")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"[AIPI] Config saved successfully to {config_path}")
    except Exception as e:
        print(f"[AIPI] Error saving config to {config_path}: {e}")

def on_ui_tabs():
    config = load_config()
    saved_llm = config.get("llm_type", "ChatGPT") # Default to ChatGPT since user said it works
    saved_gemini = config.get("gemini_key", "")
    saved_openai = config.get("openai_key", "")

    with gr.Blocks(analytics_enabled=False) as aipi_interface:
        with gr.Row():
            llm_type = gr.Dropdown(choices=["Gemini", "ChatGPT"], value=saved_llm, label="Select LLM")
            
        with gr.Row():
            gemini_key = gr.Textbox(
                value=saved_gemini,
                label="Gemini API Key", 
                placeholder="Enter Gemini API Key", 
                type="password",
                visible=(saved_llm == "Gemini")
            )
            openai_key = gr.Textbox(
                value=saved_openai,
                label="OpenAI API Key", 
                placeholder="Enter OpenAI API Key", 
                type="password",
                visible=(saved_llm == "ChatGPT")
            )
            
        def update_api_visibility(llm):
            return gr.update(visible=(llm == "Gemini")), gr.update(visible=(llm == "ChatGPT"))
            
        llm_type.change(fn=update_api_visibility, inputs=[llm_type], outputs=[gemini_key, openai_key])
        
        # Auto-save: Use .input for textboxes so it only triggers on user typing, 
        # not when values are programmatically set during initialization.
        llm_type.change(fn=save_config, inputs=[llm_type, gemini_key, openai_key], outputs=[])
        gemini_key.input(fn=save_config, inputs=[llm_type, gemini_key, openai_key], outputs=[])
        openai_key.input(fn=save_config, inputs=[llm_type, gemini_key, openai_key], outputs=[])

        def refresh_settings():
            config = load_config()
            saved_llm = config.get("llm_type", "ChatGPT")
            saved_gemini = config.get("gemini_key", "")
            saved_openai = config.get("openai_key", "")
            return (
                gr.update(value=saved_llm),
                gr.update(value=saved_gemini, visible=(saved_llm == "Gemini")),
                gr.update(value=saved_openai, visible=(saved_llm == "ChatGPT"))
            )

        aipi_interface.load(fn=refresh_settings, inputs=[], outputs=[llm_type, gemini_key, openai_key])
        
        with gr.Row():
            user_input = gr.Textbox(label="Input prompt (Japanese)", placeholder="日本語で要求を入力してください...", lines=3)
        
        with gr.Row():
            generate_btn = gr.Button("Generate", variant="primary")
            both_send_btn = gr.Button("Send Both to txt2img", variant="secondary", elem_id="gemini_both_send")
        
        error_display = gr.HTML(visible=False)
        
        with gr.Row():
            with gr.Column(scale=2):
                with gr.Row():
                    pos_prompt = gr.Textbox(label="Positive Prompt", interactive=True, elem_id="gemini_pos_prompt")
                    pos_send_btn = gr.Button("📋", elem_id="gemini_pos_send", scale=0)
                with gr.Row():
                    neg_prompt = gr.Textbox(label="Negative Prompt", interactive=True, elem_id="gemini_neg_prompt")
                    neg_send_btn = gr.Button("📋", elem_id="gemini_neg_send", scale=0)
            
            with gr.Column(scale=1):
                gr.Markdown("### 日本語訳 (Positive)")
                pos_translation_display = gr.HTML(elem_id="gemini_pos_translation_display")
                gr.Markdown("### 日本語訳 (Negative)")
                neg_translation_display = gr.HTML(elem_id="gemini_neg_translation_display")

        def on_generate(llm, g_key, o_key, text):
            # Save settings immediately
            save_config(llm, g_key, o_key)

            api_key = g_key if llm == "Gemini" else o_key
            data, error = generate_prompts(llm, api_key, text)
            
            if error:
                error_html = f"<div style='color: red; padding: 10px; border: 1px solid red; border-radius: 5px;'>{error}</div>"
                return gr.update(visible=True, value=error_html), gr.update(), gr.update(), gr.update(value=""), gr.update(value="")
            
            pos = data.get("positive", "")
            neg = data.get("negative", "")
            pos_mapping = data.get("pos_mapping", [])
            neg_mapping = data.get("neg_mapping", [])
            
            def create_mapping_html(mapping):
                if not mapping: return ""
                html = "<div class='translation-container'>"
                for item in mapping:
                    html += f"<div class='translation-item' data-word='{item['word']}'>{item['word']}: {item['translation']}</div>"
                html += "</div>"
                return html

            pos_html = create_mapping_html(pos_mapping)
            neg_html = create_mapping_html(neg_mapping)
            
            return gr.update(visible=False, value=""), gr.update(value=pos), gr.update(value=neg), gr.update(value=pos_html), gr.update(value=neg_html)

        generate_btn.click(
            fn=on_generate,
            inputs=[llm_type, gemini_key, openai_key, user_input],
            outputs=[error_display, pos_prompt, neg_prompt, pos_translation_display, neg_translation_display]
        )

    return [(aipi_interface, "AIPI", "aipi_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
