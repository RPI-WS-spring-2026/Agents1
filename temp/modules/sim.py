from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
import torch
import numpy as np
import pandas as pd
from numpy import dot
from numpy.linalg import norm
import simv2tf
import tensorflow_text as tf
import os

def test(x):
    return x


#If you need alternate ways of vectorizing texts.
#https://github.com/SeverinoCenter/similarity/blob/main/modules/simv2tf.py

def text_to_vector_old(text, vector):
    embeddings=None
    if vector =='complex':
        print("Transforming complex.")
        embeddings=simv2tf.complex_sentence_transformers(text)

    if vector =='bert2':
        print("Transforming bert model.")
        embeddings=simv2tf.embed_bert2(text)

    if vector =='univ2':
        print("Transforming universal sentence.")
        embeddings=simv2tf.embed_univ2(text)
    
    if vector =='t5':
        print("Transforming t5 model.")
        embeddings=simv2tf.embed_t5(text)
    
    if  vector=='mpnet':
        print("Transforming mpnet model.")
        embeddings=simv2tf.embed_mpnet(text)
    
    if vector =='roberta':
        print("Transforming roberta model.")
        embeddings=simv2tf.embed_roberta(text)
    
    if vector =='distilbert':
        print("Transforming distilbert model.")
        embeddings=simv2tf.embed_distilbert(text)
    
    if vector=='sentbert':
        print("Transforming sentence bert model.")
        embeddings=simv2tf.embed_sentbert(text)
    
    if vector=='parabert':
        print("Transforming paraphrase bert model.")
        embeddings=simv2tf.embed_parabert(text)
    
    if vector =='paradrob':
        print("Transforming paraphrase distilroberta model.")
        embeddings=simv2tf.embed_paradrob(text)

    if vector =='parafb':
        print("Transforming paraphrase facebook model.")
        embeddings=simv2tf.embed_parafb(text)

    if vector==['sentence']:
        embeddings=simv2tf.huggingface_transformer(text,'sentence-transformers/sentence-t5-base')
    
    if embeddings is None:
        print("No embeddings found.")
        return None
    return embeddings



def text_to_vector(text_series, model_name='distilbert-base-uncased'):
    # Load pre-trained model and tokenizer
    model = AutoModel.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.eval()

    def vectorize_text(text):
        # Tokenize input text
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        
        # Get embeddings from the last hidden layer of the model
        with torch.no_grad():
            outputs = model(**inputs)
        
        # outputs[0] contains the hidden states for each token in all input sequences
        # We take the mean to get a single vector representation for the input sequence
        #This can be different for different models. 
        embeddings = outputs[0].mean(1).cpu().numpy()

        return embeddings

    # Apply the function to the pandas series
    return text_series.apply(vectorize_text)

def compute_cosine_similarity(dftemp, X, Y, model, save=False, save_path=None,batch=None):
    # Get vector embeddings for both series
    
    X_emb=  text_to_vector_old(dftemp[X], model)
    Y_emb=  text_to_vector_old(dftemp[Y], model)

    #X_emb=np.vstack( X_emb)
    #Y_emb=np.vstack( Y_emb)
    
    #fullpath=save_path/'embeddings'

    # Compute cosine similarity for each pair of vectors in X and Y
    cs = cosine_similarity(np.vstack( X_emb), np.vstack( Y_emb)).diagonal()  #this is going to cause memory issues.
    if save:
        fullpath=save_path/'embeddings'
        dftemp.reset_index(drop=True, inplace=True)
        #check to see if the path exists.
        if not os.path.exists(fullpath):
            # If it doesn't exist, create it
            print("creating diretory: {}".format(fullpath))
            os.makedirs(fullpath)
        dftemp['cs']=cs
        dftemp[X+'_emb']=None
        dftemp[Y+'_emb']=None
        assert len(dftemp)==len(X_emb)
        assert len(dftemp)==len(Y_emb)
        dftemp[X+'_emb']= X_emb
        dftemp[Y+'_emb']= Y_emb
        print("Saving embeddings", len(dftemp), dftemp[X+'_emb'].isna().sum(),dftemp[Y+'_emb'].isna().sum()) 
        fp=fullpath/'embeddings_{}.pkl'.format(batch)
        dftemp.to_pickle(fp)


    return cs#,  X_emb, dftemp

# def compute_cosine_similarity_embeddings(X_embeddings, Y_embeddings):
#     # Get vector embeddings for both series

#     # Compute cosine similarity for each pair of vectors in X and Y
#     cosine_similarities = cosine_similarity(X_embeddings, Y_embeddings).diagonal()
#     cosine_similarities_manual=dftemp.apply(lambda x: cosine_similarity_manual(x['texta'], x['textb']), axis=1)
#     return cosine_similarities

# #def compute_cosine_similiarty_batch(df, key, texta, textb, model_name='distilbert-base-uncased', batch_size=10):
    
#     total = len(df)
#     batches = total // batch_size + (total % batch_size != 0)
#     print("Found {} batches.".format(batches))

#     cosine_similarities = []
#     #for i in tqdm(range(batches), desc="Processing batches"):
#     ret_df=pd.DataFrame()
#     ret_df['key']=df[key]
#     ret_df['texta']=df[texta]
#     ret_df['textb']=df[textb]
#     ret_df['cosine_similarity']=None
#     result=[]
#     for i in range(batches):
#         start = i * batch_size
#         if batches ==i+1:
#             end = total
#         else:
#             end = ((i+1)* batch_size)
#         temp_texta = df[texta][start:end]
#         temp_textb = df[textb][start:end]
#         ret_df['cosine_similarity'][start:end]=compute_cosine_similarity(temp_texta, temp_textb, model_name)

#         print("Processing Batch {} of {}, Start: {}, End: {}".format(i+1, batches, start, end))

#     return ret_df


def compute_cosine_similiarty_batch(df, key, texta, textb, model_name='distilbert-base-uncased', batch_size=10, save_embeddings=False, basepath=None):
    
    total = len(df)
    batches = total // batch_size + (total % batch_size != 0)
    print("Found {} batches.".format(batches))

    cosine_similarities = []
    #for i in tqdm(range(batches), desc="Processing batches"):
    ret_df=pd.DataFrame()
    ret_df['key']=df[key]
    ret_df[texta]=df[texta]
    ret_df[textb]=df[textb]
    ret_df['cosine_similarity']=None
    #ret_df[texta+'_emb']=None
    #ret_df[textb+'_emb']=None
    result=[]
    for i in range(batches):
        start = i * batch_size
        if batches ==i+1:
            end = total
        else:
            end = ((i+1)* batch_size)
        temp_texta = df[texta][start:end]
        temp_textb = df[textb][start:end]
        temp_key= df[key][start:end]
        dftemp=pd.DataFrame()
        dftemp[key]=temp_key
        dftemp[texta]=temp_texta
        dftemp[textb]=temp_textb

        if save_embeddings:
            ret_df['cosine_similarity'][start:end]=compute_cosine_similarity(dftemp, texta, textb, model_name, save_embeddings, basepath, i)
        else:
            ret_df['cosine_similarity'][start:end]=compute_cosine_similarity(dftemp, texta, textb, model_name)
      
    
        print("Processing Batch {} of {}, Start: {}, End: {}".format(i+1, batches, start, end))

    return ret_df




def cosine_similarity_manual(a, b):
    return dot(a, b)/(norm(a)*norm(b))