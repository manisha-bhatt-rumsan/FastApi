faq_prompt = """
You are an expert question generator.

Given a context, your task is to generate a free-answer question in JSON format. 
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

Here are some examples:

Context:
The water cycle describes how water evaporates from the surface of the Earth, rises into the atmosphere, cools and condenses into rain or snow, and falls again to the surface as precipitation.

Output:
{
  "question": "Describe the process that causes water to form clouds in the water cycle.",
  "type": "faq",
  "options": [],
  "correct_answer": "Condensation is the process where water vapor cools and turns into liquid droplets, forming clouds.",
  "explanation": "Condensation occurs when water vapor in the atmosphere cools and transforms into liquid, leading to cloud formation."
}

Context:
Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize food from carbon dioxide and water.

Output:
{
  "question": "Explain the role of sunlight in photosynthesis.",
  "type": "faq",
  "options": [],
  "correct_answer": "Sunlight provides the energy needed to drive the chemical reactions that combine carbon dioxide and water to produce food.",
  "explanation": "Sunlight is absorbed by chlorophyll in plants, providing the energy to convert carbon dioxide and water into glucose and oxygen."
}

Now, generate a question for the following context:
[Insert your context here]
"""

