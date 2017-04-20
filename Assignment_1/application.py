#!/usr/bin/env python2.7
'''
    Munieshwar (Kevin) Ramdass
    Professor Sambit Sahu
    CS-GY 9223 - Cloud Computing
    26 February 2017

    Assignment 1 - Twitter Map

    Services Used:
        Google API
        Twitter API
        AWS ElasticSearch Service
'''

try:
    import os#, certifi
    #from gmplot import GoogleMapPlotter
    from aws_requests_auth.aws_auth import AWSRequestsAuth
    #from requests_aws4auth import AWS4Auth, PassiveAWS4Auth
    from elasticsearch import Elasticsearch, RequestsHttpConnection, serializer, compat, exceptions
    from flask import Flask, render_template, abort, request, redirect
    from tweepy import OAuthHandler, API, TweepError, Stream
    from tweepy.streaming import StreamListener
    from json import load, loads, dump, dumps
    from argparse import ArgumentParser
    from string import printable
except Exception as e: exit(1)

# Elastic Cloud Option - These two are not used
elastic_user = None
elastic_password = None

consumer_access = None
consumer_secret = None
token_access = None
token_secret = None
twitter_api = None

google_api_key = None

AWSAccessKeyId = None
AWSSecretKey = None

endpoint = '*******************************************************.us-east-1.es.amazonaws.com'
es_client = None

application = Flask(__name__)

# Define a few popular words to Rate Limit Twitter API requests
WORDS = ['Trump', 'the', 'i', 'to', 'a', 'and', 'is', 'in', 'it', 'you']

def creds(name):
    global consumer_access, consumer_secret, token_access, token_secret, google_api_key,\
    AWSAccessKeyId, AWSSecretKey, elastic_user, elastic_password

    with open('creds.json', 'r') as r:
        keys = load(r)
        consumer_access = keys["twitter_access_api_key"]
        consumer_secret = keys["twitter_secret_api_key"]
        token_access = keys["twitter_access_token"]
        token_secret = keys["twitter_secret_token"]
        google_api_key = keys["google_maps_api_key"]
        AWSAccessKeyId = keys["AWSAccessKeyId"]
        AWSSecretKey = keys["AWSSecretKey"]
        elastic_user = keys["elastic_cloud_user"]
        elastic_password = keys["elastic_cloud_password"]
        r.close()

# Manually entering API Key for testing purposes
def insert_script(string):
    script = '<script async defer src="https://maps.googleapis.com/maps/api/js?key='\
            + google_api_key + '&libraries=visualization&callback=initMap"></script>'
    if script in string: return string
    strings = string.split('</body>')
    return strings[0] + script + '\n</body>' + strings[1]

# Manually entering Coordinates for testing purposes
def insert_coordinates(string, map_page):
    for root, dirs, files in os.walk("templates"):
        for f in files:
            if f == map_page: return
        if len(files) > 15:
            for f in files:
                if f not in ['index.html', 'map.html']:
                    os.remove(os.path.join(root, f))

    new_html = ''
    with open('templates/map.html', 'r') as r:
        for line in r:
            if 'new google.maps.LatLng(' not in line:
                new_html += line
    with open('templates/' + map_page, 'w') as w:
        strings = new_html.split('// SPLIT POINT')
        new_html = strings[0] + '// SPLIT POINT\n' + string + strings[1]
        new_html = insert_script(new_html)
        w.write(new_html)

# Manually entering Coordinates for testing purposes
def format_coordinates(hits):
    string = ''
    for hit in hits["hits"]["hits"]:
        string += 'new google.maps.LatLng(' + str(hit['_source']['coordinates']['coordinates'][1])\
                  + ',' + str(hit['_source']['coordinates']['coordinates'][0]) + '),\n'
    return string[:-1]

# AWS FUNCTIONS

# Attribution: http://stackoverflow.com/questions/38209061/django-elasticsearch-aws-httplib-unicodedecodeerror/38371830
class JSONSerializerPython2(serializer.JSONSerializer):
    """
    Second Attribution: https://docs.python.org/2/library/json.html#basic-usage
    """
    def dumps(self, data):
        if isinstance(data, compat.string_types): return data
        try: return dumps(data, default=self.default, ensure_ascii=True)
        except (ValueError, TypeError) as e: raise exceptions.SerializationError(data, e)


# TWITTER FUNCTIONS

class StreamListener(StreamListener):
    def on_status(self, status):
        global es_client
        if hasattr(status, 'retweeted_status') or status.coordinates == None:
            return
        try:
            if status.coordinates['type'] == 'Point':
                es_client.index(index="index_twitter",\
                                doc_type="tweets",\
                                id=status._json['id'],\
                                body=status._json)

        except Exception as e: pass
        return True

    def on_error(self, status_code):
        if status_code == 420:
            print(status_code)
            return False


def twitter_auth():
    global twitter_api
    try:
        auth = OAuthHandler(consumer_access, consumer_secret)
        auth.set_access_token(token_access, token_secret)
        twitter_api = API(auth)
    except Exception as e: exit(1)

def run_stream_listener():
    sl = StreamListener()
    stream = Stream(auth=twitter_api.auth, listener=sl)
    stream.filter(track=WORDS, async=True)

# RUNNING APPLICATION LOGIC

@application.route('/')
def index(): return render_template('index.html')

@application.route('/keyword', methods=['POST'])
def keyword():
    global es_client
    try:
        word = request.form['words']
        data = es_client.search(index="index_twitter",\
                                body={"query": {"match": {"text": word}}})
        insert_coordinates(format_coordinates(data), 'map_' + word + '.html')
        return render_template('map_' + word + '.html')
    except: return render_template('map.html')

# MAIN

if __name__ == "__main__":
    creds('creds.json')

    twitter_auth()
    
    #es_client = Elasticsearch(
    #    ["https://********************************.us-east-1.aws.found.io"],
    #    #port=9243,
    #    443,
    #    http_auth=elastic_user + ":" + elastic_password,
    #    serializer=JSONSerializerPython2()#,
    #    #ca_certs=certifi.where()
    #)
    

    auth = AWSRequestsAuth(aws_access_key=AWSAccessKeyId,
                           aws_secret_access_key=AWSSecretKey,
                           aws_host=endpoint,
                           aws_region='us-east-1',
                           aws_service='es')

    #auth = AWS4Auth(AWSAccessKeyId, AWSSecretKey, 'us-east-1', 'es')

    #es_client = Elasticsearch(host=endpoint,
    #                          port=80,
    #                          connection_class=RequestsHttpConnection,
    #                          http_auth=auth,
    #                          serializer=JSONSerializerPython2())


    es_client = Elasticsearch(
        hosts=[{'host': endpoint, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        serializer=JSONSerializerPython2()
    )


    print(es_client.info())
    mapping = loads(open('twitter_mapping.json', 'r').read())
    es_client.indices.create(index="index_twitter", \
                             ignore=400, \
                             body=mapping)
    
    run_stream_listener()
    application.run(debug=True)
