import openai
from dotenv import load_dotenv

load_dotenv()


class SemanticManager:
    def __init__(self):
        self.client = openai.OpenAI()

    def get_semantic_response(self, system, user, model="gpt-4o", temperature=0.0):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return str(response.choices[0].message.content)
