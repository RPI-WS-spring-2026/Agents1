from groq import Groq
import pandas as pd
from pathlib import Path
import os
import datetime

def prepare_llama_prompt_dataframe(df, prompt_file, subs, model, print_prompt=False):
    # Load the prompt template
    file_path = Path(prompt_file)
    with open(file_path) as f:
        prompt = f.read()

    for index, row in df.iterrows():
        # Create a copy of the original prompt for each row
        prompt_temp = prompt

        # Substitute values in the text
        for sub in subs:
            prompt_temp = prompt_temp.replace(f'{{{sub}}}', str(row[sub]))
        if print_prompt:
            print(prompt_temp)

        # Add prompt and model information to the DataFrame
        df.loc[index, 'template'] = prompt_file
        df.loc[index, 'prompt'] = prompt_temp
        df.loc[index, 'model'] = model

    return df

def generate_llama_completions(client, prompts, model):
    completions = []
    for prompt in prompts:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )
        completion = chat_completion.choices[0].message.content
        completions.append(completion)

    return completions

def process_llama_responses(df, example_dict, save=True, directory=Path("../responses")):
    for index, row in df.iterrows():
        try:
            # Parse the completion text as a dictionary or JSON object
            completion_dict = eval(row['completion'])
            for key, value in example_dict.items():
                df.loc[index, key] = completion_dict.get(key, '')
        except (ValueError, TypeError):
            # Handle non-dictionary completion text
            print(f"Non-dictionary completion text at index {index}: {row['completion']}")
            for key in example_dict.keys():
                df.loc[index, key] = ''

    if save:
        current_datetime = datetime.datetime.now()
        filename = current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
        filepath = os.path.join(directory, filename)
        df.to_csv(filepath, index=False)

    return df