from quickstart import *
from gbt_scraper import *
import time

#get credentials and calendar list from Google Calendar
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
service = discovery.build('calendar', 'v3', http=http)
page_token = None
while True:
  calendar_list = service.calendarList().list(pageToken=page_token).execute()
  page_token = calendar_list.get('nextPageToken')
  if not page_token:
    break

#stores which google calendar to update
cal = calendar_list['items'][1]

#scrape and store schedule from GBT website
scraper = GBTScraper(date=time.strftime("%m/%d/%Y"), days = 30) 
scraper.make()
events = scraper.btlpSchedule

def get_events(existing_events = []): #for some reason leaves out first event
#	get list of existing events on google calendar
#	eventlist: list stores information about each event on calendar
#	returns: list containing start times of events on calendar
#    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    now = datetime.datetime.utcnow() # 'Z' indicates UTC time
    then= datetime.datetime.utcnow()-datetime.timedelta(7)
    t = then.isoformat() + 'Z'
    eventsResult = service.events().list(
        calendarId=cal['id'], timeMin=t, maxResults=100, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        existing_events.append(start)
        
def start_time(event):
# gets start time of an event scraped GBT events list
    return event.start[:10]+'T'+event.start[11:]+':00-07:00'

def end_time(event):
# adds event to google calendar 
    return event.end[:10]+'T'+event.end[11:]+':00-07:00'
        
    
def check_if_exists(event):
# check to see if an event from scraper is already on calendar
#	returns True if exists, False if doesn't
	if str(start_time(event)) in existing_events:
		return True
	else:
		return False
    

def add_event(e1, e2): 
# adds event to google calendar 
    date_start = e1.start[:10]
    time_start = e1.start[11:]+':00-07:00'
    date_end = e2.end[:10]
    time_end = e2.end[11:]+':00-07:00'
    
    event_start = date_start + 'T' + time_start
    event_end = date_end + 'T' + time_end
    
    event = {
      'summary': 'GBT Observing '+ e1.receivers +'band',
      'location': '',
      'description': '',
      'start': {
        'dateTime': event_start,
        'timeZone': 'America/Los_Angeles',
      },
      'end': {
        'dateTime': event_end,
        'timeZone': 'America/Los_Angeles',
      },
      'recurrence': [
        'RRULE:FREQ=DAILY;COUNT=1'
      ],
    }

    event = service.events().insert(calendarId=cal['id'], body=event).execute()
    print 'Event created: %s' % (event.get('htmlLink'))
    

#get list of existing events from Google Calendar
existing_events = []
get_events(existing_events)


#this next part iterates over GBT events, checks if they are on the calendar, and adds if not
#special command for first event since the loop doesn't work there for some reason
# if end_time(events[0]) in existing_events == False: #to account for it not working for first event
#     add_event(events[0])
# for event in events[1:]:
#     if check_if_exists(event) == False:
#         add_event(event)

if end_time(events[0]) in existing_events == False: #to account for it not working for first event
    add_event(events[0])
for i in range(len(events[1:])):
    if check_if_exists(events[i]) == False:
        if i >= 1 and start_time(events[i]) == end_time(events[i-1]):
            None
        elif len(events) > i+1 and end_time(events[i]) != start_time(events[i+1]):
            add_event(events[i], events[i])
            print 'added 1'
        elif len(events) > i+1 and (end_time(events[i]) == start_time(events[i+1])) :
            if len(events) > i+2 and end_time(events[i+1]) == start_time(events[i+2]) :
                add_event(events[i], events[i+2])
                print 'added 2'
            else:
                add_event(events[i], events[i+1])
                print 'added 3'