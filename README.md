# RedSoxReport

###### Boston: home to the Red Sox, Celtics, Bruins, and the New England Patriots

Winning trophies is nice, but the commute...not so much

I designed a web scraper to search and aggregate Fenway Park event info, run on AWS Lambda.\
Lambda function calls are triggered daily (@ 9am EST) through AWS Cloudwatch Events.\
Amazon SES is used to send emails, notifying recipients of Fenway Park events occuring later that day.
