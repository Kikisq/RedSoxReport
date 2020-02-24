import datetime
import requests
import json
from bs4 import BeautifulSoup
import boto3
from botocore.exceptions import ClientError


class EventInfo:
	def __init__(self, dateTime, eventTitle, eventURL):
		'''
		Initializes an EventInfo object

		dateTime (string): the Event's "datetime_local"
		eventTitle (string): the Event's "title"
		eventURL (string): the Event's "url"

		an EventInfo object has three attributes:
			self.dateTime (string, ex: "2020-04-02T14:05:00")
			self.eventTitle (string, ex: "[Team] at Boston Red Sox")
			self.eventURL (string, ex: "https://www.eseats.com/production/1751401/chicago_white_sox_at_boston_red_sox_tickets.html")
		'''
		self.dateTime = dateTime
		self.eventTitle = eventTitle
		self.eventURL = "https://www.eseats.com" + eventURL


def getTodayEvent():
	'''
	Parses URL for Events
	Creates a Dict of Event Dates:EventInfo pairs

	Returns: an EventInfo object

	Can modify method to take in specific Date
	'''
	# Fenway Park Events Page URL
	URL = "https://www.eseats.com/venue/fenway_park_tickets.html"

	# Get Today's Date
	# YYYY-MM-DD
	todayDate = datetime.date.today()

	# Get Fenway Park Events Page
	page = requests.get(URL)
	# Parse Page source and filter down to Events portion
	soup = BeautifulSoup(page.content.decode("utf-8"), "html.parser")
	eventSearch = soup.find_all("script")[2].string

	# Isolate JSON and convert to dict
	esReqJSON = eventSearch[21:-2]
	esReqDict = json.loads(esReqJSON)
	# Filter down to Event list
	eventSchedule = esReqDict["data"]["data"]

	# Make a Dict for the Month's Event Dates
	# Key = Event's Date
	# Values = EventInfo
	fenwayEventDates = {}
	for event in eventSchedule:
		fenwayEventDates[event["datetime_local"][0:10]] = EventInfo(event["datetime_local"], event["title"], event["url"])

	# Assign Today's Event instance
	#todayDate = "2020-04-02" needed for testing
	eventFound = fenwayEventDates.get(todayDate)

	# If no Event Info is found for Today, eventFound == None
	return eventFound


def sendEmail(eventInfoObject):
	'''
	Sends an Email using info from EventInfo object

	eventInfoObject (EventInfo): object containing Event info
	'''
	eventTime = eventInfoObject.dateTime[11:16]
	eventTitle = eventInfoObject.eventTitle
	eventURL = eventInfoObject.eventURL

	# Replace sender@example.com with your "From" address.
	# This address must be verified with Amazon SES.
	SENDER = "Sender Name <sender@email.com>"

	# Replace recipient@example.com with a "To" address. If your account
	# is still in the sandbox, this address must be verified.
	RECIPIENT = ["recipient@email.com"]

	# Specify a configuration set. If you do not want to use a configuration
	# set, comment the following variable, and the
	# ConfigurationSetName=CONFIGURATION_SET argument below.
	# CONFIGURATION_SET = "ConfigSet"

	# If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
	AWS_REGION = "us-east-1"

	# The subject line for the email.
	SUBJECT = eventTitle + " @ " + eventTime + "!"

	# The email body for recipients with non-HTML email clients.
	BODY_TEXT = (eventTitle + "@" + eventTime + "!\r\n"
	             "Uh-Oh! There's a game today!\r\n"
	             )

	# The HTML body of the email.
	BODY_HTML = """
		<html>
		<head></head>
		<body>
			<h1>Uh-Oh! There's a game today! &#x1F62A;</h1>
			<p>{eventTitle} @ {eventTime}!</p>
			<p>{eventURL}</p>
		</body>
		</html>
				"""

	bodyHTML = BODY_HTML.format(eventTitle = eventTitle, eventTime = eventTime, eventURL = eventURL)

	# The character encoding for the email.
	CHARSET = "UTF-8"

	# Create a new SES resource and specify a region.
	client = boto3.client('ses', region_name=AWS_REGION)

	# Try to send the email.
	try:
		# Provide the contents of the email.
		response = client.send_email(
			Destination={
				'ToAddresses': RECIPIENT,
			},
			Message={
				'Body': {
					'Html': {
						'Charset': CHARSET,
						'Data': bodyHTML,
					},
					'Text': {
						'Charset': CHARSET,
						'Data': BODY_TEXT,
					},
				},
				'Subject': {
					'Charset': CHARSET,
					'Data': SUBJECT,
				},
			},
			Source=SENDER
			# If you are not using a configuration set, comment or delete the
			# following line
			# ConfigurationSetName=CONFIGURATION_SET,
		)
	# Display an error if something goes wrong.
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		print("Email sent! Message ID:"),
		print(response['MessageId'])


def lambda_handler(event, context):
	'''
	event: AWS lambda_handler event
	context: AWS lambda_handler context

	Returns: None, if no Event found
	Otherwise, Email sent with relevant Event info
	'''
	# Assign EventInfo instance
	eventFound = getTodayEvent()

	# If Event found, send Email
	if (eventFound is not None):
		sendEmail(eventFound)
	else:
		return None