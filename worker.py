#!/usr/bin/env python
try:
    import boto3, requests, json
    from time import sleep
    from multiprocessing import Pool
    from watson_developer_cloud import NaturalLanguageUnderstandingV1
    import watson_developer_cloud.natural_language_understanding.features.v1 as features
except ImportError as e:
    print e
    exit(1)

nlu_creds = None

sqs = boto3.resource('sqs')
sns = boto3.client('sns')
q = sqs.get_queue_by_name(QueueName='tweets')
sns_arn = None

def creds(name='creds.json'):
    global nlu_creds, sns_arn
    try:
        with open(name, 'r') as r:
            keys = json.load(r)
            nlu_creds = keys["natural_language_understanding"]
			sns_arn = keys["AWS_SNS_ARN"]
            r.close()
    except Exception as e:
        print e
        exit(1)

creds()

def worker():
    global q
    print 'Worker Initialized'
    attributes = ['id', 'text', 'time', 'lat', 'lon']
    while True:
        responses = q.receive_messages(MessageAttributeNames=attributes)
        if len(responses) != 0:
            for response in responses:
                if response.message_attributes is None:
                    response.delete()
                    continue
                id = response.message_attributes.get('id').get('StringValue')
                text = response.message_attributes.get('text').get('StringValue')
                time = response.message_attributes.get('time').get('StringValue')
                lat = response.message_attributes.get('lat').get('StringValue')
                lon = response.message_attributes.get('lon').get('StringValue')
                try:
                    natural_language_understanding = NaturalLanguageUnderstandingV1(\
                        version='2017-02-27',\
                        username=nlu_creds['username'],\
                        password=nlu_creds['password']\
                    )

                    nlu_response = natural_language_understanding.analyze(\
                        text=text,\
                        features=[features.Entities(), features.Keywords(), features.Sentiment()]\
                    )

                    sentiment = nlu_response['sentiment']['document']['label']
                except Exception as e:
                    print 'Error:', e
                    sentiment = 'neutral'

                # Send to AWS SNS
                notification = {
                    'id': id,
                    'text': text,
                    'time': time,
                    'lat': lat,
                    'lon': lon,
                    'sentiment': sentiment
                }
                try:
                    print notification
                    sns.publish(TargetArn=sns_arn, Message=json.dumps({'default': json.dumps(notification)}))
                    response.delete()
                except Exception as e:
                    print 'Error:', e
        sleep(2)

if __name__ == "__main__":
    print 'Running Worker'
    #p = Pool(4, worker, (q,))
    p = Pool(2, worker, ())
    #worker(q)
    while True: pass