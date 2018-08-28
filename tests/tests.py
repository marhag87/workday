import unittest
from workday import Workday, time_format, time_format_absolute
from datetime import datetime, timedelta
from freezegun import freeze_time


class DataFiles:
    def __init__(self):
        self._days = 'tests/days.log'
        self._start_day = 'tests/start_of_day'
        self._start_lunch = 'tests/start_of_lunch'
        self._end_lunch = 'tests/end_of_lunch'
        self._end_day = 'tests/end_of_day'

    def reset(self):
        open(self._days, 'w').close()
        for filename in [self._start_day, self._start_lunch, self._end_lunch, self._end_day]:
            with open(filename, 'w') as file:
                file.write('0')

    def add_log(self, start_day: datetime, start_lunch: datetime, end_lunch: datetime, end_day: datetime):
        with open(self._days, 'a') as file:
            file.write(
                '{} {} {} {}\n'.format(
                    int(start_day.timestamp()),
                    int(start_lunch.timestamp()),
                    int(end_lunch.timestamp()),
                    int(end_day.timestamp()),
                )
            )

    @staticmethod
    def get_file(filename):
        with open(filename) as file:
            time = file.read().strip()
        return datetime.fromtimestamp(int(time))

    @staticmethod
    def set_file(filename, value):
        with open(filename, 'w') as file:
            file.write(f'{int(value.timestamp())}')

    @property
    def start_day(self):
        return self.get_file(self._start_day)

    @start_day.setter
    def start_day(self, value: datetime):
        self.set_file(self._start_day, value)

    @property
    def start_lunch(self):
        return self.get_file(self._start_lunch)

    @start_lunch.setter
    def start_lunch(self, value: datetime):
        self.set_file(self._start_lunch, value)

    @property
    def end_lunch(self):
        return self.get_file(self._end_lunch)

    @end_lunch.setter
    def end_lunch(self, value: datetime):
        self.set_file(self._end_lunch, value)

    @property
    def end_day(self):
        return self.get_file(self._end_day)

    @end_day.setter
    def end_day(self, value: datetime):
        self.set_file(self._end_day, value)

@freeze_time("2018-08-22 13:30")
class TestWorkday(unittest.TestCase):
    def setUp(self):
        self.workday = Workday(
            configfile='tests/config.yaml'
        )
        self.files = DataFiles()
        self.files.reset()

    def test_sum(self):
        """Test that summary times are reasonable"""
        self.files.add_log(
            start_day=datetime(2018, 8, 20, 8, 0),
            start_lunch=datetime(2018, 8, 20, 11, 0),
            end_lunch=datetime(2018, 8, 20, 12, 0),
            end_day=datetime(2018, 8, 20, 17, 0),
        )
        self.files.add_log(
            start_day=datetime(2018, 8, 21, 8, 0),
            start_lunch=datetime(2018, 8, 21, 11, 0),
            end_lunch=datetime(2018, 8, 21, 12, 0),
            end_day=datetime(2018, 8, 21, 16, 30),
        )
        self.files.start_day = datetime(2018, 8, 22, 8, 0)
        self.files.start_lunch = datetime(2018, 8, 22, 11, 0)
        self.files.end_lunch = datetime(2018, 8, 22, 12, 0)
        self.workday.load()
        self.assertEqual(
            self.workday.until_today,
            timedelta(hours=15, minutes=30),
        )
        self.assertEqual(
            self.workday.total_time,
            timedelta(hours=20),
        )

    def test_positive_flex(self):
        """Test that flex can be positive"""
        self.files.add_log(
            start_day=datetime(2018, 8, 20, 8, 0),
            start_lunch=datetime(2018, 8, 20, 11, 0),
            end_lunch=datetime(2018, 8, 20, 12, 0),
            end_day=datetime(2018, 8, 20, 17, 30),
        )
        self.files.add_log(
            start_day=datetime(2018, 8, 21, 8, 0),
            start_lunch=datetime(2018, 8, 21, 11, 0),
            end_lunch=datetime(2018, 8, 21, 12, 0),
            end_day=datetime(2018, 8, 21, 17, 10),
        )
        self.files.start_day = datetime(2018, 8, 22, 8, 0)
        self.files.start_lunch = datetime(2018, 8, 22, 11, 0)
        self.files.end_lunch = datetime(2018, 8, 22, 12, 0)
        self.workday.load()
        self.assertEqual(
            self.workday.flex(),
            timedelta(minutes=40),
        )
        self.assertEqual(
            self.workday.when_leave(),
            datetime(2018, 8, 22, 16, 20),
        )

    def test_negative_flex(self):
        """Test that flex can be negative"""
        self.files.add_log(
            start_day=datetime(2018, 8, 20, 8, 0),
            start_lunch=datetime(2018, 8, 20, 11, 0),
            end_lunch=datetime(2018, 8, 20, 12, 0),
            end_day=datetime(2018, 8, 20, 16, 30),
        )
        self.files.add_log(
            start_day=datetime(2018, 8, 21, 8, 0),
            start_lunch=datetime(2018, 8, 21, 11, 0),
            end_lunch=datetime(2018, 8, 21, 12, 0),
            end_day=datetime(2018, 8, 21, 16, 50),
        )
        self.files.start_day = datetime(2018, 8, 22, 8, 0)
        self.files.start_lunch = datetime(2018, 8, 22, 11, 0)
        self.files.end_lunch = datetime(2018, 8, 22, 12, 0)
        self.workday.load()
        self.assertEqual(
            self.workday.flex(),
            timedelta(minutes=-40),
        )
        self.assertEqual(
            self.workday.when_leave(),
            datetime(2018, 8, 22, 17, 40),
        )

class TestFormat(unittest.TestCase):
    def test_timedelta(self):
        # Test without tmux
        self.assertEqual(
            time_format(timedelta(hours=8)),
            '08:00',
        )
        # Test that it colors green when over threshold
        self.assertEqual(
            time_format(timedelta(hours=8), threshold=(7*60*60)),
            '#[fg=green]08:00#[default]',
        )
        # Test that it colors green when exactly on threshold
        self.assertEqual(
            time_format(timedelta(hours=8), threshold=(8 * 60 * 60)),
            '#[fg=green]08:00#[default]',
        )
        # Test that it colors red when under threshold
        self.assertEqual(
            time_format(timedelta(hours=7), threshold=(8 * 60 * 60)),
            '#[fg=red]07:00#[default]',
        )

    def test_timedelta_absolute(self):
        # Test without tmux
        self.assertEqual(
            time_format_absolute(datetime.strptime('2018-08-22 17:00', '%Y-%m-%d %H:%M')),
            '17:00',
        )
        # Test that it colors green when over threshold
        self.assertEqual(
            time_format_absolute(
                datetime.strptime('2018-08-22 17:00', '%Y-%m-%d %H:%M'),
                threshold=datetime.strptime('2018-08-22 16:00', '%Y-%m-%d %H:%M'),
            ),
            '#[fg=green]16:00#[default]',
        )
        # Test that it colors green when exactly on threshold
        self.assertEqual(
            time_format_absolute(
                datetime.strptime('2018-08-22 17:00', '%Y-%m-%d %H:%M'),
                threshold=datetime.strptime('2018-08-22 17:00', '%Y-%m-%d %H:%M'),
            ),
            '#[fg=green]17:00#[default]',
        )
        # Test that it colors red when under threshold
        self.assertEqual(
            time_format_absolute(
                datetime.strptime('2018-08-22 16:00', '%Y-%m-%d %H:%M'),
                threshold=datetime.strptime('2018-08-22 17:00', '%Y-%m-%d %H:%M'),
            ),
            '#[fg=red]17:00#[default]',
        )

if __name__ == '__main__':
    unittest.main()