import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text as text

#from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np
#import spacy
#import sentence_transformers
#from sentence_transformers import SentenceTransformer, models
#from torch import nn
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer

import pandas as pd
import numpy as np
import torch


UNIVERSAL = "https://tfhub.dev/google/universal-sentence-encoder/4"
#@title Configure the model { run: "auto" }
BERT_MODEL = "https://tfhub.dev/google/experts/bert/wiki_books/2" #
# Preprocessing must match the model, but all the above use the same.
BERT_PREPROCESS_MODEL = "https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3"
MODULE_SENT = "https://tfhub.dev/google/universal-sentence-encoder/4" #@param ["https://tfhub.dev/google/universal-sentence-encoder/4", "https://tfhub.dev/google/universal-sentence-encoder-large/5"]

# pretrained T5 https://huggingface.co/sentence-transformers/sentence-t5-base
T5 = SentenceTransformer('sentence-t5-base')

# pretrained MPNET https://huggingface.co/sentence-transformers/all-mpnet-base-v2
MPNET = SentenceTransformer('sentence-transformers/nli-mpnet-base-v2')

# pretrained ROBERTA https://huggingface.co/sentence-transformers/nli-roberta-base-v2
ROBERTA = SentenceTransformer('sentence-transformers/nli-roberta-base-v2')

# pretrained DISTILBERT from QUORA https://huggingface.co/sentence-transformers/quora-distilbert-base
DISTILBERT = SentenceTransformer('sentence-transformers/nli-distilbert-base')#('sentence-transformers/quora-distilbert-base')

# pretrained SENTENCE BERT https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2
SENTBERT = SentenceTransformer('all-MiniLM-L12-v2')

# pretrained PARAPHRASE SENTENCE BERT https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L6-v2
PARABERT = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L6-v2')

# pretrained PARAPHRASE DISTILROBERTA https://huggingface.co/sentence-transformers/paraphrase-distilroberta-base-v2
PARADROB = SentenceTransformer('sentence-transformers/paraphrase-distilroberta-base-v2')

# pretrained PARAPHRASE DISTILROBERTA https://huggingface.co/sentence-transformers/paraphrase-distilroberta-base-v2
PARAFB = SentenceTransformer('sentence-transformers/facebook-dpr-question_encoder-single-nq-base')

#https://www.sbert.net/docs/training/overview.html?highlight=dense#creating-networks-from-scratch
#This creates a sentence embbedding limited at a specific length.
# def complex_transformers(text, model='bert-base-cased', complexity=256, sp_lib='en_core_web_md'):
#     tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
#     text=text.apply(tokenizer)
#     word_embedding_model = BertModel.from_pretrained('bert-base-uncased',output_hidden_states = True,)
#     pooling_model = sentence_transformers.models.Pooling(word_embedding_model.get_word_embedding_dimension())
#     dense_model = sentence_transformers.models.Dense(in_features=pooling_model.get_sentence_embedding_dimension(), out_features=complexity, activation_function=nn.Tanh())
#     model = sentence_transformers.SentenceTransformer(modules=[word_embedding_model, pooling_model,dense_model])
#     return pd.Series(model.encode(text).tolist())


def embed_univ(df,column):
    encoder_lib_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
    embed = hub.load(encoder_lib_url) # current encoder as at May 20th, 2021 - url "https://tfhub.dev/google/universal-sentence-encoder/4"
    message_embeddings = embed(df[column])
    df[column+'_universal'] = pd.Series(np.array(message_embeddings).tolist())
    return df


def embed_univ2(text,model=UNIVERSAL):
    model = hub.load(model) # current encoder as at May 20th, 2021 - url "https://tfh
    message_embeddings = model(text)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_t5(text,model=T5):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_roberta(text,model=ROBERTA):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_mpnet(text,model=MPNET):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_distilbert(text,model=DISTILBERT):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_sentbert(text,model=SENTBERT):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_parabert(text,model=PARABERT):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_paradrob(text,model=PARADROB):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_parafb(text,model=PARAFB):
    message_embeddings = model.encode(text.values)
    return pd.Series(np.array(message_embeddings).tolist())

def embed_transformer(tokenizer, model, text):
    encoded_input=tokenizer(text,padding="max_length", truncation=True, return_tensors='tf')
    output = model(encoded_input)
    tvec=pd.Series(output.last_hidden_state[:, -1].numpy().tolist())
    assert len(text)==len(tvec)
    return tvec

def embed(input):
    return model(input)

def embed_bert(df, column):
    preprocess = hub.load(PREPROCESS_MODEL)
    bert = hub.load(BERT_MODEL)
    inputs = preprocess(df[column])
    outputs = bert(inputs)
    df[column+'_bert']=pd.Series(np.array(outputs["pooled_output"]).tolist())
    return df

def embed_bert2(text, model=BERT_MODEL,preprocess=BERT_PREPROCESS_MODEL):
    pre_model = hub.load(preprocess)
    text=pre_model(text)
    model = hub.load(model)
    outputs = model(text)
    return pd.Series(outputs["pooled_output"].numpy().tolist())



def sentence_tokenizer(text,nlp):
    tokens = nlp(text)
    return [sent.string.strip() for sent in tokens.sents]

def preprocess_function(examples):
    return tokenizer(examples["text"], truncation=True)

#def complex_transformers(text, model='bert-base-cased', complexity=256, sp_lib='en_core_web_md'):
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    text=text.apply(tokenizer, truncation=True)
    word_embedding_model = transformers.models.Transformer('bert-base-uncased',max_seq_length=256)
    pooling_model = transformers.models.Pooling(word_embedding_model.get_word_embedding_dimension())
    dense_model = transformers.models.Dense(in_features=pooling_model.get_sentence_embedding_dimension(), out_features=256, activation_function=nn.Tanh())
    model = transformers.Transformer(modules=[word_embedding_model, pooling_model,dense_model])

    #return pd.Series(model.encode(text).tolist())

#https://huggingface.co/sentence-transformers/sentence-t5-base
#This is added new.
from sentence_transformers import SentenceTransformer
import sentence_transformers
def huggingface_transformer(text,modelname):
    model = SentenceTransformer(modelname)
    outputs = model.encode(text)
    return pd.Series(outputs.tolist())

def complex_sentence_transformers(text, model='bert-base-cased', complexity=256, sp_lib='en_core_web_md'):
    #This isn't working.
    #nlp = spacy.load(sp_lib)
    #text=text.apply(sentence_tokenizer,nlp=nlp)
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-cased")
    text=text.apply(tokenizer, truncation=True)
    word_embedding_model = sentence_transformers.models.Transformer('bert-base-uncased')
    pooling_model = sentence_transformers.models.Pooling(word_embedding_model.get_word_embedding_dimension())
    dense_model = sentence_transformers.models.Dense(in_features=pooling_model.get_sentence_embedding_dimension(), out_features=complexity, activation_function=nn.Tanh())
    model = sentence_transformers.SentenceTransformer(modules=[word_embedding_model, pooling_model,dense_model])
    return model.encode(text.values)
    #return pd.Series(mymodel.encode(text).tolist())
