import os
import google.generativeai as genai


def enhance_resume_text(raw_text):
    """
    Enhances resume bullet points using Gemini AI with token optimization.
    Strictly follows facts and does not invent data.
    Limits response length to reduce token consumption.
    """
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(
            'gemini-flash-latest',
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 300  # Limit response to 300 tokens (~1200 chars)
            }
        )

        # Simplified prompt to reduce token usage
        prompt = f"""Act as a professional resume writer. Rewrite the following rough bullet points to be impactful and action-oriented.

STRICT RULES:
1. Use ONLY information provided - NO fabrication
2. For simple inputs (<5 words), return exactly 1 bullet point
3. For longer inputs, return maximum 2-3 bullet points
4. Start each bullet with a strong action verb
5. Keep it concise and professional
6. Return ONLY the bullet points (no extra text)

Input Text:
{raw_text}"""

        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        error_str = str(e)
        # Handle quota exceeded error
        if "429" in error_str or "quota" in error_str.lower():
            # Return a basic enhanced version without API
            return f"* {raw_text.strip()}" if raw_text.strip() else "* No content provided"
        raise