# Twitter Map
## Tweet Sentiment Analysis
![alt tag](https://github.com/mramdass/Twitter_Map/blob/master/Screenshots/Zoom_Out.PNG)  
## Sypnosis
Web Application that allows users to search keywords from an AWS Elasticsearch Service powered by AWS Elastic Beanstalk. The Twitter Streaming API is used to send tweets to AWS SQS which is then handled by a worker that judges a tweet's sentiment or whether tweets are positive, negative, or neutral - this leverages IBM's Natural Language Understanding API. Once a sentiment is obtained, tweets are pushed to AWS SNS service which then are pushed to services that are interested in this topic. User may ask an HTTP/HTTPS, email, or SMS endpoint to subscribe to this AWS SNS topic. In this case, AWS Elasticsearch is the endpoint that is subscribed to the SNS topic. A web interface is provided to view tweets or filter them. Viewers may read the tweet and its corresponding sentiment by hovering over them on Google Map.  
![alt tag](https://github.com/mramdass/Twitter_Map/blob/master/Screenshots/Architecture.png)  
## Prerequisities
Refer to requirements.txt and creds.json.  
Twitter Developer Account  
Google API Key  
Amazon Web Services Account - With SQS, SNS, Elasticsearch and Beanstalk services running  
IBM Natural Language Understanding Account and API Key
Elastic Cloud Account (Optional)  
Python 2.7.11  
```
pip install -r requirements.txt
```
## Running
You may run either for local use or AWS Beanstalk.  
```
python application.py
python worker.py
python streamer.py
```
## Key
### Positive
Positive sentiments are indicated with green map pins. Hovering over a green pin will display its tweet content which includes text and time of the tweet.  
![alt tag](https://github.com/mramdass/Twitter_Map/blob/master/Screenshots/Positive_Green.png)  
### Negative
Negative sentiments are indicated with red map pins. Hovering over a red pin will display its tweet content which includes text and time of the tweet.  
![alt tag](https://github.com/mramdass/Twitter_Map/blob/master/Screenshots/Negative_Red.png)  
### Neutral
Neutral sentiments are indicated with blue map pins. Hovering over a blue pin will display its tweet content which includes text and time of the tweet.  
![alt tag](https://github.com/mramdass/Twitter_Map/blob/master/Screenshots/Neutral_Blue.png)  
## Closer View
![alt tag](https://github.com/mramdass/Twitter_Map/blob/master/Screenshots/Zoom_In.png) 
