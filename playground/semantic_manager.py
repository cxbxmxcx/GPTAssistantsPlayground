from playground.llms import get_llm_client


class SemanticManager:
    def __init__(self):
        self.client = get_llm_client()

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
