import json
import random
from datetime import datetime



class AnalyticsData:
    """
    An in memory persistence object.
    Declare more variables to hold analytics tables.
    """
    # statistics table 1
    # fact_clicks is a dictionary with the click counters: key = doc id | value = click counter
    fact_clicks = dict([])
    
    
    # statistics table 2
    # fact_queries is a dictionary with the queries counters: key = query | value = query counter
    fact_queries = dict([])

    # statistics table 3
     # fact_click_queries is a dictionary with the clicks counters within a query: key = query | value = query counter
    fact_click_queries = dict([])
    
    # statistics table 4
    # fact_browser is a dictionary with the browser counters: key = browser| value = browser counter
    fact_browser = dict([])
    
    # statistics table 5
    # fact_os is a dictionary with the os counters: key = os | value = os counter
    fact_os = dict([])
    
    # statistics table 6
    # fact_timeactivity is a dictionary with the number of events counters: key = time | value = event counter
    fact_timeactivity = dict([])
    
    def save_query_terms(self, terms: str) -> int:
        print(self)
        return random.randint(0, 100000)
    
    def increment_fact(self,var,fact):
        if var in fact.keys():
            fact[var] += 1
        else:
            fact[var] = 1
    def add_timeactivity(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M") #we decided to use only hours - minutes for simplicity
        self.increment_fact(current_time,self.fact_timeactivity)
        
class ClickedDoc:
    def __init__(self, doc_id, description, counter):
        self.doc_id = doc_id
        self.description = description
        self.counter = counter

    def to_json(self):
        return self.__dict__

    def __str__(self):
        """
        Print the object content as a JSON string
        """
        return json.dumps(self)


