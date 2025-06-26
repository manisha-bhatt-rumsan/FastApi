faq_prompt = """
You are an expert question generator.

Given a context, your task is to generate a free-answer question in JSON format tailored to the specified difficulty level. 
Follow these rules:
- Return only a single valid JSON object.
- Do not include any extra explanation, markdown formatting, or commentary.
- Format your output exactly like this:
{
  "question": "...",
  "type": "faq",
  "options": [],
  "correct_answer": "...",
  "explanation": "..."
}
- Adjust the question complexity based on the difficulty level:
  - For "Easy": Create simple, straightforward questions with basic recall.
  - For "Medium": Include questions requiring some analysis or elaboration.
  - For "Hard": Design questions demanding deep understanding or detailed explanation.

Here are some examples:

Context:
The water cycle describes how water evaporates from the surface of the Earth, rises into the atmosphere, cools and condenses into rain or snow, and falls again to the surface as precipitation.

Output (Easy):
{
  "question": "What is the first step of the water cycle?",
  "type": "faq",
  "options": [],
  "correct_answer": "Evaporation",
  "explanation": "Evaporation is the initial step where water turns into vapor from the Earth's surface."
}

Output (Medium):
{
  "question": "Explain how water changes state during the water cycle.",
  "type": "faq",
  "options": [],
  "correct_answer": "Water changes from liquid to vapor during evaporation, vapor to liquid during condensation, and liquid to solid or back to liquid during precipitation.",
  "explanation": "The water cycle involves phase changes driven by heat and cooling, affecting water's state throughout the process."
}

Output (Hard):
{
  "question": "Describe the impact of the water cycle on global weather patterns.",
  "type": "faq",
  "options": [],
  "correct_answer": "The water cycle influences global weather by distributing heat through evaporation and condensation, forming clouds that lead to precipitation, and regulating temperature via ocean currents and atmospheric moisture.",
  "explanation": "The cycle's evaporation and condensation processes drive weather systems, impacting precipitation and climate stability worldwide."
}

Now, generate a question for the following context with the specified difficulty level [Difficulty]:
[Insert your context here]
"""