"""
Data Scraping Tool for GBT.
Pragaash Ponnusamy, 2016.


Usage:
	- Run from command line:
		
		python gbt_scraper.py date=02/11/2106 days=5
	
		Note: The date and days arguments are optional i.e. you could specify either of them or
			  both or neither but they require their formats to be date=MM/DD/YYYY and days=X
			  respectively.

	- Import as Python Library:

		>>> from gbt_scraper import *

		>>> scraper = GBTScraper(date='02/11/2016',days=5)

			Note: The date and days arguments are optional. Their default values are None and 5
				  respectively.

		>>> scaper.next()  			... Shows the first entry from the date specified ...
		>>> scaper.view(limit=n)	... Shows the first n or all (when limit is omitted) entries ...


In both cases, when the date and/or days are not specified, the current local time (PST) is used
to collect data in UTC format.

"""

import urllib2
import calendar,time,re,sys
from bs4 import BeautifulSoup

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

class BLISPEntry():

	def __init__(self,record):
		self.start,self.end = record['start-time'],record['end-time']
		self.type,self.receivers = record['type'],record['rcvrs']
		self.friend,self.pi = record['friend'],record['pi']
		self.freq = record['freq-ghz']

	def __repr__(self):
		return 'START:\t\t'+self.start+'\n'+'END:\t\t'+self.end+'\n'+\
			   'TYPE:\t\t'+self.type+'\n'+'RECEIVERS:\t'+self.receivers+'\n'+\
			   'FREQ (GHz):\t'+self.freq+'\n'+'PI:\t\t'+self.pi+'\n'+\
			   'FRIEND:\t\t'+self.friend

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

class GBTScraper():

	def __init__(self,date=None,days=7):
		self.name = 'Breakthrough Listen Project'
		self.pid = 'GBT16A-999'
		self.backend = 'Other'
		self.html_file = urllib2.urlopen(self.__buildURL__(date,str(days))).read()
		self.rows = self.__extractRows__(self.html_file)
		self.btlpSchedule = []

	def __extractRows__(self,page):
		soup = BeautifulSoup(page,'html.parser')
		return soup.table.find_all('tr')

	def __buildURL__(self,date,days):
		ctime,dc = time.gmtime(),re.compile('^[0-9]{2}/[0-9]{2}/[0-9]{4}$')
		if date is None: date = '/'.join([str(ctime[i]).zfill(2) for i in (1,2,0)])
		elif not dc.match(date): raise Exception('Invalid Input Date Format!')
		return 'https://dss.gb.nrao.edu/schedule/public/printerFriendly?tz=UTC&start='+date+'&days='+days

	def __utc2pst__(self,date,wctime, timezone = 'pst'):
		input_str = '{0} {1} UTC'.format(date,wctime)
		format_str = '%Y-%m-%d %H:%M'
		utcTime = time.strptime(input_str,format_str+' %Z') #DST is correct here.
		pstTime = time.localtime(calendar.timegm(utcTime)) #DST is correct here.
		#print('gbt_scraper.py: input_str:',input_str)
		#print('gbt_scraper.py: format_str:',format_str)
		#print('gbt_scraper.py: pstTime',pstTime)
		#print('gbt_scraper.py: utcTime',utcTime)
		if timezone == 'pst':
			return time.strftime(format_str,pstTime)
		elif timezone == 'utc':
			return time.strftime(format_str,utcTime)

	def make(self, t = 'pst'):
		headers = {1:'type',4:'pi',5:'friend',6:'rcvrs',7:'freq-ghz'}
		utc_date,entry = None,None
		for row in self.rows:
			if row.get('class') is not None and row.get('class')[0] == 'day_header':
				utc_date = row.find('th').text.split()[0]
			else:
				col = row.find_all('td')
				if col[3].text == self.name:
					if entry is None:
						entry = {headers[i]:col[i].text.strip() for i in (1,4,5,6,7)}
					stime,etime = col[0].text.split(' - ')
					if stime.startswith('+'):
						entry['end-time'] = self.__utc2pst__(utc_date,etime, timezone = t)
						if 'start-time' not in entry:
							entry['start-time'] = entry['end-time'].split()[0] + ' --:--'
						self.btlpSchedule.append(BLISPEntry(entry))
						entry = None
					elif etime.endswith('+'):
						entry['start-time'] = self.__utc2pst__(utc_date,stime, timezone = t)
					else:
						entry['start-time'] = self.__utc2pst__(utc_date,stime, timezone = t)
						entry['end-time'] = self.__utc2pst__(utc_date,etime, timezone = t)
						self.btlpSchedule.append(BLISPEntry(entry))
						entry = None

	def view(self,limit=None):
		if len(self.btlpSchedule) == 0: self.make()
		if limit is None: 
			limit = len(self.btlpSchedule)
		elif limit > len(self.btlpSchedule):
			raise Exception("Limit out of range.")
		for i in range(limit):
			print self.btlpSchedule[i]
					
	def next(self):
		self.view(1)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #

if __name__ == "__main__":
	date,days = None,7
	
	if len(sys.argv) > 1:
		if sys.argv[1].startswith('date'): 
			date = sys.argv[1].split('=')[1]
			if len(sys.argv) > 2 and sys.argv[2].startswith('days'):
				days = sys.argv[2].split('=')[1]
		elif sys.argv[1].startswith('days'): 
			days = sys.argv[1].split('=')[1]
			if len(sys.argv) > 2 and sys.argv[2].startswith('date'):
				date = sys.argv[2].split('=')[1]

	S = GBTScraper(date,days)
	S.make()
	S.view()