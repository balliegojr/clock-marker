"""Clock work.

Usage:
  clock.py config WORKSPACE [--hours=HOURS ]
  clock.py activate WORKSPACE
  clock.py mark [--time=TIME --date=DATE]
  clock.py comment COMMENT [--date=DATE --time=TIME]
  clock.py show [-v -c --months=MONTHS --date=DATE]
  clock.py show WORKSPACE [-v -c --months=MONTHS --date=DATE]
  clock.py export [--months=MONTHS]
  clock.py migrate FILE
  clock.py check

  clock.py (-h | --help)
  clock.py --version

Options:
  -h --help             Show this screen.
  --version             Show version.
  --hours=8             The amount of hours to work in a given day
  --time=HHMM           Force a given time in the entry
  --date=DDMMYYYY       Force a given date in the entry
  --months=MONTHS       The amount of months to go backwards 
  -v                    Be verbose on the list
  -c                    Show comments
"""
import datetime, os, re, calendar
from docopt import docopt
from itertools import groupby
from peewee import SqliteDatabase, Model, DoesNotExist, JOIN, \
    PrimaryKeyField, DateTimeField, DateField, ForeignKeyField, TimeField, IntegerField, CharField, BooleanField

_db_name = os.path.dirname(os.path.realpath(__file__)) + '/clock-1.0.db'
db = SqliteDatabase(_db_name)


class WorkSpace(Model):
    class Meta:
        database = db

    id = PrimaryKeyField()
    name = CharField(null=False, unique=True, max_length=100)
    is_active = BooleanField(null=False, default=False)

    hours = IntegerField(null=False, default=8)


class WorkDay(Model):
    class Meta:
        database = db

    id = PrimaryKeyField()
    date = DateField(null=False)

    workspace = ForeignKeyField(WorkSpace, related_name='workdays')


class Comment(Model):
    class Meta:
        database = db

    id = PrimaryKeyField()
    time_spent = TimeField(null=True)
    text = CharField(null=False, max_length=100)

    work_day = ForeignKeyField(WorkDay, related_name='comments')


class PunchTime(Model):
    class Meta:
        database = db

    id = PrimaryKeyField()
    time = TimeField(null=False)
    work_day = ForeignKeyField(WorkDay, related_name='times')


def init():
    db.create_tables([WorkSpace, WorkDay, PunchTime, Comment], safe=True)


def config():
    hours = int(args['--hours']) if args['--hours'] else 8
    wp_name = args['WORKSPACE']

    try:
        workspace = WorkSpace.get(WorkSpace.name == wp_name)
        workspace.hours = hours
        workspace.save()
    except DoesNotExist:
        is_active = WorkSpace.select().where(WorkSpace.is_active==True).count() == 0
        WorkSpace.create(name=wp_name, hours = hours, is_active = is_active)

    print('%s is now configurated to work with %d hours' % (wp_name, hours))

def activate():
    wp_name = args['WORKSPACE']
    try:
        workspace = WorkSpace.get(WorkSpace.name == wp_name)

        WorkSpace.update(is_active=False).execute()

        workspace.is_active = True
        workspace.update()

        print('%s is now active' % wp_name)
    except DoesNotExist:
        raise Exception('There is no workspace with the given name')

def mark():
    punchtime = PunchTime()
    punchtime.time = _getTime()
    punchtime.work_day = _getWorkDay()
    punchtime.save()


def comment():
    _comment = Comment()
    _comment.work_day = _getWorkDay()
    _comment.text = args['COMMENT']

    if args['--time']:
        _comment.time_spent = _getTime()

    _comment.save()

def show():
    _query = WorkSpace.select().join(WorkDay, JOIN.LEFT_OUTER).join(PunchTime, JOIN.LEFT_OUTER)

    if args['WORKSPACE']:
        wp_name = args['WORKSPACE']
        _query = _query.where(WorkSpace.name == wp_name)
    else:
        _query = _query.where(WorkSpace.is_active == True)



    workspace = _query.order_by(WorkDay.date).get()

    print('Workspace: ', workspace.name, '\n')

    if len(workspace.workdays) == 0:
        print('There is no workdays in the given range')
        return;

    for month, month_group in groupby(workspace.workdays, lambda x: x.date.month):
        monthly = datetime.timedelta()

        print(calendar.month_name[month])
        for day in month_group:
            print('  ', day.date)




def export():
    pass

def check():
    pass

def migrate():
    pass

def _getWorkDay():
    if args['--date']:
        force_date = re.match(r'(\d{2})/?(\d{2})/?(\d{4})', args['--date'])
        day = int(force_date.group(1))
        month = int(force_date.group(2))
        year = int(force_date.group(3))
        date = datetime.date(year, month, day)
    else:
        date = datetime.date.today()

    try:
        workspace = WorkSpace.get(WorkSpace.is_active == True)
    except DoesNotExist:
        raise Exception('There is no workspace active, please activate one')

    try:
        workday = WorkDay.get((WorkDay.date == date) & (WorkDay.workspace == workspace))
    except DoesNotExist:
        workday = WorkDay.create(date = date, workspace = workspace)

    return workday


def _getTime():
    if args['--time']:
        
        force_time = re.match(r'(\d{1,2}):?(\d{2})', args['--time'])

        hour = int(force_time.group(1))
        minutes = int(force_time.group(2))

        return datetime.time(hour=hour, minute=minutes)

    else:
        return datetime.datetime.now().time()

# def total_hours(t):
#     return (t.days * 24) + (t.seconds / 60 / 60)

# def total_minutes(t):
#     return t.seconds % (60 * 60) / 60

# def list_tasks():
#     clocks = list(Clock.select())

#     if (len(clocks) == 0):
#         print('Without marks')
#         return

#     for month, clock_group in groupby(clocks, lambda x: x.date.month):

#         monthly = datetime.timedelta()
#         for day, daily_group in groupby(list(clock_group), lambda x: x.date):
#             daily = datetime.timedelta()
#             grouped = list(daily_group)
#             for g in grouped:
#                 daily += g.duration

#             print(day, daily)
#             if args.verbose:
#                 for g in grouped:
#                     print('\t {0} - {1} ({2})'.format(g.time_in.strftime('%H:%M:%S'), g.time_out.strftime('%H:%M:%S') if g.time_out is not None else ' ------ ', g.duration))

#             monthly += daily

#         print('')
#         print('Month %d :' % month, '%d hours and %d minutes' % ( total_hours(monthly), total_minutes(monthly)) );
#         print('')



def init_args():
    global args
    args = docopt(__doc__, version='Clock work 1.0')
    

if __name__ == '__main__':
    init()
    init_args()
    
    _locals = locals()

    for (arg, val) in args.items():
        if val == True and arg in _locals:
            to_call = arg

    try:    
        _locals[to_call]()
    except Exception as ex:
        print(ex)
