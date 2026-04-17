import os
import google.generativeai as genai


def enhance_resume_text(raw_text):
    """
    Enhances resume bullet points using Gemini AI.
    Strictly follows facts and does not invent data.
    """
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-flash-latest',generation_config={"temperature": 0.2} )

    # Prompt engineering for professional enhancement without fabrication
    prompt = f""".
    Act as a professional resume writer. Rewrite the following rough bullet points 
    to be impactful and action-oriented using strong verbs (e.g., 'Spearheaded', 'Optimized').

    RULES:
    
 
7.No Hallucinations: Do not add specific metrics, ranks, or leadership roles not present in the input.

8.Proportional Output: For short inputs (like "NCC" or "Fixed bugs"), generate MAX 1-2 points. Do not expand small tasks into a 5-point list.

9.Fact-First: If the input lacks detail, keep the output professional but general. (e.g., "NCC" → "Undergoing disciplined leadership and physical training as an NCC cadet.")

10.Combine Related Tasks: Do not split one workflow into multiple bullets.

11.Return ONLY the enhanced bullet points.
  1. Factual Integrity: Use only the provided information; do not invent metrics, tools, or scope.

2.Strict Point Limit: Use 1 bullet point for simple tasks. Use a maximum of 2-3 points only if the input describes multiple distinct achievements.

3.Consolidation: Do not split a single achievement into multiple bullets to fill space.

4.Action-Result Focus: Start with a strong verb and follow with the specific task or outcome. If no outcome is provided, do not make one up.

5.No Redundancy: Do not rephrase the same idea using different synonyms to create additional points.

6.Output Format: Return ONLY the bullet points.

Example of the result:
Input: "NCC"
Output: * Participating in rigorous physical training and leadership development modules to build discipline and teamwork

    # 1. DO NOT add fake metrics, numbers, or experiences not present in the input.
    # 2. Maintain 100% factual accuracy.
    # 3. If the input is too vague, just clean the grammar and keep it professional.
    # 4. Return ONLY the enhanced bullet points separated by newlines.
    # 5.Do not repeat the same thing nd use your own mind how to describe the thing written nd do not exagerrate use no of points wisely.
    # 6.Do not exaggerate.use only 2 small or max 3 points if entered text is small.
    # 1. NO HALLUCINATIONS: Do not mention 'disaster relief', 'infrastructure', 'management', or 'construction' unless explicitly in the input. 
    # 2. RATIO RULE: If the input is < 5 words (e.g., "NCC", "Fixed bugs"), you MUST return exactly ONE bullet point.
    # 3. NO FAKE IMPACT: Do not use fluff like 'high-impact' or 'large-scale' unless the input provides data to support it.
    # 4. ACTION-RESULT: Start with a strong verb. If the input is just an organization name, focus on "Participated in" or "Trained in."
    # 5. NO REPETITION: Do not rephrase the same task into multiple points.
    # 6. OUTPUT FORMAT: Return ONLY the bullets. No conversational text or explanations.

    Input Text:
    {raw_text}
    """

    response = model.generate_content(prompt)
    return response.text.strip()