#!/usr/bin/env python
try:
    import os, certifi, boto3, urllib2
    from multiprocessing import Pool
    from aws_requests_auth.aws_auth import AWSRequestsAuth
    from requests_aws4auth import AWS4Auth, PassiveAWS4Auth
    from elasticsearch import Elasticsearch, RequestsHttpConnection, serializer, compat, exceptions
    from flask import Flask, render_template, abort, request, redirect,  jsonify
    from tweepy import OAuthHandler, API, TweepError, Stream
    from tweepy.streaming import StreamListener
    from json import load, loads, dumps
    from time import sleep
except ImportError as ie:
    print ie
    exit(1)

application = Flask(__name__)

google_api_key = None

# AWS ElasticSearch Credentials
AWSAccessKeyId = None
AWSSecretKey = None

# Elastic Cloud Credentials
elastic_cloud_endpoint = None
elastic_cloud_username = None
elastic_cloud_password = None

def creds(name='creds.json'):
    global google_api_key, AWSAccessKeyId, AWSSecretKey,\
        elastic_cloud_endpoint, elastic_cloud_username, elastic_cloud_password
    try:
        with open(name, 'r') as r:
            keys = load(r)
            google_api_key          = keys["google_maps_api_key"]
            AWSAccessKeyId          = keys["AWSAccessKeyId"]
            AWSSecretKey            = keys["AWSSecretKey"]
            elastic_cloud_endpoint  = keys["elastic_cloud_endpoint"]
            elastic_cloud_username  = keys["elastic_cloud_username"]
            elastic_cloud_password  = keys["elastic_cloud_password"]
            r.close()
    except Exception as e:
        print e
        exit(1)

creds()

# 1st Attribution: http://stackoverflow.com/questions/38209061/django-elasticsearch-aws-httplib-unicodedecodeerror/38371830
# 2nd Attribution: https://docs.python.org/2/library/json.html#basic-usage
class JSONSerializerPython2(serializer.JSONSerializer):
    def dumps(self, data):
        if isinstance(data, compat.string_types): return data
        try: return dumps(data, default=self.default, ensure_ascii=True)
        except (ValueError, TypeError) as e: raise exceptions.SerializationError(data, e)

es = Elasticsearch(
    [elastic_cloud_endpoint],
    port=9243,
    http_auth=elastic_cloud_username + ":" + elastic_cloud_password,
    serializer=JSONSerializerPython2(),
    ca_certs=certifi.where()
)

mapping = {
    "text": {
        "type": "string"
    },
    "location": {
        "type": "geo_point"
    },
    "time": {
        #"format": "EEE MMM dd HH:mm:ss Z YYYY",
        "format": "YYYY-MM-dd HH:mm:ss",
        "type": "date"
    },
    "sentiment": {
        "type": "string"
    },
    "lat": {
        "type": "float"
    },
    "lon": {
        "type": "float"
    },
    "id": {
        "type": "integer"
    }
}

#es.indices.delete(index='tweets', ignore=[400, 404])

es.indices.create(index='tweets', body=mapping, ignore=400)

@application.route('/')
def index():
    search = {'query': {'match_all': {}}, 'size': 2000}
    data = es.search(index='tweets', body=search)
    res = {}
    try:
        for hit in data['hits']['hits']:
            res[hit['_id']] = hit['_source']
    except Exception as e:
        print 'Error:', e
    return render_template('map.html', field=res)

@application.route('/keyword', methods=['GET', 'POST'])
def keyword():
    word = request.form['words']
    search = {'query': {'match_phrase': {'text': word}}, 'size': 2000}
    data = es.search(index='tweets', body=search)
    res = {}
    try:
        for hit in data['hits']['hits']:
            res[hit['_id']] = hit['_source']
    except Exception as e:
        print 'Error', e
    return render_template('map.html', field=res)

@application.route('/', methods=['GET', 'POST'])
def sns_es():
    print 'SNS to ES'
    try:
        if request.method != 'GET':
            request_json = request.get_json()
            body = loads(request.get_data())
            head = request.headers
            if 'Type' in body:
                if body['Type'] == 'Notification':
                    notification = loads(loads(body['Message']).get('default'))
                    print 'Notification:', notification
                    data = {
                        'id': int(notification.get('id')),
                        'sentiment': notification.get('sentiment'),
                        'text': notification.get('text'),
                        'lat': float(notification.get('lat')),
                        'lon': float(notification.get('lon')),
                        'time': notification.get('time'),
                        'location': {'lat': float(notification.get('lat')), 'lng': float(notification.get('lon'))}
                    }
                    es.index(index='tweets', doc_type='tweets', id=data['id'], body=data)
                elif body['Type'] == 'SubscriptionConfirmation':
                    print 'Got Subscription'
                    confirmed = urllib2.urlopen(body['SubscribeURL']).read()
                    print confirmed
                    print 'Subscribed'
    except Exception as e:
        print 'Error:', e


if __name__ == "__main__":
    application.run(debug=True)