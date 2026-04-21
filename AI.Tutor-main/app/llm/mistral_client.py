from mistralai.client import MistralClient
from app.config.settings import settings


class MistralService:
    def __init__(self):
        self.client = MistralClient(api_key=settings.MISTRAL_API_KEY)

    def generate_response(self, context: str, query: str) -> str:
        system_prompt = (
            "You are a helpful retrieval-augmented assistant.\n"
            "Your goal is to answer questions using the provided context snippets.\n"
            "1. If the context contains the answer, explain it clearly.\n"
            "2. If the context mentions names or details closely related to the question, you can use them.\n"
            "3. If the answer is absolutely NOT in the context, say 'The answer is not available in the provided documents.'\n"
            "Always maintain a professional tone."
        )

        user_prompt = (
            f"Context:\n{context}\n\n"
            f"Question:\n{query}\n\n"
            "Answer:"
        )

        response = self.client.chat(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0,  
        )

        return response.choices[0].message.content.strip()

    def generate_quiz(self, context: str, num_questions: int = 3) -> str:
        system_prompt = (
            "You are an AI Tutor creating a quiz to test a student's understanding of the provided notes.\n"
            "Return ONLY a raw JSON array of objects. Do not wrap it in markdown code blocks.\n"
            "Each object must have the following keys: \n"
            "   'question' (string), \n"
            "   'options' (array of 4 strings), \n"
            "   'correct_answer' (string, must exactly match one of the options), \n"
            "   'explanation' (string, briefly explaining why the answer is correct).\n"
        )
        user_prompt = f"Context Notes:\n{context}\n\nPlease generate a {num_questions}-question quiz based on these notes in the requested JSON format."

        response = self.client.chat(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"} if hasattr(self.client, "chat") else None # Try native json if supported
        )
        return response.choices[0].message.content.strip()

    def tutor_response(self, context: str, query: str) -> str:
        system_prompt = (
            "You are an encouraging, expert AI Tutor, like those at highly-rated learning platforms.\n"
            "Your goal is to help the student learn, not just give them the answer.\n"
            "1. ALWAYS explain concepts step-by-step.\n"
            "2. Use the Socratic method when appropriate to guide them.\n"
            "3. Use the provided context to inform your explanation.\n"
            "4. Format the response clearly using Markdown (bullet points, bold text for key terms).\n"
            "5. If the context doesn't have the exact answer, use your general knowledge but keep it relevant to the question."
        )

        user_prompt = (
            f"Reference Context:\n{context}\n\n"
            f"Student Question:\n{query}\n\n"
            "AI Tutor Explanation:"
        )

        response = self.client.chat(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )

        return response.choices[0].message.content.strip()
