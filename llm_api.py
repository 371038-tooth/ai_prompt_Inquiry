import google.generativeai as genai
import openai
import json
import re

def generate_prompts_gemini(api_key, user_input):
    if not api_key:
        return None, "Gemini API Key is required."
    
    genai.configure(api_key=api_key)
    
    # Try preferred names first
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-2.0-flash',
        'gemini-1.5-pro',
    ]
    
    # Also fetch all available models to be super robust
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for m in available_models:
            clean_name = m.replace('models/', '')
            if clean_name not in models_to_try:
                models_to_try.append(clean_name)
    except Exception:
        pass # Fallback to hardcoded if listing fails
    
    last_error = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            
            prompt = create_system_prompt(user_input)
            response = model.generate_content(prompt)
            
            return parse_json_response(response.text, model_name)
                
        except Exception as e:
            last_error = str(e)
            if "404" in last_error or "429" in last_error:
                continue
            else:
                return None, f"Error with {model_name}: {last_error}"
    
    return None, f"All Gemini models ({len(models_to_try)}) failed. Please try ChatGPT instead. Last error: {last_error}"

def generate_prompts_openai(api_key, user_input):
    if not api_key:
        return None, "OpenAI API Key is required."
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        prompt = create_system_prompt(user_input)
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Default fast model
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return parse_json_response(response.choices[0].message.content, "gpt-4o-mini")
        
    except Exception as e:
        return None, f"OpenAI Error: {str(e)}"

def create_system_prompt(user_input):
    full_request = f"Stable Diffusion で利用するプロンプトを生成してください。\n要望: {user_input}"
    return f"""
Convert the following request into Stable Diffusion prompts (Positive and Negative).
Return the result in JSON format with the following keys:
- positive: The English positive prompt (comma-separated tags).
- negative: The English negative prompt (comma-separated tags).
- pos_mapping: A list of objects with "word" (English tag from positive) and "translation" (Japanese meaning).
- neg_mapping: A list of objects with "word" (English tag from negative) and "translation" (Japanese meaning).

Request: {full_request}

Response MUST be ONLY the JSON object.
"""

def parse_json_response(text, model_name):
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            return data, None
        else:
            return None, f"Failed to parse JSON response from {model_name}."
    except Exception as e:
        return None, f"JSON parse error from {model_name}: {str(e)}"

def generate_prompts(llm_type, api_key, user_input):
    if llm_type == "ChatGPT":
        return generate_prompts_openai(api_key, user_input)
    else:
        return generate_prompts_gemini(api_key, user_input)
