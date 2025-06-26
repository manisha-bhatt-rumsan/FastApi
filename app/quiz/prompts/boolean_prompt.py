boolean_prompt = """
You are an expert question generator.

Given a context, your task is to generate a Boolean question in JSON format tailored to the specified difficulty level. 
Follow these rules:
- Return only a single valid JSON object.
- Do not include any extra explanation, markdown formatting, or commentary.
- Format your output exactly like this:
{
  "question": "...",
  "type": "boolean",
  "options": [],
  "correct_answer": "True" or "False",
  "explanation": "..."
}
- Adjust the question complexity based on the difficulty level:
  - For "Easy": Create simple, factual True/False questions with basic concepts.
  - For "Medium": Include questions requiring some understanding or inference.
  - For "Hard": Design questions involving nuanced judgment or complex scenarios.

Here are some examples:

Context:
The water cycle describes how water evaporates from the surface of the Earth, rises into the atmosphere, cools and condenses into rain or snow, and falls again to the surface as precipitation.

Output (Easy):
{
  "question": "Does water evaporate in the water cycle?",
  "type": "boolean",
  "options": [],
  "correct_answer": "True",
  "explanation": "Evaporation is a fundamental process in the water cycle."
}

Output (Medium):
{
  "question": "Is condensation the process that causes rain to fall in the water cycle?",
  "type": "boolean",
  "options": [],
  "correct_answer": "False",
  "explanation": "Condensation forms clouds, but precipitation is the process that causes rain to fall."
}

Output (Hard):
{
  "question": "Does the water cycle significantly influence global climate patterns through evaporation alone?",
  "type": "boolean",
  "options": [],
  "correct_answer": "False",
  "explanation": "While evaporation contributes, the water cycle's impact on climate involves multiple processes, including condensation and precipitation."
}

Now, generate a question for the following context with the specified difficulty level [Difficulty]:
[Insert your context here]
"""