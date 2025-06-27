from langchain.prompts import PromptTemplate

boolean_prompt = PromptTemplate.from_template( """
You are an expert question generator.

Given a context, your task is to generate a Boolean question in JSON format based solely on the provided context, without introducing external knowledge or examples not present in the text. 
Follow these rules:
- Return only a single valid JSON object.
- Do not include any extra explanation, markdown formatting, or commentary.
- Format your output exactly like this:
{{
  "question": "...",
  "type": "boolean",
  "options": [],
  "correct_answer": "True" or "False",
  "explanation": "..."
}}
- Base the question and answer entirely on the given context. Do not infer or use knowledge outside the provided text.
-Don't hallucinate(don't use the same example as here)
- Give every answer's explanation.
- Adjust the question complexity based on the difficulty level:
  - For "Easy": Create simple, factual True/False questions.
  - For "Medium": Include questions requiring basic inference from the context.
  - For "Hard": Design questions involving nuanced judgment based solely on the context.
Now, generate a question for the following context with the specified difficulty level {difficulty}:
{context}
"""
)