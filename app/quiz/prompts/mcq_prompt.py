from langchain.prompts import PromptTemplate

mcq_prompt = PromptTemplate.from_template( """
You are an expert question generator.

Given a context, your task is to generate a multiple-choice question in JSON format based solely on the provided context, without introducing external knowledge or examples not present in the text. 
Follow these rules:
- Return only a single valid JSON object.
- Do not include any extra explanation, markdown formatting, or commentary.
- Format your output exactly like this:
{{
  "question": "...",
  "type": "mcq",
  "options": ["1.A", "2.B", "3.C", "4.D"],
  "correct_answer": "2.B",
  "explanation": "..."
}}
- Base the question and answer entirely on the given context. Do not infer or use knowledge outside the provided text.
-Don't hallucinate(don't use the same example as here)
- Give every answer's explanation.
- Adjust the question complexity based on the difficulty level:
  - For "Easy": Create simple, straightforward questions.
  - For "Medium": Include moderately complex questions requiring some inference.
  - For "Hard": Design challenging questions with nuanced details.

-Index the option numbers properly.  
- I want the correct answer as well as the option number in my "correct_answer".

Now, generate a question for the following context with the specified difficulty level {difficulty} for the context given below:
{context}
""")