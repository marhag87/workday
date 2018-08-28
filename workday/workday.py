from datetime import datetime, timedelta
from pathlib import Path
from pyyamlconfig import load_config


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

class Day:
    def __init__(self, start_day=0, start_lunch=0, end_lunch=0, end_day=0):
        self.start_day = datetime.now() if start_day == 0 else datetime.fromtimestamp(start_day)
        self.start_lunch = datetime.fromtimestamp(start_lunch)
        self.end_lunch = datetime.fromtimestamp(end_lunch)
        self.end_day = datetime.now() if end_day == 0 else datetime.fromtimestamp(end_day)

    def from_line(self, line) -> None:
        times = line.strip().split(' ')
        self.start_day = datetime.fromtimestamp(int(times[0]))
        self.start_lunch = datetime.fromtimestamp(int(times[1]))
        self.end_lunch = datetime.fromtimestamp(int(times[2]))
        self.end_day = datetime.fromtimestamp(int(times[3]))

    def day_time(self) -> timedelta:
        return self.end_day-self.start_day-(self.end_lunch-self.start_lunch)

    def until_workday_done(self) -> timedelta:
        return timedelta(hours=WORKDAY_HOURS) - self.day_time()

    @property
    def week(self):
        return self.start_day.isocalendar()[1]

class Workday:
    def __init__(self, configfile=None):
        if configfile is None:
            configfile = f'{Path.home()}/.config/workday.yaml'
        self.config = load_config(configfile)
        self.days_file = self.config.get('days_file')
        self.until_today = timedelta()
        self.until_today_days = 0
        self.total_time = timedelta()
        self.total_days = 0
        self.week_days = []

    def load(self) -> None:
        with open(self.days_file) as file:
            for line in file.readlines():
                day = Day()
                day.from_line(line)

                self.until_today += day.day_time()
                self.until_today_days += 1
                if day.week == CURRENT_WEEK:
                    self.week_days.append(day)
            self.total_time = self.until_today + self.current_day().day_time()
            self.total_days = self.until_today_days + 1

    def flex(self) -> timedelta:
        return self.until_today - timedelta(hours=(self.until_today_days * WORKDAY_HOURS))

    def get_single_time_from_file(self, config_name) -> int:
        with open(self.config.get(config_name)) as file:
            return int(file.read().strip())

    def current_day(self) -> Day:
        return Day(
            start_day=self.get_single_time_from_file('start_day_file'),
            start_lunch=self.get_single_time_from_file('start_lunch_file'),
            end_lunch=self.get_single_time_from_file('end_lunch_file'),
            end_day=0,
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

if __name__ == '__main__':
    workday = Workday()
    workday.load()
    current_day=workday.current_day()

    print(
        '{} ({}) | {} | {}'.format(
            time_format(current_day.day_time(), threshold=(8*60*60)),
            time_format(current_day.until_workday_done()),
            time_format(workday.week_total(), threshold=(7*8*60*60)),
            time_format_absolute(datetime.now(), workday.when_leave()),
        )
    )
