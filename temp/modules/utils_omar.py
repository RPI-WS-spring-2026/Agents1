import yaml
import openai
import pandas as pd
from pathlib import Path
import os
import datetime



def load_yaml_file(file_path):
    
    try:
        with open(file_path, 'r') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except yaml.YAMLError as e:
        print(f"Error: Failed to load YAML from '{file_path}': {e}")
        return None


def get_completion(prompt, model="gpt-3.5-turbo", temperature=0, save=True):
    current_datetime = datetime.datetime.now()
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, # this is the degree of randomness of the model's output
    )
    textr = response.choices[0].message["content"] 
    directory = "../responses"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Generate the filename based on the current date and time
    filename = os.path.join(directory, current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".txt")

    with open(filename, "w") as file:
        file.write(textr)
    return response, textr
