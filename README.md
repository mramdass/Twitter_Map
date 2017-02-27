# Twitter Map
## Sypnosis
Web Application that uses Amazon Web Services ElasticSearch Service and Amazon Web Services ElasticBeanstalk Service to generate a Google Map heatmap display of Tweets based on user input of keyword(s).
## Prerequisities
Twitter Developer Account  
Google API Key  
Amazon Web Services Account - With ElasticSearch and Beanstalk services running  
Python 2.7.11  
```
pip install elasticsearch-py
pip install flask
pip install tweepy
pip install requests-aws4auth
```
## Running
```
python driver.py -c creds.json -e <endpoint to AWS ElasticSearch Service>
```
## References
