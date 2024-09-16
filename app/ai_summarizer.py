import tiktoken
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from tqdm import tqdm
from typing import List, Tuple, Optional

model_4_o = "gpt-4o" 
model_3_5_turbo =  "gpt-3.5-turbo" # Cheaper but can handle less text.

# Need to find out 4o-mini's threshold (this isn't currently used anyway).
max_model_tokens = {model_3_5_turbo: 16385, model_4_o: 30339}

#system_prompt = "You are an animal shelter assistant that summarizes case files to improve animal care, and so the animals can be placed in adoptive homes. Tone should be honest but positive. Most entries in the files are dated, and summaries should highlight progress or changes over time."
titles_prompt = "This is a list of section titles from a shelter pet's history. Return a comma-separated list containing only the titles of sections that are 1) relevant to behavioral history or 2) likely to contain other info that should be provided to a potential adopter.\n{}"
section_summary_prompt = "Summarize this section from a case file for a shelter dog named {}. The section is titled {}. You don't need to restate the title in your response. {}"
file_summary_prompt = "Summarize this case file for a shelter dog named {}. {}"

# These sections are not interesting to summarize, even though the model often thinks they are.
always_exclude_sections = ["Matchmaker Summary", "Kennel Card / Web Site Memo"]

class AISummarizer: 
    def __init__(self, model, system_prompt):
        self.model = model
        self.client = OpenAI()
        self.system_prompt = system_prompt

    def summarize_file(self, text: str, name: str):
        return self.chat_completion(file_summary_prompt.format(name, text), temperature=0.2, max_tokens=750)

    def summarize_file_in_sections(self, text: dict, prompt: str, name: str):
        """
        Removes the part of the text starting from the specified substring.
        
        :param text: A dict of title->content mapping for each section of the file to summarize.
        :param prompt: The prompt to use for summaries.
        :param name: The name of the animal.
        :return: A dict of title->summary for the sections deemed relevant by the model.
        """
        summaries = {}
        titles = ', '.join(list(text.keys()))
        # Another way to do filter sections is to pass the whole section in and see if the AI thinks it is relevant,
        # but this is faster and cheaper.
        recommended_sections = self.chat_completion(titles_prompt.format(titles), temperature=0.2, max_tokens=200).split(', ')
        titles_to_summarize = [item for item in recommended_sections if item not in always_exclude_sections]

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.summarize_section, title, text[title], name): title for title in titles_to_summarize}
            for future in futures:
                title = futures[future]  # Get the title associated with this Future
                summary = future.result()  # Get the summary result
                summaries[title] = summary  # Add the summary to the dictionary
        return summaries

    def summarize_section(self, title, content, name):
        return self.chat_completion(section_summary_prompt.format(name, title, content), 0.2, 500)
            
    def chat_completion(self, user_prompt: str, temperature: float, max_tokens: int) -> str:
        """
        Sends a chat completion to OpenAI.

        :param system_prompt: the system prompt sets the overall behavior and tone.
        :param user_prompt: the user prompt contains the specific question.
        :param temperature: controls creativity and consistency of responses (lower = less creative, more consistent)
        :param max_tokens: controls the length of the response. If too low, may cause truncated responses.
        """
        response = self.client.chat.completions.create(
        model = self.model,
        messages=[
            {
                "role" : "system",
                "content" : self.system_prompt,
            },
            {
                "role" : "user",
                "content" : user_prompt,
            }
        ],
        max_tokens=max_tokens, 
        temperature = temperature,
        )
        return response.choices[0].message.content

    def tokenize(self, text) -> List[str]:
        encoding = tiktoken.encoding_for_model(self.model)
        encoded = encoding.encode(text)
        return encoded