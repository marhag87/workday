from datetime import datetime, timedelta
from pathlib import Path
import argparse
import os
from pyyamlconfig import load_config, write_config


WORKDAY_HOURS = 8
CURRENT_WEEK = datetime.now().isocalendar()[1]


def time_format(diff: timedelta, threshold=None) -> str:
    color = '#[fg=red]'
    default = '#[default]'
    prefix = ''
    if diff < timedelta(seconds=0):
        prefix = '-'
    if threshold is not None and diff >= timedelta(seconds=threshold):
        color = '#[fg=green]'
    hours = int(abs(diff.total_seconds()) / 3600)
    minutes = int((abs(diff.total_seconds()) - hours * 3600) / 60)
    if threshold is None:
        return f'{prefix}{str(hours).zfill(2)}:{str(minutes).zfill(2)}'
    else:
        return f'{color}{prefix}{str(hours).zfill(2)}:{str(minutes).zfill(2)}{default}'

def time_format_absolute(time: datetime, threshold=None) -> str:
    """
    If only time is sent, return time in format of HH:MM
    If time and threshold is sent, returns threshold in format of HH:MM with
    added tmux color codes dependant on time in relation to threshold. In this
    case, time should be the current time and threshold the comparison.
    """
    color = '#[fg=red]'
    default = '#[default]'
    if threshold is None:
        return datetime.strftime(time, '%H:%M')
    else:
        if time >= threshold:
            color = '#[fg=green]'
        return '{}{}{}'.format(
            color,
            datetime.strftime(threshold, '%H:%M'),
            default,
        )

def timestamp_from_string(datestring: str) -> int:
    hour, minute = datestring.split(':')
    now = datetime.now()
    return int(
        datetime(
            year=now.year,
            month=now.month,
            day=now.day,
            hour=int(hour),
            minute=int(minute),
        ).timestamp()
    )

def total_format(week_total: timedelta) -> str:
    if week_total != timedelta():
        return f'  -----\n  Total: {time_format(week_total)}\n'
    else:
        return ''

class Day:
    def __init__(self, start_day=0, start_lunch=0, end_lunch=0, end_day=0):
        now = datetime.now()
        self.start_day = now if start_day == 0 else datetime.fromtimestamp(start_day)
        self.start_lunch = now if start_lunch == 0 else datetime.fromtimestamp(start_lunch)
        self.end_lunch = now if end_lunch == 0 else datetime.fromtimestamp(end_lunch)
        self.end_day = now if end_day == 0 else datetime.fromtimestamp(end_day)

    def from_line(self, line) -> None:
        times = line.strip().split(' ')
        self.start_day = datetime.fromtimestamp(int(times[0]))
        self.start_lunch = datetime.fromtimestamp(int(times[1]))
        self.end_lunch = datetime.fromtimestamp(int(times[2]))
        self.end_day = datetime.fromtimestamp(int(times[3]))

    def to_line(self) -> str:
        return '{} {} {} {}\n'.format(
            int(datetime.timestamp(self.start_day)),
            int(datetime.timestamp(self.start_lunch)),
            int(datetime.timestamp(self.end_lunch)),
            int(datetime.timestamp(self.end_day)),
        )

    def day_time(self) -> timedelta:
        return self.end_day-self.start_day-(self.end_lunch-self.start_lunch)

    def until_workday_done(self) -> timedelta:
        return timedelta(hours=WORKDAY_HOURS) - self.day_time()

    @property
    def week(self):
        return self.start_day.isocalendar()[1]

    @property
    def day_name(self):
        return self.start_day.strftime('%A')

class Workday:
    def __init__(self, configfile=None):
        if configfile is None:
            if os.name == 'nt':
                configfile = f'{Path.home()}\workday.yaml'
            else:
                configfile = f'{Path.home()}/.config/workday.yaml'
        self.configfile = configfile
        self.config = load_config(configfile)
        self.days_file = self.config.get('days_file')
        self.until_today = timedelta()
        self.until_today_days = 0
        self.total_time = timedelta()
        self.total_days = 0
        self.week_days = []
        self.all_days = []

    def load(self) -> None:
        with open(self.days_file) as file:
            for line in file.readlines():
                day = Day()
                day.from_line(line)

                self.all_days.append(day)
                self.until_today += day.day_time()
                self.until_today_days += 1
                if day.week == CURRENT_WEEK:
                    self.week_days.append(day)
            self.all_days.append(self.current_day())
            self.total_time = self.until_today + self.current_day().day_time()
            self.total_days = self.until_today_days + 1

    def set_config(self, parameter, value):
        self.config[parameter] = value
        write_config(self.configfile, self.config)

    def log_day(self) -> None:
        with open(self.days_file, 'a') as file:
            file.write(self.current_day().to_line())

    def reset(self) -> None:
        self.set_config('start_day', 0)
        self.set_config('start_lunch', 0)
        self.set_config('end_lunch', 0)
        self.set_config('end_day', 0)

    def flex(self) -> timedelta:
        return self.until_today - timedelta(hours=(self.until_today_days * WORKDAY_HOURS))

    def current_day(self) -> Day:
        return Day(
            start_day=self.config.get('start_day', 0),
            start_lunch=self.config.get('start_lunch', 0),
            end_lunch=self.config.get('end_lunch', 0),
            end_day=self.config.get('end_day', 0),
        )

    def week_total(self) -> timedelta:
        total = timedelta()
        for day in self.week_days:
            total += day.day_time()
        total += self.current_day().day_time()
        return total

    def when_leave(self) -> datetime:
        """When you can leave and have zero flex"""
        return datetime.now() + self.current_day().until_workday_done() - self.flex()

    def tmux_status(self) -> str:
        current_day = self.current_day()
        return '{} ({}) | {} | {}'.format(
            time_format(current_day.day_time(), threshold=(8 * 60 * 60)),
            time_format(current_day.until_workday_done()),
            time_format(self.week_total(), threshold=(7 * 8 * 60 * 60)),
            time_format_absolute(datetime.now(), self.when_leave()),
        )

    def workday_status(self):
        week = None
        week_total = timedelta()
        result = ''
        for day in self.all_days:
            if week != day.week:
                result += total_format(week_total)
                result += str(day.week) + '\n'
                week = day.week
                week_total = timedelta()

            result += '  {} {}\n'.format(
                day.day_name,
                time_format(day.day_time()),
            )
            week_total += day.day_time()
        result += total_format(week_total)
        result += '\nFlex (until today): {}'.format(
            time_format(self.flex()),
        )
        result += '\nFlex (leave now): {}'.format(
            time_format(datetime.now()-self.when_leave())
        )
        result += '\nZero flex at: {}'.format(
            time_format_absolute(self.when_leave())
        )
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config',
        '-c',
        help='location of configuration file',
        action='store',
        nargs='?',
        const=None,
        default=None,
    )
    parser.add_argument(
        '--start-day',
        help='start day at HH:MM, defaults to current time',
        action='store',
        metavar='HH:MM',
        nargs='?',
        const=time_format_absolute(datetime.now()),
    )
    parser.add_argument(
        '--end-day',
        help='end day at HH:MM, defaults to current time',
        action='store',
        metavar='HH:MM',
        nargs='?',
        const=time_format_absolute(datetime.now()),
    )
    parser.add_argument(
        '--lunch',
        help='lunch occured between HH:MM and HH:MM',
        action='store',
        metavar='HH:MM',
        nargs=2,
    )
    parser.add_argument('--log-day', '-l', help='add day to persistent log', action='store_true')
    parser.add_argument('--reset', '-r', help='reset data for today', action='store_true')
    parser.add_argument('--reset-end', help='reset data for end of day', action='store_true')
    parser.add_argument('--tmux', '-t', help='print tmux format', action='store_true')
    parser.add_argument('--weeks', '-w', help='print weeks status', action='store_true')
    args = parser.parse_args()
    workday = Workday(configfile=args.config)
    if args.reset:
        workday.reset()
    elif args.reset_end:
        workday.set_config('end_day', 0)
    elif args.start_day is not None:
        workday.set_config('start_day', timestamp_from_string(args.start_day))
    elif args.end_day is not None:
        workday.set_config('end_day', timestamp_from_string(args.end_day))
    elif args.lunch is not None:
        workday.set_config('start_lunch', timestamp_from_string(args.lunch[0]))
        workday.set_config('end_lunch', timestamp_from_string(args.lunch[1]))
    elif args.log_day:
        workday.log_day()
    elif args.tmux:
        workday.load()
        print(workday.tmux_status())
    elif args.weeks:
        workday.load()
        print(workday.workday_status())
    else:
        parser.print_help()
