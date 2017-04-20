#!/usr/bin/env python
try:
    import os, certifi, boto3
    from tweepy import OAuthHandler, API, TweepError, Stream
    from tweepy.streaming import StreamListener
    from json import load
except ImportError as ie:
    print ie
    exit(1)

# Twitter Credentials
consumer_access = None
consumer_secret = None
token_access = None
token_secret = None
twitter_api = None

# Some popular words in the time this script was written
WORDS = ['Trump', 'the', 'i', 'to', 'a', 'and', 'is', 'in', 'it', 'you']

def creds(name='creds.json'):
    global consumer_access, consumer_secret, token_access, token_secret, AWSAccessKeyId, AWSSecretKey,\
        elastic_cloud_endpoint, elastic_cloud_username, elastic_cloud_password
    try:
        with open(name, 'r') as r:
            keys = load(r)
            consumer_access         = keys["twitter_access_api_key"]
            consumer_secret         = keys["twitter_secret_api_key"]
            token_access            = keys["twitter_access_token"]
            token_secret            = keys["twitter_secret_token"]
            r.close()
    except Exception as e:
        print e
        exit(1)

creds()

sqs = boto3.resource('sqs')
q = sqs.create_queue(QueueName='tweets', Attributes={'DelaySeconds':'5'})

class StreamListener(StreamListener):
    def on_status(self, status):
        global q
        try:
            # Send status to AWS SQS
            if status.lang != 'en': return  # Filter by language: English
            lat = None
            lon = None
            if hasattr(status, 'coordinates') and status.coordinates:  # Filter by location
                lat = status.coordinates['coordinates'][1]
                lon = status.coordinates['coordinates'][0]
            elif hasattr(status, 'place') and status.place:
                lat = status.place.bounding_box.coordinates[0][0][1]
                lon = status.place.bounding_box.coordinates[0][0][0]
            elif  hasattr(status, 'retweeted_status') and hasattr(status.retweeted_status, 'place') and status.retweeted_status.place:
                lat = status.retweeted_status.place.bounding_box.coordinates[0][0][1]
                lon = status.retweeted_status.place.bounding_box.coordinates[0][0][0]
            elif hasattr(status, 'quoted_status') and hasattr(status.quoted_status, 'place') and status.quoted_status.place:
                lat = status.quoted_status.place.bounding_box.coordinates[0][0][1]
                lon = status.quoted_status.place.bounding_box.coordinates[0][0][0]
            else: return
            if lat and lon:  # Create tweet dictionary to send to AWS SQS and send it; if condition not necessary
                tweet = {
                    'id': {'DataType': 'Number', 'StringValue': str(status.id)},
                    'text': {'DataType': 'String', 'StringValue': str(status.text.encode("ascii", "ignore"))},
                    'time': {'DataType': 'String', 'StringValue': str(status.created_at)},
                    'lat': {'DataType': 'Number', 'StringValue': str(lat)},
                    'lon': {'DataType': 'Number', 'StringValue': str(lon)}
                }
                print tweet
                q.send_message(MessageBody="TwitterStreamingInformation", MessageAttributes=tweet)
        except Exception as e:
            print 'Error:', e
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
    except Exception as e: exit(1)

def run_stream_listener():
    sl = StreamListener()
    stream = Stream(auth=twitter_api.auth, listener=sl)
    stream.filter(track=WORDS, async=True)

if __name__ == "__main__":
    print 'Running Twitter Streamer'
    twitter_auth()
    run_stream_listener()