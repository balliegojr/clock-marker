# Clock #
A simple command line python project to track time

All information will be stored in a Sqlite database name clock-1.0.db in the same folder of the script

## Requirements ##
[Peewee](https://github.com/coleifer/peewee)
[Docopt](https://github.com/docopt/docopt)


## Usage ##
There must be at least on Workspace active to keep track
```
python clock.py config example-wp --hours=8 --date-format=%Y/%m/%d

or just

python clock.py config example-wp
```

The default values are:
hours: 8
date-format: %Y/%m/%d


When a single workspace is created, it is already activated. If you have more than one workspace, it is possible to activate a specific workspace
```
python clock.py activate example-wp
```

The active workspace becomes the default workspace.

After a workspace is created, it is possible to create time marks and notes
```
python clock.py mark
python clock.py comment "this is a nice comment"
```

## Arguments ##
#### -h --help ####
Display help info
```
python clock.py help
```

#### config ####
Configurate a workspace
```
python clock.py config WORKSPACE [--hours=HOURS --date-format=DATEFORMAT ]
```

#### getconfig ####
Show the configuration of the given workspace
```
python clock.py getconfig WORKSPACE
```

#### activate ####
Activate the given workspace, only one workspace can be active at time
```
python clock.py activate WORKSPACE
python clock.py activate example-wp
```

#### mark ####
Mark the time, it is possible to force an especific time and date, also is possible to mark the time in another workspace
```
python clock.py mark
python clock.py --time=10:00 --date=2010/10/10

python clock.py mark ProjectX
```

#### comment ####
Create a comment in a date, it is possible to force an especific date
--time anotates the time of the comment
```
python clock.py comment "Spent the day working on project X" --date=2010/10/10
python clock.py comment ProjectY "Spent some time in this task" --time=02:00
```

#### lookup ####
Lookup for a given text in all the coments
```
python clock.py lookup "*project*"
python clock.py lookup ProjectY "task-35*"
```


#### show ####
Print marks and comments. It is possible to limit to a given date with --date or to a number of months with --months
```
python clock.py show
python clock.py show ProjectX
```

Outputs:
```
Month
  Date D   (total time of day / balance of hours according to the workspace configuration)
  Date D+1 (total time of day / balance of hours according to the workspace configuration)

Month total: Total time of month (balance of the month)
```

```
python clock.py show -vc
```
Outputs:
```
Month
  Date D
  	time - time (balance)
  	time - time (balance)
  Notes D
  	time - text
  	time - text

  
  Date D+1
  	time - time (balance)
  	time - time (balance)

  Notes D+1
  	time - text
  	time - text

Month total: Total time of month (balance of the month)

```
 
#### export ####
Exports two csv files (workspace_hours.csv and workspace_notes.csv).

```
python clock.py export --months=3
python clock.py export ProjectX
```

#### import ####
Import the contents of a csv times file
```
python clock.py import ProjectX path_to_file.csv
```

#### check ####
Check if all dates have an even number of marks
```
python clock.py check
```
  