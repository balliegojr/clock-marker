# Clock #
A simple python project to clock in/out through command line

All information will be stored in a Sqlite database name clock.db in the same folder of the script

## Requirements ##
[Peewee](https://github.com/coleifer/peewee)

## Arguments ##
#### -h ####
Display help info
```
clock.py -h
```

#### in ####
Mark the entrance time
```
clock.py in
```
Use -f or --force to force an specific time
```
clock.py in -f 0900
```
#### out ####
Mark the exit time
```
clock.py out
```
Use -f or --force to force an specific time
```
clock.py out -f 1200
```

#### list ####
Summarize all clock marks
```
clock.py list

# output
2016-02-01 9:40:07.321210
2016-02-02 5:20:26.788790

Month 2 : 15 hours and 0 minutes
```
Use -v or --verbose to output daily information
```
clock.py list -v

#output
2016-02-01 9:40:07.321210
         10:33:48 - 11:57:06 (1:23:17.816578)
         12:48:37 - 19:06:44 (6:18:07.942531)
         21:43:43 - 23:42:25 (1:58:41.562101)
2016-02-02 5:21:29.758600
         09:12:38 - 11:55:36 (2:42:58.243846)
         12:40:47 -  ------  (2:38:31.514754)

Month 2 : 15 hours and 1 minutes

```
