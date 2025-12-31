import launch

if not launch.is_installed("google-generativeai"):
    launch.run_pip("install google-generativeai", "requirements for Gemini Prompt Inquiry")

if not launch.is_installed("openai"):
    launch.run_pip("install openai", "requirements for Gemini Prompt Inquiry")
