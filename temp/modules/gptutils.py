import yaml
import openai
import pandas as pd
from pathlib import Path
import os
import datetime
import json
import requests



local_url = "http://localhost:1234/v1/chat/completions"
gpt_base = "https://api.openai.com"

current_datetime = datetime.datetime.now()

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




def call_v3(prompt, json_output=True, client=None,  model="local", temperature= 0.7, max_tokens=-1, save=True, directory = Path("../responses"), local_url=local_url, gpt_base=gpt_base, file_key=current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"):

    if json_output:
        context= "Always answer in a structure JSON document."
    else:
        context="You are a helpful assistant."
    
    if model=='local':
        url=local_url
    else:
        url=None    #I think the GPT URL involves a gpt_base and the model. 


    # Prepare the headers
    headers = {
        "Content-Type": "application/json",
    }

    data = {
        "messages": [
            {"role": "system", "content": context},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }

    print(data)
    # Perform the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))
    # Perform the POST request
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # Check if the request was successful
    if not response.ok:
    #    print(response.text)  # To print the response’s content
    #else:
        print("Request failed with status code:", response.status_code)
    
    textr=json.loads(response.text)['choices'][0]['message']['content']
    if not os.path.exists(directory):
        os.makedirs(directory)
  
    # Generate the filename based on the current date and time
    if save:
        #current_datetime = datetime.datetime.now()
        filename = file_key
        with open(filename, "w") as file:
            file.write(textr)
    
    return response.text, textr

def get_completion(client, messages, model="gpt-3.5-turbo", temperature=0, save=True, directory = Path("../responses")):
    

    #Make the call to OPENAI. 
    response = client.chat.completions.create(
        model=model,
        messages=messages)
    
    textr=response.choices[0].message.content
    
        
    if not os.path.exists(directory):
        os.makedirs(directory)
  
    # Generate the filename based on the current date and time
    if save:
        current_datetime = datetime.datetime.now()
        filename = os.path.join(directory, current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
        with open(filename, "w") as file:
            file.write(textr)

    return response,textr

def get_completion_json(client, messages, model="gpt-3.5-turbo", temperature=0, save=True, directory = Path("../responses")):
    #
    #Make the call to OPENAI. 
    response = client.chat.completions.create(
        model=model,
        response_format={ "type": "json_object" },
        messages=messages)
    textr=response.choices[0].message.content
    
    if not os.path.exists(directory):
        os.makedirs(directory)
  
    
    # Generate the filename based on the current date and time
    if save:
        current_datetime = datetime.datetime.now()
        filename=current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".txt"
        filename = os.path.join(directory, filename)
        with open(filename, "w") as file:
            file.write(textr)
    else:
        filename=None

    return response, textr, filename

def prepare_prompt_dataframe(df, prompt_file, subs, model, print_prompt=False):
    #This loads a prompt.
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
        #Add prompt and model to dataframe
        # Add prompt and model information to the DataFrame
        df.loc[index, 'template'] = prompt_file
        df.loc[index, 'prompt'] = prompt_temp
        df.loc[index, 'model'] = model
    return df


def run_df_openai(openaiclient, df, save=True):
    dftemp = df.copy()
    for index, row in dftemp.iterrows():
        messages = [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user", "content": row['prompt']},
        ]

        # Make sure to import or define the get_completion_json method
        responseall, response, file = get_completion_json(openaiclient, messages, save=save, model=row['model'])
        dftemp.loc[index, 'response'] = response
        #df.loc[index, 'responseall'] = responseall
        dftemp.loc[index, 'file'] = file

    if save:
        # Construct the full file path using os.path.join
        current_datetime = datetime.datetime.now()
        filename = current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
        filepath = os.path.join('..', 'responses', filename)
        dftemp.to_csv(filepath, index=False)

    return dftemp, response, responseall

def process_json(row, ex):
    for key, value in ex.items():
        data = json.loads(row['response'])
        # Extract the corresponding value from the nested JSON structure
        row[key] = data.get(key)

    return row