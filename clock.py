"""Clock work.

Usage:
  clock.py config WORKSPACE [--hours=HOURS --date-format=DATEFORMAT ]
  clock.py activate WORKSPACE
  clock.py mark [--time=TIME --date=DATE]
  clock.py mark WORKSPACE [--time=TIME --date=DATE]
  clock.py comment COMMENT [--date=DATE --time=TIME]
  clock.py comment WORKSPACE COMMENT [--date=DATE --time=TIME]
  clock.py lookup COMMENT
  clock.py lookup WORKSPACE COMMENT
  clock.py show [-v -c][--months=MONTHS|--date=DATE]
  clock.py show WORKSPACE [-v -c][--months=MONTHS|--date=DATE]
  clock.py export [--months=MONTHS]
  clock.py export WORKSPACE [--months=MONTHS]
  clock.py migrate WORKSPACE FILE
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
import datetime, os, re, calendar, inspect, csv
from docopt import docopt
from itertools import groupby
from math import ceil
from peewee import SqliteDatabase, Model, DoesNotExist, JOIN, fn, OP, \
    PrimaryKeyField, DateTimeField, DateField, ForeignKeyField, TimeField, IntegerField, CharField, BooleanField


from peewee import Expression # the building block for expressions

OP['MOD'] = 'mod'
def mod(lhs, rhs):
    return Expression(lhs, OP.MOD, rhs)

SqliteDatabase.register_ops({OP.MOD: '%'})

_db_name = os.path.dirname(os.path.realpath(__file__)) + '/clock-1.0.db'
db = SqliteDatabase(_db_name)


class WorkSpace(Model):
    '''
        Represents the workspace Model
    '''
    class Meta:
        database = db

    id = PrimaryKeyField()
    name = CharField(null=False, unique=True, max_length=100)
    is_active = BooleanField(null=False, default=False)

    hours = IntegerField(null=False, default=8)
    date_format = CharField(null=False, max_length=10)


class WorkDay(Model):
    '''
        Represents a WorkDay Model
    '''
    class Meta:
        database = db

    id = PrimaryKeyField()
    date = DateField(null=False)

    workspace = ForeignKeyField(WorkSpace, related_name='workdays')


class Comment(Model):
    '''
        Represents a Comment Model
    '''
    class Meta:
        database = db

    id = PrimaryKeyField()
    time_spent = TimeField(null=True)
    text = CharField(null=False, max_length=100)

    work_day = ForeignKeyField(WorkDay, related_name='comments')


    def __str__(self):
        return '{0} {1}'.format(
            self.time_spent.strftime('%H:%M') if self.time_spent else '--:--',
            self.text
            )

class PunchTime(Model):
    '''
        Represents a PunchTime Model
    '''
    class Meta:
        database = db

    id = PrimaryKeyField()
    time = TimeField(null=False)
    work_day = ForeignKeyField(WorkDay, related_name='times')


def init():
    db.create_tables([WorkSpace, WorkDay, PunchTime, Comment], safe=True)


def config(wp_name, hours = None, date_format=None):
    '''
        Configure the given workspace
            hours

    '''
    wp_name = args['WORKSPACE']

    try:
        workspace = WorkSpace.get(WorkSpace.name == wp_name)
    except DoesNotExist:
        is_active = WorkSpace.select().where(WorkSpace.is_active==True).count() == 0
        workspace = WorkSpace.create(name=wp_name, is_active = is_active, date_format='%Y/%m/%d')
        workspace.hours = 8
    
    if hours:
        workspace.hours = int(hours)

    if date_format:
        workspace.date_format = date_format

    workspace.save()
    print('%s is now configurated to work with %d hours' % (wp_name, workspace.hours))


def activate(wp_name):
    '''
        Activate the given workspace
    '''

    try:
        workspace = WorkSpace.get(WorkSpace.name == wp_name)

        WorkSpace.update(is_active=False).execute()

        workspace.is_active = True
        workspace.save()

        print('%s is now active' % wp_name)
    except DoesNotExist:
        raise Exception('There is no workspace with the given name')


def mark(wp_name = None, time = None, date = None):
    '''
        Mark the time in the clock
    '''
    punchtime = PunchTime()
    punchtime.time = _getTime(time)
    punchtime.work_day = _getWorkDay(wp_name, date)
    punchtime.save()


def comment(comment, wp_name=None, time=None, date=None):
    _comment = Comment()
    _comment.work_day = _getWorkDay(wp_name, date)
    _comment.text = comment

    if time:
        _comment.time_spent = _getTime(time)

    _comment.save()


def show(verbose, show_comments, wp_name=None, date=None, months=None):
    _query = WorkSpace.select(WorkSpace, WorkDay, PunchTime).join(WorkDay, JOIN.LEFT_OUTER).join(PunchTime, JOIN.LEFT_OUTER)

    if wp_name:
        _query = _query.where(WorkSpace.name == wp_name)
    else:
        _query = _query.where(WorkSpace.is_active == True)

    if date:
        date = _getWorkDay(wp_name, date)
        _query = _query.where(WorkDay.date == date.date)

    if months:
        days = int(months) * 30
        limit = datetime.date.today() - datetime.timedelta(days=days)
        _query = _query.where(WorkDay.date >= limit)
        

    workspace_query = _query.order_by(WorkDay.date, PunchTime.time).aggregate_rows()
    for workspace in workspace_query:
        print('Workspace: ', workspace.name, '\n')

        daily_goal = datetime.timedelta(hours=workspace.hours)

        if len(workspace.workdays) == 0:
            print('There is no workdays in the given range')
            return;

        for month, month_group in groupby(workspace.workdays, lambda x: x.date.month):
            days_count = 0
            month_delta = datetime.timedelta()

            print(calendar.month_name[month])
            
            for day in month_group:
                days_count = days_count + 1
                total_times = len(day.times)
                
                if verbose and (total_times > 0 or (show_comments and len(day.comments) > 0)):
                    print('  ', day.date.strftime(workspace.date_format))

                if total_times > 0:
                    day_delta = datetime.timedelta()

                    for x in range(0, total_times, 2):
                        f_time = day.times[x].time
                        if x+1 < total_times:
                            s_time = day.times[x+1].time

                            _delta = datetime.timedelta(hours=s_time.hour, minutes=s_time.minute, seconds=s_time.second) - \
                                datetime.timedelta(hours=f_time.hour, minutes=f_time.minute, seconds=f_time.second)

                            day_delta = day_delta + _delta


                            if verbose:
                                print('    ',f_time.strftime('%H:%M:%S'), ' - ', s_time.strftime('%H:%M:%S'), '({0})'.format(_delta))
                        else:
                            if verbose:
                                # calculate goal
                                print('    ',f_time.strftime('%H:%M:%S'), ' -  **:**:**')

                    month_delta = month_delta + day_delta
                    if verbose:
                        print('\t', '({0}/{1})'.format(day_delta, _getDailyGoal(day_delta, daily_goal)))
                        print('')
                    else:
                        print('  ', day.date.strftime(workspace.date_format), '({0}/{1})'.format(day_delta, _getDailyGoal(day_delta, daily_goal)))

                if show_comments:
                    if verbose and len(day.comments):
                        print('   Notes')

                    for comment in day.comments:
                        print('     ', str(comment))

                    if verbose and len(day.comments):
                        print('')

            print('')
            print('{0} total:{1} ({2})'.format(calendar.month_name[month],month_delta, _getMonthGoal(workspace.hours, days_count, month_delta)))
            print('')


def export(wp_name, months):
    path = os.getcwd()
    wp = _getWorkSpace(wp_name)

    _query = (WorkDay
        .select(WorkDay, PunchTime, Comment)
        .join(PunchTime, JOIN.LEFT_OUTER)
        .switch(WorkDay)
        .join(Comment, JOIN.LEFT_OUTER)
        .where(WorkDay.workspace_id == wp.id))
        

    if months:
        days = int(months) * 30
        limit = datetime.date.today() - datetime.timedelta(days=days)
        _query = _query.where(WorkDay.date >= limit)
        
    workdays = _query.order_by(WorkDay.date, PunchTime.time).aggregate_rows()

    with open(wp.name + '_hours.csv', 'w', newline='') as csvfile:
        hourswriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        hourswriter.writerow(['date','time'])
        for workday in workdays:

            for time in workday.times:
                hourswriter.writerow((
                    workday.date.strftime(wp.date_format), 
                    time.time.strftime('%H:%M:%S')
                    ))

    with open(wp.name + '_notes.csv', 'w', newline='') as csvfile:
        commentwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
        commentwriter.writerow(['date','time_spent','note'])

        for workday in workdays:
            for comment in workday.comments:
                commentwriter.writerow((
                    workday.date.strftime(wp.date_format), 
                    comment.time_spent.strftime('%H:%M') if comment.time_spent else '', 
                    comment.text
                    ))


def check(wp_name):
    wp = _getWorkSpace(wp_name)

    query = (WorkDay
         .select(WorkDay.date, fn.COUNT(PunchTime.id).alias('times_count'))
         .join(PunchTime)
         .where(WorkDay.workspace_id == wp.id)
         .group_by(WorkDay.date)
         .order_by(WorkDay.date)
         .having(mod(fn.COUNT(PunchTime.id), 2) == 1)
         ).aggregate_rows()

    if  len(query) == 0:
        print('There are no missing marks')
        return

    print('The following days have an odd number of marks')

    for workday in query:
        print(workday.date.strftime(wp.date_format))
    

def migrate(wp_name, file_name):
    with open(file_name, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        for row in csvreader:
            mark(wp_name=wp_name, time=row['time'], date=row['date'])


def lookup(comment, wp_name=None):
    workspace = _getWorkSpace(wp_name)
    workdays = (WorkDay
        .select(WorkDay, Comment)
        .join(Comment)
        .where((WorkDay.workspace_id == workspace.id) & (Comment.text % comment) )
        ).aggregate_rows()

    if len(workdays) == 0:
        print('No comments found')

    for workday in workdays:
        print(workday.date.strftime(wp.date_format))
        for _comment in workday.comments:
            print('     ', str(_comment))
               

def _getWorkSpace(wp_name=None):
    if wp_name:
        try:
            workspace = WorkSpace.get(WorkSpace.name == wp_name)
        except DoesNotExist:
            raise Exception('There is no workspace with the given name')
    else:
        try:
            workspace = WorkSpace.get(WorkSpace.is_active == True)
        except DoesNotExist:
            raise Exception('There is no workspace active, please activate one')

    return workspace


def _getWorkDay(wp_name=None, date=None):
    workspace = _getWorkSpace(wp_name)

    if date:
        date = datetime.datetime.strptime(date, workspace.date_format).date()
    else:
        date = datetime.date.today()


    try:
        workday = WorkDay.get((WorkDay.date == date) & (WorkDay.workspace == workspace))
    except DoesNotExist:
        workday = WorkDay.create(date = date, workspace = workspace)

    return workday


def _getTime(time = None):
    if time:
        force_time = re.match(r'(\d{1,2}):?(\d{2})(:?(\d{2}))?', time)

        hour = int(force_time.group(1))
        minutes = int(force_time.group(2))
        seconds = int(force_time.group(4)) if force_time.group(4) else 0

        return datetime.time(hour=hour, minute=minutes, second=seconds)

    else:
        return datetime.datetime.now().time()


def _getDailyGoal(total, goal):
    if total < goal:
        return '-{0}'.format((goal - total))

    return '+{0}'.format(total - goal)


def _getMonthGoal(hours_goal, total_days, total):
    goal = datetime.timedelta(hours=total_days*hours_goal)

    if total < goal:
        return '-{0}'.format((goal - total))

    return '+{0}'.format(total - goal)


def _init_args():
    global args
    args = docopt(__doc__, version='Clock work 1.0')
    

def _get_args(f):
    '''
        converts the arguments list to the arguments of the function
    '''
    arg_list = inspect.getargspec(f)[0]

    kwargs = {
        'wp_name': args['WORKSPACE'],
        'hours': args['--hours'],
        'time': args['--time'],
        'date': args['--date'],
        'comment': args['COMMENT'],
        'months': args['--months'],
        'verbose': args['-v'],
        'show_comments': args['-c'],
        'file_name': args['FILE'],
        'date_format': args['--date-format']
    }

    return dict([(k, kwargs[k]) for k in arg_list if k in kwargs])

if __name__ == '__main__':
    init()
    _init_args()
    
    _locals = locals()

    for (arg, val) in args.items():
        if val == True and arg in _locals:
            to_call = arg

    kwargs = _get_args(_locals[to_call])

    try:    
        _locals[to_call](**kwargs)
    except Exception as ex:
        print(ex)
