## PACKAGE IMPORT
import nltk
nltk.download('stopwords')
nltk.download('punkt')
from collections import defaultdict
from array import array
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import collections
import re
stemmer = nltk.stem.SnowballStemmer('english')
stopwords = set(stopwords.words('english'))
import math
import numpy as np
from numpy import linalg as la

## PREPROCESS STEPS

# Remove white spaces
def remove_white_space(text):
    return ' '.join(text.split())
    
# Remove stopwords
def remove_stopwords(words):
    return [w for w in words if w.lower() not in stopwords]
    
# Remove emojis
def remove_emojis(data):
    emoj = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002500-\U00002BEF"  # chinese char
        u"\U00002702-\U000027B0"
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001f926-\U0001f937"
        u"\U00010000-\U0010ffff"
        u"\u2640-\u2642" 
        u"\u2600-\u2B55"
        u"\u200d"
        u"\u23cf"
        u"\u23e9"
        u"\u231a"
        u"\ufe0f"  # dingbats
        u"\u3030"
                      "]+", re.UNICODE)
    return emoj.sub(r'', data)
    
# Remove punctuation and hashtags
def remove_punctuation(data):
    return re.sub(r'[^\w\s]', '', data)
    
# Remove numbers
def remove_numbers(data):
    return re.sub(r'[0-9]', '', data)
    
# Remove https
def remove_https(words):
  return [w for w in words if not w.startswith("https") ]

# Preprocess text
def preprocess(text):
    text = text.replace('\\n', '')
    text = remove_emojis(text)
    text = remove_punctuation(text)
    text = remove_numbers(text)
    text = remove_white_space(text)
    words = nltk.tokenize.word_tokenize(text)
    words = [stemmer.stem(word) for word in words]
    words = remove_stopwords(words)
    words = remove_https(words)
    return words

## INDEX CREATION

def create_tfidf_index(corpus):

    index = defaultdict(list)
    tf = defaultdict(list)  # term frequencies of terms in documents (documents in the same order as in the main index)
    df = defaultdict(int)  # document frequencies of terms in the corpus
    idf = defaultdict(float) # inverse document frequency for each term
    num_tweets = len(corpus) # number of tweets in corpus
    tweet_index = defaultdict(int) # dictionary to map tweet id with index in tweets list
    counter = 0 # keep track of index inside tweets
    
    for i in range(num_tweets):  # for all tweets
    
        tweet_id = list(corpus.values())[i].id #get id of each tweet
        tweet_text = list(corpus.values())[i].description #get text of each tweet
        terms = preprocess(tweet_text) #preprocess tweet and return list of terms
        
        tweet_index[tweet_id] = counter # Save original tweets position with tweet id to recover all the information
        counter = counter + 1 # Move to next tweets position
        
        current_page_index = {}
        
        for position, term in enumerate(terms):  
            try:
                # if the term is already in the dict append the position to the corresponding list
                current_page_index[term][1].append(position) 
            except:
                # Add the new term as dict key and initialize the array of positions and add the position
                current_page_index[term] = [tweet_id, array('I', [position])]  #'I' indicates unsigned int (int in Python)

        # normalize term frequencies
        # Compute the denominator to normalize term frequencies (formula 2 above)
        # norm is the same for all terms of a document.
        norm = 0
        for term, posting in current_page_index.items():
            # posting will contain the list of positions for current term in current document. 
            # posting ==> [current_doc, [list of positions]] 
            # you can use it to infer the frequency of current term.
            norm += len(posting[1]) ** 2
        norm = math.sqrt(norm)

        #calculate the tf(dividing the term frequency by the above computed norm) and df weights
        for term, posting in current_page_index.items():
            # append the tf for current term (tf = term frequency in current doc/norm)
            tf[term].append(np.round(len(posting[1]) / norm, 4)) ## SEE formula (1) above
            #increment the document frequency of current term (number of documents containing the current term)
            df[term] += 1 # increment DF for current term
            
        # Compute IDF
        for term in df:
            idf[term] = np.round(np.log(float(num_tweets/ df[term])), 4)

        #merge the current page index with the main index
        for term_page, posting_page in current_page_index.items():
            index[term_page].append(posting_page)

    return index, tf, df, idf, tweet_index

## RANK DOCUMENTS
def rank_documents(terms, docs, index, idf, tf):
    # I'm interested only on the element of the docVector corresponding to the query terms 
    # The remaining elements would became 0 when multiplied to the query_vector
    doc_vectors = defaultdict(lambda: [0] * len(terms)) # I call doc_vectors[k] for a nonexistent key k, the key-value pair (k,[0]*len(terms)) will be automatically added to the dictionary
    query_vector = [0] * len(terms)

    # compute the norm for the query tf
    query_terms_count = collections.Counter(terms)  # get the frequency of each term in the query. 

    query_norm = la.norm(list(query_terms_count.values()))

    for termIndex, term in enumerate(terms):  #termIndex is the index of the term in the query
        if term not in index:
            continue
        # query_vector[termIndex]=idf[term]  # original
        ## Compute tf*idf(normalize TF as done with documents)

        query_vector[termIndex]=query_terms_count[term]/query_norm * idf[term]

        # Generate doc_vectors for matching docs
        for doc_index, (doc, postings) in enumerate(index[term]):          
            if doc in docs:
                doc_vectors[doc][termIndex] = tf[term][doc_index] * idf[term]  

    # Calculate the score of each doc 
    # compute the cosine similarity between queyVector and each docVector:
    
    doc_scores = [[np.dot(curDocVec, query_vector), doc] for doc, curDocVec in doc_vectors.items()]
    doc_scores.sort(reverse=True)
    result_docs = [x[1] for x in doc_scores]
    result_ranks = [x[0] for x in doc_scores] #get rank value
    #print document titles instead if document id's
    if len(result_docs) == 0:
        print("No results found, try again")
    return result_docs, result_ranks
  
## SEARCH DOCUMENTS
def search_in_corpus(query, index, idf, tf):
    query = preprocess(query)#create list of query terms (each term is preprocessed to match terms in index)
    docs = set()
    for term in query:
        try:
            # store in term_docs the ids of the docs that contain "term"                        
            term_docs = [posting[0] for posting in index[term]]
            
            # docs = docs Union term_docs
            docs |= set(term_docs)
        except:
            #term is not in index
            pass
    docs = list(docs)
    ranked_docs, ranked_ranks = rank_documents(query, docs, index, idf, tf)#rank docs
    return ranked_docs, ranked_ranks
