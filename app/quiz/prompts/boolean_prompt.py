boolean_prompt = """
You are an expert question generator.

Given a context, your task is to generate a Boolean question in JSON format. 
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

Here are some examples:

Context:
The water cycle describes how water evaporates from the surface of the Earth, rises into the atmosphere, cools and condenses into rain or snow, and falls again to the surface as precipitation.

Output:
{
  "question": "Does the water cycle involve the process of evaporation?",
  "type": "boolean",
  "options": [],
  "correct_answer": "True",
  "explanation": "Evaporation is a key process in the water cycle where water turns into vapor and rises into the atmosphere."
}

Context:
Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize food from carbon dioxide and water.

Output:
{
  "question": "Is photosynthesis a process used by animals to produce food?",
  "type": "boolean",
  "options": [],
  "correct_answer": "False",
  "explanation": "Photosynthesis is primarily used by green plants and some organisms, not animals, to produce food using sunlight."
}

Now, generate a question for the following context:
[Insert your context here]
"""
