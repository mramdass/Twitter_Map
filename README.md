# Twitter Map
## Sypnosis
Web Application that uses Amazon Web Services ElasticSearch Service and Amazon Web Services ElasticBeanstalk Service to generate a Google Map heatmap display of Tweets based on user input of keyword(s).
## Prerequisities
Twitter Developer Account  
Google API Key  
Amazon Web Services Account - With ElasticSearch and Beanstalk services running  
Elastic Cloud Account (Optional)  
Python 2.7.11  
```
pip install -r requirements.txt
```
## Running
You may run either for local use.  
Only application.py will run on AWS Beanstalk.
```
python driver.py -c creds.json -e <endpoint to AWS ElasticSearch Service>
python application.py
```
