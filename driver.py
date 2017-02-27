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
    import requests
    from gmplot import GoogleMapPlotter
    #from aws_requests_auth.aws_auth import AWSRequestsAuth
    from requests_aws4auth import AWS4Auth
    from elasticsearch import Elasticsearch, RequestsHttpConnection, serializer, compat, exceptions
    from flask import Flask, render_template, abort, request, redirect
    from tweepy import OAuthHandler, API, TweepError, Stream
    from tweepy.streaming import StreamListener
    from json import load, loads, dump, dumps
    from argparse import ArgumentParser
    from string import printable
except Exception as e: print e

consumer_access = None
consumer_secret = None
token_access = None
token_secret = None
twitter_api = None

google_api_key = None

AWSAccessKeyId = None
AWSSecretKey = None
endpoint = None
es_client = None

app = Flask(__name__)

def creds(name):
    global consumer_access, consumer_secret, token_access, token_secret, google_api_key,\
    AWSAccessKeyId, AWSSecretKey

    with open('creds.json', 'r') as r:
        keys = load(r)
        consumer_access = keys["twitter_access_api_key"]
        consumer_secret = keys["twitter_secret_api_key"]
        token_access = keys["twitter_access_token"]
        token_secret = keys["twitter_secret_token"]
        google_api_key = keys["google_maps_api_key"]
        AWSAccessKeyId = keys["AWSAccessKeyId"]
        AWSSecretKey = keys["AWSSecretKey"]
        r.close()

def insert_script(string):
    script = '<script async defer src="https://maps.googleapis.com/maps/api/js?key='\
            + google_api_key + '&libraries=visualization&callback=initMap"></script>'
    if script in string: return string
    strings = string.split('</body>')
    return strings[0] + script + '\n</body>' + strings[1]

def insert_coordinates(string):
    new_html = ''
    with open('templates/map.html', 'r') as r:
        for line in r:
            if 'new google.maps.LatLng(' not in line:
                new_html += line
    with open('templates/map.html', 'w') as w:
        strings = new_html.split('// SPLIT POINT')
        new_html = strings[0] + '// SPLIT POINT\n' + string + strings[1]
        new_html = insert_script(new_html)
        w.write(new_html)

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

def AWS_auth():
    global es_client
    try:
        auth = AWS4Auth(AWSAccessKeyId, AWSSecretKey, 'us-east-1', 'es')
        response = requests.get('https://' + endpoint, auth=auth)
        print response.content

        es_client = Elasticsearch(
            hosts=[{'host': endpoint, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            serializer=JSONSerializerPython2()
        )
        print es_client.info()
        mapping = loads(open('twitter_mapping.json', 'r').read())
        es_client.indices.create(index="index_twitter",\
                                 ignore=400,\
                                 body=mapping)
    except Exception as e:
        print e


# TWITTER FUNCTIONS

class StreamListener(StreamListener):
    def on_status(self, status):
        if hasattr(status, 'retweeted_status') or status.coordinates == None:
            return
        try:
            if status.coordinates['type'] == 'Point':
                print status.user.screen_name
                es_client.index(index="index_twitter",\
                                doc_type="tweets",\
                                id=status._json['id'],\
                                body=status._json)

        except Exception as e: print e
        return True

    def on_error(self, status_code):
        if status_code == 420:
            print status_code
            return False


def twitter_auth():
    global twitter_api
    try:
        auth = OAuthHandler(consumer_access, consumer_secret)
        auth.set_access_token(token_access, token_secret)
        twitter_api = API(auth)
    except Exception as e: print e

def run_stream_listener():
    sl = StreamListener()
    stream = Stream(auth=twitter_api.auth, listener=sl)
    print 'Running Twitter Stream Listener'
    stream.filter(track=['Trump'], async=True)
    print 'Twitter Stream Listener active async'

# RUNNING APPLICATION LOGIC

@app.route('/')
def index(): return render_template('index.html')

@app.route('/keyword', methods=['POST'])
def keyword():
    word = request.form['words']
    print 'Querying AWS ElasticSeach Service for:', word
    data = es_client.search(index="index_twitter",\
                            body={"query": {"match": {"text": word}}})
    with open('search_output.json', 'w') as w:
        w.write(dumps(data, indent=4))

    string = 'new google.maps.LatLng(37.782551, -122.445368),\n\
              new google.maps.LatLng(37.782745, -122.444586),\n\
              new google.maps.LatLng(37.782842, -122.443688),\n\
              new google.maps.LatLng(37.782919, -122.442815),\n\
              new google.maps.LatLng(37.782992, -122.442112)'

    insert_coordinates(string)

    return render_template('map.html')

# MAIN

def main():
    global endpoint
    parser = ArgumentParser()
    parser.add_argument('-c', '--credentials', \
                        help='Path to credentials JSON file', \
                        required=True)
    parser.add_argument('-e', '--endpoint', \
                        help='AWS ElasticSearch endpoint', \
                        required=True)
    args = parser.parse_args()
    endpoint = args.endpoint
    creds(args.credentials)
    twitter_auth()
    AWS_auth()
    run_stream_listener()
    app.run(debug=True)

if __name__ == "__main__":
    main()
