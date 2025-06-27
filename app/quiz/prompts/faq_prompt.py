from langchain.prompts import PromptTemplate

faq_prompt = PromptTemplate.from_template( """
You are an expert question generator.

Given a context, your task is to generate a free-answer question in JSON format based solely on the provided context, without introducing external knowledge or examples not present in the text. 
Follow these rules:
- Return only a single valid JSON object.
- Do not include any extra explanation, markdown formatting, or commentary.
- Format your output exactly like this:
{{
  "question": "...",
  "type": "faq",
  "options": [],
  "correct_answer": "...",
  "explanation": "..."
}}
- Base the question and answer entirely on the given context. Do not infer or use knowledge outside the provided text.
-Don't hallucinate(don't use the same example as here)
- Give every answer's explanation.
- Adjust the question complexity based on the difficulty level:
  - For "Easy": Create simple, recall-based questions.
  - For "Medium": Include questions requiring some analysis.
  - For "Hard": Design questions demanding detailed explanation.

Now, generate a question for the following context with the specified difficulty level {difficulty} for the context provided below:
{context}
""")