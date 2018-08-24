from datetime import datetime, timedelta
from pathlib import Path
from pyyamlconfig import load_config


WORKDAY_HOURS = 8
CURRENT_WEEK = datetime.now().isocalendar()[1]


def time_format(diff) -> str:
    prefix = ''
    if diff < timedelta(seconds=0):
        prefix = '-'
    hours = int(abs(diff.total_seconds()) / 3600)
    minutes = int((abs(diff.total_seconds()) - hours * 3600) / 60)
    return f'{prefix}{str(hours).zfill(2)}:{str(minutes).zfill(2)}'


class Day:
    def __init__(self, start_day=0, start_lunch=0, end_lunch=0, end_day=0):
        self.start_day = datetime.fromtimestamp(start_day)
        self.start_lunch = datetime.fromtimestamp(start_lunch)
        self.end_lunch = datetime.fromtimestamp(end_lunch)
        if end_day == 0:
            self.end_day = datetime.now()
        else:
            self.end_day = datetime.fromtimestamp(end_day)

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
        f'{time_format(current_day.day_time())} ({time_format(current_day.until_workday_done())}) | {time_format(workday.week_total())}'
    )
    print(workday.when_leave())
