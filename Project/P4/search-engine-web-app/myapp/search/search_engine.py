import random
import pickle
from pathlib import Path

from myapp.search.objects import ResultItem, Document
from myapp.search.algorithms import create_tfidf_index, search_in_corpus


def build_demo_results(corpus: dict, search_id):
    """
    Helper method, just to demo the app
    :return: a list of demo docs sorted by ranking
    """
    res = []
    size = len(corpus)
    ll = list(corpus.values())
    for index in range(random.randint(0, 40)):
        item: Document = ll[random.randint(0, size)]
        res.append(ResultItem(item.id, item.title, item.description, item.doc_date,
                              "doc_details?id={}&search_id={}&param2=2".format(item.id, search_id), random.random()))

    # for index, item in enumerate(corpus['Id']):
    #     # DF columns: 'Id' 'Tweet' 'Username' 'Date' 'Hashtags' 'Likes' 'Retweets' 'Url' 'Language'
    #     res.append(DocumentInfo(item.Id, item.Tweet, item.Tweet, item.Date,
    #                             "doc_details?id={}&search_id={}&param2=2".format(item.Id, search_id), random.random()))

    # simulate sort by ranking
    res.sort(key=lambda doc: doc.ranking, reverse=True)
    return res


class SearchEngine:
    """educational search engine"""
    index = []
    tf = []
    df = []
    idf = []
    tweet_index = []
    
    def create_index(self,corpus):
    
        # Check if file dumps exists to avoid index creation each time we run the server
        DUMP_DIR = Path('./myapp/dump_files')
        DUMP_DIR.mkdir(parents=True, exist_ok=True)
        
        index_filepath =  DUMP_DIR / 'index.pk'
        tf_filepath =  DUMP_DIR / 'tf.pk'
        df_filepath =  DUMP_DIR / 'df.pk'
        idf_filepath =  DUMP_DIR / 'idf.pk'
        twindex_filepath = DUMP_DIR / 'tweet_index.pk'
        
        always_create = False # Set it False if you want to load from dump if the file exists or true if you want to create index always
        
        # Check if files exist to load data from cache or create a new tf-idf index and the new files
        if always_create == False and index_filepath.exists() and tf_filepath.exists() and df_filepath.exists() and idf_filepath.exists() and twindex_filepath.exists(): 
            print("Load data from cache!")
            self.index = pickle.load(index_filepath.open('rb'))
            self.tf = pickle.load(tf_filepath.open('rb'))
            self.df = pickle.load(df_filepath.open('rb'))
            self.idf = pickle.load(idf_filepath.open('rb'))
            self.tweet_index = pickle.load(twindex_filepath.open('rb'))
            print("Data loaded successfully!")
        else:
            print("Creating tf-idf index...")
            self.index, self.tf, self.df, self.idf, self.tweet_index = create_tfidf_index(corpus)
            print("Finishing index creation...")
            
            print("Creating file dumps...")
            with open(index_filepath, "wb") as f:
              pickle.dump(self.index, f)
              
            with open(tf_filepath, "wb") as f:
              pickle.dump(self.tf, f)
              
            with open(df_filepath, "wb") as f:
              pickle.dump(self.df, f)
              
            with open(idf_filepath, "wb") as f:
              pickle.dump(self.idf, f)
            
            with open(twindex_filepath, "wb") as f:
              pickle.dump(self.tweet_index, f)
              
            print("Finishing file dumps...")
   
      
    def search(self, search_query, search_id, corpus):
        print("Search query:", search_query)

        results = []
        ##### your code here #####
        #results = build_demo_results(corpus, search_id)  # replace with call to search algorithm

        ranked_docs , ranked_ranks = search_in_corpus(search_query, self.index, self.idf, self.tf)
        ##### Given the list of tweets id process to take entire tweets #####
        ll = list(corpus.values())
        rank_counter = 0
        for id in ranked_docs:
            item = self.find_tweet(ll,id)
            results.append(ResultItem(item.id, item.title, item.description, item.doc_date,
                              "doc_details?id={}&search_id={}&param2=2".format(item.id, search_id), ranked_ranks[rank_counter]))
            rank_counter = rank_counter + 1
            
        
        return results
        
    def find_tweet(self, ll, id):
        corpus_index = self.tweet_index[id]
        item: Document = ll[corpus_index]
        return item