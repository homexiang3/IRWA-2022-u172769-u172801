import os
from json import JSONEncoder

# pip install httpagentparser
import httpagentparser  # for getting the user agent as json
import nltk
from flask import Flask, render_template, session
from flask import request

from myapp.analytics.analytics_data import AnalyticsData, ClickedDoc
from myapp.search.load_corpus import load_corpus
from myapp.search.objects import Document, StatsDocument
from myapp.search.search_engine import SearchEngine


# *** for using method to_json in objects ***
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = JSONEncoder().default
JSONEncoder.default = _default

# end lines ***for using method to_json in objects ***

# instantiate the Flask application
app = Flask(__name__)

# random 'secret_key' is used for persisting data in secure cookie
app.secret_key = 'afgsreg86sr897b6st8b76va8er76fcs6g8d7'
# open browser dev tool to see the cookies
app.session_cookie_name = 'IRWA_SEARCH_ENGINE'

# instantiate our search engine
search_engine = SearchEngine()

# instantiate our in memory persistence
analytics_data = AnalyticsData()

# print("current dir", os.getcwd() + "\n")
# print("__file__", __file__ + "\n")
full_path = os.path.realpath(__file__)
path, filename = os.path.split(full_path)
# print(path + ' --> ' + filename + "\n")
# load documents corpus into memory.
file_path = path + "/tweets-data-who.json"

# file_path = "../../tweets-data-who.json"
corpus = load_corpus(file_path)
print("loaded corpus. first elem:", list(corpus.values())[0])

# create tf-idf index
# create tf-idf index
search_engine.create_index(corpus)


# Home URL "/"
@app.route('/')
def index():
    print("starting home url /...")

    # flask server creates a session by persisting a cookie in the user's browser.
    # the 'session' object keeps data between multiple requests
    session['some_var'] = "IRWA 2021 home"

    user_agent = request.headers.get('User-Agent')
    print("Raw user browser:", user_agent)

    user_ip = request.remote_addr
    agent = httpagentparser.detect(user_agent)

    print("Remote IP: {} - JSON user browser {}".format(user_ip, agent))

    print(session)
    
    #Get user agent information
    browser = "{} {}".format(agent['browser']['name'],agent['browser']['version'])
    os = "{} {}".format(agent['os']['name'],agent['os']['version'])

    # store data in statistics table 4
    analytics_data.increment_fact(browser,analytics_data.fact_browser)
    
    # store data in statistics table 5
    analytics_data.increment_fact(os,analytics_data.fact_os)
    
    # store data in statistics table 6
    analytics_data.add_timeactivity()

    return render_template('index.html', page_title="Welcome")


@app.route('/search', methods=['POST'])
def search_form_post():
    search_query = request.form['search-query']

    session['last_search_query'] = search_query

    search_id = analytics_data.save_query_terms(search_query)

    results = search_engine.search(search_query, search_id, corpus)

    found_count = len(results)
    session['last_found_count'] = found_count

    print(session)
    
    # store data in statistics table 2
    analytics_data.increment_fact(search_query,analytics_data.fact_queries)
    
    # store data in statistics table 6
    analytics_data.add_timeactivity()
    
    return render_template('results.html', results_list=results, page_title="Results", found_counter=found_count)


@app.route('/doc_details', methods=['GET'])
def doc_details():
    # getting request parameters:
    # user = request.args.get('user')

    print("doc details session: ")
    print(session)

    res = session["some_var"]

    print("recovered var from session:", res)

    # get the query string parameters from request
    clicked_doc_id = request.args["id"]
    p1 = int(request.args["search_id"])  # transform to Integer
    p2 = int(request.args["param2"])  # transform to Integer
    print("click in id={}".format(clicked_doc_id))

    # store data in statistics table 1
    analytics_data.increment_fact(clicked_doc_id,analytics_data.fact_clicks)
    # store data in statistics table 3
    analytics_data.increment_fact(session['last_search_query'],analytics_data.fact_click_queries)
    # store data in statistics table 6
    analytics_data.add_timeactivity()
    
    print("fact_clicks count for id={} is {}".format(clicked_doc_id, analytics_data.fact_clicks[clicked_doc_id]))
    
    ll = list(corpus.values())
    tweet = search_engine.find_tweet(ll,int(clicked_doc_id))
    tweet.url = "doc_details?id={}&search_id={}&param2=2".format(tweet.id, p1)
    return render_template('doc_details.html',tweet=tweet, page_title="doc_details")


@app.route('/stats', methods=['GET'])
def stats():
    """
    Show simple statistics example. ### Replace with dashboard ###
    :return:
    """
    # store data in statistics table 6
    analytics_data.add_timeactivity()
    docs = []
    # ### Start replace with your code ###

    for doc_id in analytics_data.fact_clicks:
        row: Document = corpus[int(doc_id)]
        count = analytics_data.fact_clicks[doc_id]
        doc = StatsDocument(row.id, row.title, row.description, row.doc_date, row.url, count)
        docs.append(doc)

    # simulate sort by ranking
    docs.sort(key=lambda doc: doc.count, reverse=True)
    return render_template('stats.html', clicks_data=docs)
    # ### End replace with your code ###


@app.route('/dashboard', methods=['GET'])
def dashboard():
    # store data in statistics table 6
    analytics_data.add_timeactivity()
    
    visited_docs = []
    print(analytics_data.fact_clicks.keys())
    for doc_id in analytics_data.fact_clicks.keys():
        d: Document = corpus[int(doc_id)]
        doc = ClickedDoc(doc_id, d.description, analytics_data.fact_clicks[doc_id])
        visited_docs.append(doc)

    # simulate sort by ranking
    visited_docs.sort(key=lambda doc: doc.counter, reverse=True)
    visited_ser=[]
    for doc in visited_docs:
        visited_ser.append(doc.to_json())
    #sort dictionaries
    sorted_browsers = sorted(analytics_data.fact_browser.items(), key=lambda kv:kv[1], reverse=True)
    sorted_browsers = dict(sorted_browsers)
    
    sorted_os = sorted(analytics_data.fact_os.items(), key=lambda kv:kv[1], reverse=True)
    sorted_os = dict(sorted_os)
    
    sorted_queries = sorted(analytics_data.fact_queries.items(), key=lambda kv:kv[1], reverse=True)
    sorted_queries = dict(sorted_queries)
    
    sorted_click_queries = sorted(analytics_data.fact_click_queries.items(), key=lambda kv:kv[1], reverse=True)
    sorted_click_queries = dict(sorted_click_queries)
    #print all fact tables
    
    print(sorted_queries)
    print(sorted_click_queries)
    print(sorted_browsers)
    print(sorted_os)
    print(analytics_data.fact_timeactivity)
    return render_template('dashboard.html', visited_docs=visited_ser, queries = sorted_queries, click_queries = sorted_click_queries,
    browsers = sorted_browsers, os = sorted_os, timeactivity = analytics_data.fact_timeactivity)


@app.route('/sentiment')
def sentiment_form():
    # store data in statistics table 6
    analytics_data.add_timeactivity()
    return render_template('sentiment.html')


@app.route('/sentiment', methods=['POST'])
def sentiment_form_post():
    # store data in statistics table 6
    analytics_data.add_timeactivity()
    text = request.form['text']
    nltk.download('vader_lexicon')
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    sid = SentimentIntensityAnalyzer()
    score = ((sid.polarity_scores(str(text)))['compound'])
    return render_template('sentiment.html', score=score)


if __name__ == "__main__":
    app.run(port=8088, host="0.0.0.0", threaded=False, debug=True)
