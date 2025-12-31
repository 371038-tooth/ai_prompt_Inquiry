import google.generativeai as genai
import json
import re

def generate_prompts(api_key, user_input):
    if not api_key:
        return None, "API Key is required."
    
    genai.configure(api_key=api_key)
    
    # Try multiple common model names in case of 404
    models_to_try = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-8b',
        'gemini-1.5-pro',
        'gemini-1.0-pro'
    ]
    
    last_error = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            
            prompt = f"""
Convert the following Japanese request into Stable Diffusion prompts (Positive and Negative).
Return the result in JSON format with the following keys:
- positive: The English positive prompt (comma-separated tags).
- negative: The English negative prompt (comma-separated tags).
- mapping: A list of objects with "word" (English tag from positive/negative) and "translation" (Japanese meaning).

Japanese Request: {user_input}

Response MUST be ONLY the JSON object.
"""

            response = model.generate_content(prompt)
            
            # Extract JSON from response text
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return data, None
            else:
                return None, f"Failed to parse JSON from Gemini response ({model_name})."
                
        except Exception as e:
            last_error = str(e)
            if "404" in last_error:
                continue # Try next model
            else:
                return None, f"Error with {model_name}: {last_error}"
    
    return None, f"All models failed. Last error: {last_error}"

