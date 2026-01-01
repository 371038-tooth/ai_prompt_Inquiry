import modules.script_callbacks as script_callbacks
import gradio as gr
import json
import os
from llm_api import generate_prompts

# Path for config files
script_path = os.path.abspath(__file__)
base_dir = os.path.dirname(os.path.dirname(script_path))
config_path = os.path.join(base_dir, "config.json")
presets_path = os.path.join(base_dir, "presets.json")

print(f"[AIPI] Base Directory: {base_dir}")
print(f"[AIPI] Config Path: {config_path}")
print(f"[AIPI] Presets Path: {presets_path}")

def load_json(path):
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if data else {}
        except Exception as e:
            print(f"[AIPI] Error loading JSON from {abs_path}: {e}")
    return {}

def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[AIPI] Error saving JSON to {path}: {e}")

def load_config():
    return load_json(config_path)

def save_config(llm_type, gemini_key, openai_key, grok_key, prompt_settings_enabled, quality_tags_enabled, quality_tags_preset, bottom_mandatory_enabled, bottom_mandatory_preset, user_input):
    config = load_config()
    config.update({
        "llm_type": llm_type,
        "gemini_key": gemini_key,
        "openai_key": openai_key,
        "grok_key": grok_key,
        "prompt_settings_enabled": prompt_settings_enabled,
        "quality_tags_enabled": quality_tags_enabled,
        "quality_tags_preset": quality_tags_preset,
        "bottom_mandatory_enabled": bottom_mandatory_enabled,
        "bottom_mandatory_preset": bottom_mandatory_preset,
        "user_input": user_input
    })
    save_json(config_path, config)

def on_ui_tabs():
    config = load_config()
    presets = load_json(presets_path)
    if "quality_tags" not in presets: presets["quality_tags"] = {}
    if "bottom_mandatory" not in presets: presets["bottom_mandatory"] = {}

    with gr.Blocks(analytics_enabled=False) as aipi_interface:
        # Modal Layer
        with gr.Group(visible=False) as preset_edit_modal_wrapper:
            with gr.Group(elem_id="aipi_preset_modal"):
                with gr.Box(elem_id="aipi_preset_modal_content"):
                    gr.Markdown("## 🖌️ プリセット編集")
                    preset_category = gr.State("")
                    preset_edit_name = gr.Dropdown(label="プリセット名（新規は直接入力）", allow_custom_value=True, choices=[""], info="既存を選択または新しい名前を入力")
                    preset_edit_content = gr.Textbox(label="プロンプト内容", lines=4, placeholder="カンマ区切りでタグを入力...")
                    with gr.Row():
                        preset_save_btn = gr.Button("💾 保存", variant="primary", scale=2)
                        preset_delete_btn = gr.Button("🗑️ 削除", variant="stop", scale=1)
                        preset_close_btn = gr.Button("✕ 閉じる", scale=1)

        with gr.Column(elem_id="aipi_main_container"):
            # LLM Settings Group
            with gr.Group(elem_id="aipi_llm_settings_group"):
                gr.Markdown("### LLM設定")
                with gr.Row():
                    llm_type = gr.Dropdown(choices=["Gemini", "ChatGPT", "Grok"], value=config.get("llm_type", "ChatGPT"), label="LLM選択", scale=1)
                    gemini_key = gr.Textbox(value=config.get("gemini_key", ""), label="API Key (Gemini)", type="password", visible=(config.get("llm_type") == "Gemini"), scale=2)
                    openai_key = gr.Textbox(value=config.get("openai_key", ""), label="API Key (ChatGPT)", type="password", visible=(config.get("llm_type") == "ChatGPT"), scale=2)
                    grok_key = gr.Textbox(value=config.get("grok_key", ""), label="API Key (Grok)", type="password", visible=(config.get("llm_type") == "Grok"), scale=2)



            with gr.Row():
                user_input = gr.Textbox(value=config.get("user_input", ""), label="Input prompt (Japanese)", placeholder="日本語で要求を入力してください...", lines=3)


        # Modal logic


        
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

        # Prompt Settings Accordion with integrated checkbox (ADetailer style)
        with gr.Row(elem_classes="aipi_accordion_header"):
            prompt_settings_enabled = gr.Checkbox(value=config.get("prompt_settings_enabled", False), label="", scale=0, elem_id="aipi_prompt_settings_checkbox")
            with gr.Accordion("プロンプト設定", open=False, elem_id="aipi_prompt_settings_accordion") as prompt_settings_accordion:
                # Quality Tags Section
                with gr.Row():
                    quality_tags_enabled = gr.Checkbox(value=config.get("quality_tags_enabled", False), label="品質タグ固定", scale=0)
                    gr.Markdown("<small>先頭に指定した品質タグを固定付与。他の品質タグは出力されません。ネガティブとの整合性も考慮されます。</small>", elem_classes="aipi_description")
                with gr.Row(elem_classes="aipi_preset_row"):
                    quality_tags_preset = gr.Dropdown(choices=[""] + list(presets.get("quality_tags", {}).keys()), value=config.get("quality_tags_preset", ""), label="プリセット名", scale=3)
                    quality_tags_edit_btn = gr.Button("🖌️", elem_id="aipi_quality_tags_edit_btn", elem_classes="aipi_edit_btn")
                quality_tags_prompt = gr.Textbox(value=presets.get("quality_tags", {}).get(config.get("quality_tags_preset", ""), ""), label="品質タグ", placeholder="品質タグを入力...", lines=2, interactive=True)
                
                # Bottom Mandatory Section
                with gr.Row():
                    bottom_mandatory_enabled = gr.Checkbox(value=config.get("bottom_mandatory_enabled", False), label="最下部タグ付与", scale=0)
                    gr.Markdown("<small>Positiveプロンプトの末尾に指定タグを付与。ネガティブとの整合性も考慮されます。</small>", elem_classes="aipi_description")
                with gr.Row(elem_classes="aipi_preset_row"):
                    bottom_mandatory_preset = gr.Dropdown(choices=[""] + list(presets.get("bottom_mandatory", {}).keys()), value=config.get("bottom_mandatory_preset", ""), label="プリセット名", scale=3)
                    bottom_mandatory_edit_btn = gr.Button("🖌️", elem_id="aipi_bottom_mandatory_edit_btn", elem_classes="aipi_edit_btn")
                bottom_mandatory_prompt = gr.Textbox(value=presets.get("bottom_mandatory", {}).get(config.get("bottom_mandatory_preset", ""), ""), label="最下部タグ", placeholder="最下部タグを入力...", lines=2, interactive=True)

        def on_generate(llm, g_key, o_key, gr_key, prompt_settings_enabled, quality_tags_enabled, quality_tags_preset, bottom_mandatory_enabled, bottom_mandatory_preset, text, qt_prompt, bm_prompt):
            # Save settings (saving presets names)
            save_config(llm, g_key, o_key, gr_key, prompt_settings_enabled, quality_tags_enabled, quality_tags_preset, bottom_mandatory_enabled, bottom_mandatory_preset, text)

            api_key = g_key if llm == "Gemini" else (o_key if llm == "ChatGPT" else gr_key)
            
            # Pass quality tags constraint to LLM if enabled (using the actual textbox content)
            data, error = generate_prompts(llm, api_key, text, quality_tags=(qt_prompt if (prompt_settings_enabled and quality_tags_enabled) else None))
            
            if error:
                error_html = f"<div style='color: red; padding: 10px; border: 1px solid red; border-radius: 5px;'>{error}</div>"
                return gr.update(visible=True, value=error_html), gr.update(), gr.update(), gr.update(value=""), gr.update(value="")
            
            pos = data.get("positive", "")
            neg = data.get("negative", "")
            
            # Apply Prompt Settings only if master toggle is enabled
            if prompt_settings_enabled:
                # 1. Quality Tags filtering (Final client-side check)
                if quality_tags_enabled and qt_prompt:
                    input_quality_tags = [t.strip() for t in qt_prompt.split(",") if t.strip()]
                    common_quality_tags = ["masterpiece", "best quality", "ultra high res", "highres", "extremely detailed", "8k", "4k"]
                    pos_tags = [t.strip() for t in pos.split(",")]
                    filtered_tags = []
                    quality_tags_to_prepend = []

                    # First, identify already present quality tags or ones we want to keep
                    for t in pos_tags:
                        t_lower = t.lower()
                        is_quality = any(q in t_lower for q in common_quality_tags)
                        if is_quality:
                            # Keep only if it's one of the explicitly requested tags
                            if any(it.lower() in t_lower for it in input_quality_tags):
                                quality_tags_to_prepend.append(t)
                        else:
                            filtered_tags.append(t)
                    
                    # Ensure all input quality tags are in the prepend list
                    for it in input_quality_tags:
                        if not any(it.lower() in q.lower() for q in quality_tags_to_prepend):
                            quality_tags_to_prepend.insert(0, it)
                    
                    # Prepend all quality tags
                    pos = ", ".join(quality_tags_to_prepend + filtered_tags)

                # 2. Bottom Mandatory
                if bottom_mandatory_enabled and bm_prompt:
                    bm_tags = [t.strip() for t in bm_prompt.split(",") if t.strip()]
                    pos_tags = [t.strip() for t in pos.split(",")]
                    # Remove duplicates from current pos
                    pos_tags = [t for t in pos_tags if not any(bt.lower() == t.lower() for bt in bm_tags)]
                    # Append bm_tags
                    pos = ", ".join(pos_tags + bm_tags)

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

        # Modal logic
        def open_preset_edit(cat):
            ps = load_json(presets_path)
            choices = [""] + list(ps.get(cat, {}).keys())
            return gr.update(visible=True), cat, gr.update(choices=choices, value=""), ""
        
        quality_tags_edit_btn.click(fn=open_preset_edit, inputs=[gr.State("quality_tags")], outputs=[preset_edit_modal_wrapper, preset_category, preset_edit_name, preset_edit_content])
        bottom_mandatory_edit_btn.click(fn=open_preset_edit, inputs=[gr.State("bottom_mandatory")], outputs=[preset_edit_modal_wrapper, preset_category, preset_edit_name, preset_edit_content])

        def on_preset_name_input(name, cat):
            ps = load_json(presets_path)
            content = ps.get(cat, {}).get(name)
            if content is not None:
                return content
            return gr.update() # Don't update/clear if not found
        
        preset_edit_name.change(fn=on_preset_name_input, inputs=[preset_edit_name, preset_category], outputs=[preset_edit_content])

        def save_preset(cat, name, content):
            if not name: return [gr.update()] * 6
            ps = load_json(presets_path)
            if cat not in ps: ps[cat] = {}
            ps[cat][name] = content
            save_json(presets_path, ps)
            
            # Refresh choices for ALL relevant dropdowns
            qt_choices = [""] + list(ps.get("quality_tags", {}).keys())
            bm_choices = [""] + list(ps.get("bottom_mandatory", {}).keys())
            edit_choices = [""] + list(ps.get(cat, {}).keys())
            
            qt_upd = gr.update(choices=qt_choices, value=name) if cat == "quality_tags" else gr.update(choices=qt_choices)
            bm_upd = gr.update(choices=bm_choices, value=name) if cat == "bottom_mandatory" else gr.update(choices=bm_choices)
            
            # Sync the textboxes
            qt_prompt_upd = gr.update(value=content) if cat == "quality_tags" else gr.update()
            bm_prompt_upd = gr.update(value=content) if cat == "bottom_mandatory" else gr.update()
            
            edit_upd = gr.update(choices=edit_choices, value=name)
            
            return qt_upd, bm_upd, qt_prompt_upd, bm_prompt_upd, edit_upd, gr.update(visible=False)

        def delete_preset(cat, name):
            if not name: return [gr.update()] * 6
            ps = load_json(presets_path)
            if cat in ps and name in ps[cat]:
                del ps[cat][name]
                save_json(presets_path, ps)
            
            qt_choices = [""] + list(ps.get("quality_tags", {}).keys())
            bm_choices = [""] + list(ps.get("bottom_mandatory", {}).keys())
            edit_choices = [""] + list(ps.get(cat, {}).keys())
            
            qt_upd = gr.update(choices=qt_choices, value="") if cat == "quality_tags" else gr.update(choices=qt_choices)
            bm_upd = gr.update(choices=bm_choices, value="") if cat == "bottom_mandatory" else gr.update(choices=bm_choices)
            
            qt_prompt_upd = gr.update(value="") if cat == "quality_tags" else gr.update()
            bm_prompt_upd = gr.update(value="") if cat == "bottom_mandatory" else gr.update()
            
            edit_upd = gr.update(choices=edit_choices, value="")
            
            return qt_upd, bm_upd, qt_prompt_upd, bm_prompt_upd, edit_upd, gr.update(visible=False)

        preset_save_btn.click(fn=save_preset, inputs=[preset_category, preset_edit_name, preset_edit_content], outputs=[quality_tags_preset, bottom_mandatory_preset, quality_tags_prompt, bottom_mandatory_prompt, preset_edit_name, preset_edit_modal_wrapper])
        preset_delete_btn.click(fn=delete_preset, inputs=[preset_category, preset_edit_name], outputs=[quality_tags_preset, bottom_mandatory_preset, quality_tags_prompt, bottom_mandatory_prompt, preset_edit_name, preset_edit_modal_wrapper])
        preset_close_btn.click(fn=lambda: gr.update(visible=False), outputs=[preset_edit_modal_wrapper])

        def on_load():
            ps = load_json(presets_path)
            qt_choices = [""] + list(ps.get("quality_tags", {}).keys())
            bm_choices = [""] + list(ps.get("bottom_mandatory", {}).keys())
            cfg = load_config()
            qt_preset = cfg.get("quality_tags_preset", "")
            bm_preset = cfg.get("bottom_mandatory_preset", "")
            qt_prompt_val = ps.get("quality_tags", {}).get(qt_preset, "")
            bm_prompt_val = ps.get("bottom_mandatory", {}).get(bm_preset, "")
            return (
                gr.update(choices=qt_choices, value=qt_preset),
                gr.update(choices=bm_choices, value=bm_preset),
                gr.update(value=qt_prompt_val),
                gr.update(value=bm_prompt_val)
            )

        aipi_interface.load(fn=on_load, outputs=[quality_tags_preset, bottom_mandatory_preset, quality_tags_prompt, bottom_mandatory_prompt])

        def update_llm_visibility(llm):
            return gr.update(visible=(llm == "Gemini")), gr.update(visible=(llm == "ChatGPT")), gr.update(visible=(llm == "Grok"))
        
        llm_type.change(fn=update_llm_visibility, inputs=[llm_type], outputs=[gemini_key, openai_key, grok_key])

        # Preset logic
        def on_preset_change(preset_name, category):
            ps = load_json(presets_path)
            return ps.get(category, {}).get(preset_name, "")

        quality_tags_preset.change(fn=on_preset_change, inputs=[quality_tags_preset, gr.State("quality_tags")], outputs=[quality_tags_prompt])
        bottom_mandatory_preset.change(fn=on_preset_change, inputs=[bottom_mandatory_preset, gr.State("bottom_mandatory")], outputs=[bottom_mandatory_prompt])

        # Auto-save settings
        all_settings = [llm_type, gemini_key, openai_key, grok_key, prompt_settings_enabled, quality_tags_enabled, quality_tags_preset, bottom_mandatory_enabled, bottom_mandatory_preset, user_input]
        for s in all_settings:
            if isinstance(s, gr.Textbox):
                s.input(fn=save_config, inputs=all_settings, outputs=[])
            else:
                s.change(fn=save_config, inputs=all_settings, outputs=[])

        generate_btn.click(
            fn=on_generate,
            inputs=[llm_type, gemini_key, openai_key, grok_key, prompt_settings_enabled, quality_tags_enabled, quality_tags_preset, bottom_mandatory_enabled, bottom_mandatory_preset, user_input, quality_tags_prompt, bottom_mandatory_prompt],
            outputs=[error_display, pos_prompt, neg_prompt, pos_translation_display, neg_translation_display]
        )

    return [(aipi_interface, "AIPI", "aipi_tab")]

script_callbacks.on_ui_tabs(on_ui_tabs)
