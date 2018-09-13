workday
=======
Keep track of how long you have worked and the amount of flex time you have

Installation
============
* Install python

* Download this repo and cd to it

* `pip install .`

* Add a config file with "days_file: \<location of days file\>".

Default location for the config file is ~/.config/workday.yaml on linux and %USERPROFILE%\workday.yaml on windows

The days file contains all the data and should be backed up.

Usage
=====
`workday.py -w` Shows a summary

`workday.py --start-day 07:30` Sets your start of day to 07:30

`workday.py --lunch 11:30 12:00` Sets your lunch to 11:30-12:00

`workday.py --end-day 16:00` Sets your end of day to 16:00

`workday.py -l` Logs todays data to the days file

Automation
==========
These instructions are suggestions on how to automate the input of times

Linux
-----
Use cron to log and reset the day log, for example:

`0 18 * * * /home/marhag87/.virtualenvs/workday/bin/python /home/marhag87/git/workday/workday/workday.py -l`

`0 0 * * * /home/marhag87/.virtualenvs/workday/bin/python /home/marhag87/git/workday/workday/workday.py -r`

Use a script to trigger your lock, or look for it in some way. For example:

```
# Assume locking screen ends the day
/home/marhag87/.virtualenvs/workday/bin/python /home/marhag87/git/workday/workday/workday.py --end-day
# Don't fork i3lock
i3lock -n
# Assume unlocking starts the day, but don't edit if it's not 0
/home/marhag87/.virtualenvs/workday/bin/python /home/marhag87/git/workday/workday/workday.py --start-empty-day
# If you unlock, the day has not ended. Reset it
/home/marhag87/.virtualenvs/workday/bin/python /home/marhag87/git/workday/workday/workday.py --reset-end
```

Windows
-------
Windows can use the Task Scheduler to trigger the jobs.

Use the following triggers and actions:

* On workstation lock: run script with "--end-day"
* On workstation unlock: run script twice, once with "--start-empty-day" and once with "--reset-end"
* Before midnight: run script with "-l"
* At midnight: run script with "-r"
* At system startup: run script twice, once with "--start-empty-day" and once with "--reset-end"
* At system shutdown: run script with "--end-day"

System shutdown is not a normal trigger. You can use "on event" with Log: System, Source: User32, Event ID: 1074
