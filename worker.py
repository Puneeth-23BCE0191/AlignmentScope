from dotenv import load_dotenv
from openai import OpenAI
import os
import json

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_reasoning(user_prompt):
    prompt = f"""
You are a reasoning agent.

Task:
{user_prompt}

Generate exactly 5 short reasoning steps.
Each step must be under 10 words.
Also generate the final answer.

Return ONLY valid JSON, no markdown, no backticks.

{{
    "steps": ["", "", "", "", ""],
    "answer": ""
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    text = response.choices[0].message.content.strip()
    return json.loads(text)