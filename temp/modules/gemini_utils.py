import json
import os
import datetime
from pathlib import Path
import pandas as pd
import google.generativeai as genai
import yaml

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

def get_completion_json(client, messages, save=True, model="gemini-1.0-pro-latest", directory=Path("../responses")):
    # Convert messages to the format expected by the Gemini API
    contents = [{"text": message['content']} for message in messages]
    response = client.generate_content(contents[1]["text"])
    textr = response.text
    
    if not os.path.exists(directory):
        os.makedirs(directory)
  
    # Generate the filename based on the current date and time
    if save:
        current_datetime = datetime.datetime.now()
        filename = directory / (current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".txt")
        with open(filename, "w") as file:
            file.write(textr)
    else:
        filename = None

    return response, textr, filename

from pathlib import Path

def prepare_prompt_dataframe(df, prompt_file, subs, model, print_prompt=False, encoding='utf-8'):
    # This loads a prompt.
    file_path = Path(prompt_file)
    with open(file_path, encoding=encoding) as f:
        prompt = f.read()
    print(prompt)
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


def run_df_Geminipro(client, df, save=True):
    dftemp = df.copy()
    responses = []
    responsealls = []

    for index, row in dftemp.iterrows():
        messages = [
            {"role": "system", "content": "You are a helpful assistant designed to output JSON format"},
            {"role": "user", "content": row['prompt']}
        ]
        responseall, response, file = get_completion_json(client, messages, save=save, model=row['model'])
        dftemp.loc[index, 'response'] = response
        dftemp.loc[index, 'file'] = file
        responses.append(response)
        responsealls.append(responseall)

    if save:
        # Construct the full file path using os.path.join
        current_datetime = datetime.datetime.now()
        filename = current_datetime.strftime("%Y-%m-%d_%H-%M-%S") + ".csv"
        filepath = os.path.join('..', 'responses', filename)
        dftemp.to_csv(filepath, index=False)

    return dftemp, responses, responsealls


def process_json(row, ex):
    try:
        # Directly parse the JSON string
        data = json.loads(row)
    except json.JSONDecodeError as e:
        print(f"JSON decoding error for row: {row}, error: {e}")
        print(f"Invalid JSON: {row}")
        return {key: None for key in ex.keys()}
    
    # If JSON parsing is successful, proceed to extract values
    processed_row = {}
    for key in ex.keys():
        processed_row[key] = data.get(key, None)
    return processed_row


def main_run_models(selected_prompt_file, selected_model, mode, output_file, example):
    
    #### Define parameters
    prompt_files = {
        1: "../prompts/prompts_pivot_1.txt",
        2: "../prompts/prompts_pivot_2.txt",
        3: "../prompts/prompts_pivot_3.txt"
    }

    models = {
        1: "google-gemi",
        2: "openai-model"
    }

    # Load configuration data
    cf = load_yaml_file(Path('..', 'config', 'key.yaml'))
    
    # Choose model
    llm = models[selected_model]  # Use selected_model to choose the model
    if llm == 'google-gemi':
        GOOGLE_API_KEY = cf['google']
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash', generation_config={"response_mime_type": "application/json"})
    elif llm == 'openai-model':
        # Code to configure OpenAI model
        pass
    else:
        raise ValueError("Unsupported LLM specified")
    
    # Read data from an Excel file
    lpath = Path('../data')
    df = pd.read_excel(lpath / 'sample_200_quality.xlsx')
    df = df.iloc[:, 1:4]
    
    # Choose prompt file
    prompt_file = prompt_files[selected_prompt_file]  # Use selected_prompt_file to choose the prompt file
    
    # Prepare the prompt DataFrame
    substitute = ['key', '2018_description', '2023_description']
    df = prepare_prompt_dataframe(df, prompt_file, substitute, 'gemini-1.0-pro-latest', print_prompt=False)
    
    # Run the completion
    dftemp, response, responseall = run_df_Geminipro(model, df, save=True)
    print(responseall)
    
    print(">>>>>>>>>>>>>")
    
    print(dftemp.head())
    
    print(dftemp["response"][0])
    
    # Process the JSON responses
    dfnew2 = dftemp['response'].apply(lambda x: process_json(x, example))
    dfnew2 = pd.DataFrame(dfnew2.tolist())
    
    # Save the results
    dfnew2.to_csv(output_file, index=False)
    print('CSV saved to', output_file)