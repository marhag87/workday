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