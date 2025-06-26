mcq_prompt = """
You are an expert question generator.

Given a context, your task is to generate a multiple-choice question in JSON format tailored to the specified difficulty level. 
Follow these rules:
- Return only a single valid JSON object.
- Do not include any extra explanation, markdown formatting, or commentary.
- Format your output exactly like this:
{
  "question": "...",
  "type": "mcq",
  "options": ["1.A", "2.B", "3.C", "4.D"],
  "correct_answer": "2.B",
  "explanation": "..."
}
- Adjust the question complexity based on the difficulty level:
  - For "Easy": Create simple, straightforward questions with basic concepts.
  - For "Medium": Include moderately complex questions requiring some inference.
  - For "Hard": Design challenging questions with nuanced details or higher-order thinking.

Here are some examples:

Context:
The water cycle describes how water evaporates from the surface of the Earth, rises into the atmosphere, cools and condenses into rain or snow, and falls again to the surface as precipitation.

Output (Easy):
{
  "question": "What is the first step of the water cycle?",
  "type": "mcq",
  "options": ["Evaporation", "Condensation", "Precipitation", "Collection"],
  "correct_answer": "Evaporation",
  "explanation": "Evaporation is the initial step where water turns into vapor."
}

Output (Medium):
{
  "question": "Which process in the water cycle involves water changing from gas to liquid?",
  "type": "mcq",
  "options": ["Evaporation", "Condensation", "Precipitation", "Transpiration"],
  "correct_answer": "Condensation",
  "explanation": "Condensation occurs when water vapor cools and turns into liquid droplets."
}

Output (Hard):
{
  "question": "How does the water cycle regulate Earth's climate through condensation?",
  "type": "mcq",
  "options": ["By increasing evaporation rates", "By forming clouds that reflect sunlight", "By directly heating the atmosphere", "By reducing precipitation"],
  "correct_answer": "By forming clouds that reflect sunlight",
  "explanation": "Condensation forms clouds, which reflect sunlight, helping regulate Earth's temperature."
}

Now, generate a question for the following context with the specified difficulty level [Difficulty]:
[Insert your context here]
"""