from peewee import SqliteDatabase, Model, PrimaryKeyField, DateTimeField, DoesNotExist
import argparse, datetime, os, re
from itertools import groupby

parser = argparse.ArgumentParser(description='Clock work')
parser.add_argument('action', metavar='Action', choices=['in', 'out', 'list'], help='the task to be executed [in, out, list]')
parser.add_argument('-f', '--force', help="force a given time with format HHMM (0900)")
parser.add_argument('-v', '--verbose', help="Be more verbose in the list", action='store_true')

args = parser.parse_args()
_db_name = os.path.dirname(os.path.realpath(__file__)) + '/clock.db'
db = SqliteDatabase(_db_name)

actions = {}

class Clock(Model):
	class Meta:
		database = db

	id = PrimaryKeyField()
	time_in = DateTimeField(null=False)
	time_out = DateTimeField(null=True)

	@property
	def date(self):
		return datetime.date(self.time_in.year, self.time_in.month, self.time_in.day)

	@property
	def duration(self):
		if self.time_out is not None:
			return self.time_out - self.time_in
		else:
			return datetime.datetime.now() - self.time_in

def init():
	Clock.create_table(fail_silently=True)

def _getTime():
	if (args.force is None):
		return datetime.datetime.now()

	today = datetime.datetime.today()
	force_time = re.match(r'(\d{1,2}):?(\d{2})', args.force)

	hour = int(force_time.group(1))
	minutes = int(force_time.group(2))

	return datetime.datetime.combine(today, datetime.time(hour, minutes))

def time_in():
	if Clock.select().where(Clock.time_out.is_null(True)).count() == 0:
		Clock.create(time_in=_getTime())
	else:
		print('You have to go out first')

def time_out():

	try:
		clock = Clock.get(Clock.time_out.is_null(True))
	except DoesNotExist:
		print('You have to go in first')
		return

	clock.time_out = _getTime()
	clock.save()

	print('clock out:', clock.duration)

def total_hours(t):
	return (t.days * 24) + (t.seconds / 60 / 60)

def total_minutes(t):
	return t.seconds % (60 * 60) / 60

def list_tasks():
	clocks = list(Clock.select())

	if (len(clocks) == 0):
		print('Without marks')
		return

	for month, clock_group in groupby(clocks, lambda x: x.date.month):

		monthly = datetime.timedelta()
		for day, daily_group in groupby(list(clock_group), lambda x: x.date):
			daily = datetime.timedelta()
			grouped = list(daily_group)
			for g in grouped:
				daily += g.duration

			print(day, daily)
			if args.verbose:
				for g in grouped:
					print('\t {0} - {1} ({2})'.format(g.time_in.strftime('%H:%M:%S'), g.time_out.strftime('%H:%M:%S') if g.time_out is not None else ' ------ ', g.duration))

			monthly += daily

		print('')
		print('Month %d :' % month, '%d hours and %d minutes' % ( total_hours(monthly), total_minutes(monthly)) );
		print('')

init()

actions['in'] = time_in
actions['out'] = time_out
actions['list'] = list_tasks

actions[args.action]()
