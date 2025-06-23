mcq_prompt = """
You are an expert question generator.

Given a context, your task is to generate a multiple-choice question in JSON format. 
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

Here are some examples:

Context:
The water cycle describes how water evaporates from the surface of the Earth, rises into the atmosphere, cools and condenses into rain or snow, and falls again to the surface as precipitation.

Output:
{
  "question": "What process in the water cycle is responsible for forming clouds?",
  "type": "mcq",
  "options": ["Evaporation", "Condensation", "Precipitation", "Infiltration"],
  "correct_answer": "Condensation",
  "explanation": "Condensation is the process where water vapor cools and changes into liquid droplets, forming clouds."
}

Context:
Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize food from carbon dioxide and water.

Output:
{
  "question": "What is the primary purpose of photosynthesis in plants?",
  "type": "mcq",
  "options": ["To absorb water", "To produce energy", "To synthesize food", "To release oxygen"],
  "correct_answer": "To synthesize food",
  "explanation": "Photosynthesis enables plants to make their own food using sunlight, carbon dioxide, and water."
}

Now, generate a question for the following context:
[Insert your context here]
"""
