from quickstart import *
from gbt_scraper import *
import time
import copy

'''
	Written by Isabel Angelo, UCB,  Fall 2016
	Modified by Howard Isaacson, UCB, Fall 2016
	
	Purpose:  Automatically update the GBT calendar 
	
	Resources:
		Website describing google calendar API.
		https://developers.google.com/google-apps/calendar/quickstart/python
		Obtain .json file as described in above link.
		Change SCOPE from readonly to read/write
		
		Install:
		pip install apiclient
		pip install --upgrade google-api-python-client

	calendar:    u'summary': u'BL_Obs'		
'''

#get credentials and calendar list from Google Calendar
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)
page_token = None
BL_CAL = 'BL_Obs'  #Choose to update calendar with this name
while True:
  calendar_list = service.calendarList().list(pageToken=page_token).execute()
  for calendar_list_entry in calendar_list['items']: #hti
    print 'calendar name:',calendar_list_entry['summary'] #hti
    if calendar_list_entry['summary'] == BL_CAL:
      cal = calendar_list_entry# ['items']
      print 'credentials successful, calendar retrieved'
      break
  page_token = calendar_list.get('nextPageToken')
  if not page_token:
    break

#stores which google calendar to update
cal = calendar_list['items'][2] #1=index of BL google calendar in calendar list
#hti commented ths out.

#alternately set this up to find item in calendar_list called 'BL_Obs'

#scrape and store schedule from GBT website
scraper = GBTScraper(date=time.strftime("%m/%d/%Y"), days = 30) #store for next 30 days
scraper.make(t = 'utc')
#HTI combine events if end time of one is start time of next.
#if len(scraper.btlpSchedule) > 1:
#	for session in scraper.btlpSchedule:
#		session1 = session 
#		endtime = session2
#		
#hti end
events = scraper.btlpSchedule
#print events

def get_events(existing_events = [], existing_event_endtimes = []):
	'''
	get list of existing events on google calendar
	'eventlist: list stores information about each event on calendar
	returns: list containing start times of events on calendar '''
	now = datetime.datetime.utcnow() # 'Z' indicates UTC time
	then= datetime.datetime.utcnow()-datetime.timedelta(7)
	t = then.isoformat() + 'Z'
	eventsResult = service.events().list(
        calendarId=cal['id'], timeMin=t, maxResults=100, singleEvents=True,
        orderBy='startTime', timeZone = 'Etc/UTC').execute()
	events = eventsResult.get('items', [])

	if not events:
		print('No upcoming events found.')
	for event in events:
		start = event['start'].get('dateTime', event['start'].get('date'))
		end = event['end'].get('dateTime', event['start'].get('date'))
        existing_events.append(start)
        existing_event_endtimes.append(end)
        
        
def start_time(event):
	''' gets start time of an event scraped GBT events list'''
	e = event.start[:10]+'T'+event.start[11:]+':00Z'
	e = e.decode('unicode_escape')
	return e

def end_time(event):
	''' gets start time of an event scraped GBT events list '''
	e = event.end[:10]+'T'+event.end[11:]+':00Z'
	e = e.decode('unicode_escape')
	return e
        
    
def check_if_exists(event):
	''' check to see if an event from scraper is already on calendar
	returns True if exists, False if doesn't '''
	if start_time(event) in existing_events:
		print 'Event Exists'
		return True
	elif end_time(event) in existing_event_endtimes:
		print 'Event Exists'
		return True
	else:
		print 'Event Does Not Exist, Updating New Event'
		return False
    

def add_event(e):
	''' adds event to google calendar '''
	event_start = str(start_time(e))[:-1]
	event_end = str(end_time(e))[:-1]
	event = {
      'summary': 'GBT Observing '+ e.receivers +'band',
      'location': '',
      'description': '',
      'start': {
        'dateTime': event_start,
        'timeZone': 'Etc/UTC',
      },
      'end': {
        'dateTime': event_end,
        'timeZone': 'Etc/UTC',
      },
      'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=1'
      ],
    }
	event = service.events().insert(calendarId=cal['id'], body=event).execute()
	print 'Event created: %s' % (event.get('htmlLink'))
	print 'begin: ',event_start
	print 'end:   ',event_end 

def write_to_database(event):
	'''writes the event date, time, timezone and duration to database
 	gbt_observations_database.txt '''
	s = start_time(event)
	a = time.strptime(str(start_time(event)), '%Y-%m-%dT%H:%M:%SZ')
	b = time.strptime(str(end_time(event)), '%Y-%m-%dT%H:%M:%SZ')
	
	a = time.mktime(a)
	b = time.mktime(b)
	
	d = b - a
	
	days = int(d) / 86400
	hours = str(int(d) / 3600 % 24)
	minutes = str(int(d) / 60 % 60)
	seconds = str(int(d) % 60)
	
	duration = hours + 'h' + minutes + 'm' + seconds + 's'
	entry =  s[:10]+ '\t' + s[11:-1] + '\t' + 'UTC' + '\t' + duration + '\n'
	
	with open('gbt_observations_database.txt', 'a') as file:
		file.write(entry)
	print 'database updated'




#get list of existing events from Google Calendar
existing_events = []
existing_event_endtimes = []
get_events(existing_events, existing_event_endtimes)
print existing_events
print existing_event_endtimes


#iterate over GBT events, checks if they are on the calendar, and adds if not
# Check to see if events are consecutive
print ''
print 'Checking for back to back events...'

unq_events = []

for i in range(len(events)):
	print 'Event ',i,':',
	event = events[i]
	#Reset back2back for each event
	back2back = False
	for other_event in events:
		#this if statement extends first two events
		if event.end == other_event.start:
			print 'Back to back detected, events merged' 
			back2back = True
			unq_events.append(copy.copy(event))
			unq_events[-1].end = other_event.end
		# Removes 2nd of two events
		elif event.start == other_event.end:
			back2back = True
			print 'Back to back detected, removing 2nd of back to back events'
	# Allow single events to be added
	if back2back == False:
		unq_events.append(event)
		print 'Adding in single event'

print 'Total Unique Events:', len(unq_events)

print ''
print 'Checking if events exist...'

for i in range(len(unq_events)):
	print 'Unique Event',i,':',
	event = unq_events[i]
	if check_if_exists(event) == False:
		add_event(event)
		write_to_database(event)

		
