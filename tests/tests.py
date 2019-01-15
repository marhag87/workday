import unittest
from workday import Workday, Day, time_format, time_format_absolute, timestamp_from_string
from datetime import datetime, timedelta
from freezegun import freeze_time


class DataFiles:
    def __init__(self):
        self._days = 'tests/days.log'
        open(self._days, 'w').close()

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


@freeze_time("2018-08-22 13:30")
class TestWorkday(unittest.TestCase):
    def setUp(self):
        self.workday = Workday(
            configfile='tests/config.yaml'
        )
        self.files = DataFiles()
        self.workday.reset()
        self.workday.set_config('start_day', timestamp_from_string('08:00'))
        self.workday.set_config('start_lunch', timestamp_from_string('11:00'))
        self.workday.set_config('end_lunch', timestamp_from_string('12:00'))

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
        self.workday.load()
        self.assertEqual(
            self.workday.flex(),
            timedelta(minutes=-40),
        )
        self.assertEqual(
            self.workday.when_leave(),
            datetime(2018, 8, 22, 17, 40),
        )

    def test_tmux_string(self):
        """Test that a tmux string can be printed"""
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
        self.workday.load()
        self.assertEqual(
            self.workday.tmux_status(),
            '#[fg=red]04:30#[default] (03:30) | #[fg=red]04:30#[default] | #[fg=red]17:40#[default]',
        )

    def test_workday_status_string(self):
        """Test that the summary can be printed"""
        self.files.add_log(
            start_day=datetime(2018, 8, 17, 8, 0),
            start_lunch=datetime(2018, 8, 17, 11, 0),
            end_lunch=datetime(2018, 8, 17, 12, 0),
            end_day=datetime(2018, 8, 17, 16, 30),
        )
        self.files.add_log(
            start_day=datetime(2018, 8, 21, 8, 0),
            start_lunch=datetime(2018, 8, 21, 11, 0),
            end_lunch=datetime(2018, 8, 21, 12, 0),
            end_day=datetime(2018, 8, 21, 16, 50),
        )
        self.workday.load()
        self.assertEqual(
            self.workday.workday_status(),
            '''33
  Friday 07:30
  -----
  Total: 07:30
34
  Tuesday 07:50
  Wednesday 04:30
  -----
  Total: 12:20

Flex (until today): -00:40
Flex (leave now): -04:10
Zero flex at: 17:40
Full workday at: 17:00''',
        )

    def test_log(self):
        """Test that a day is logged"""
        self.workday.log_day()
        with open(self.workday.days_file) as file:
            lines = file.readlines()
            last = lines[-1]
        self.assertEqual(
            last,
            '1534917600 1534928400 1534932000 1534937400\n',
        )

    def test_log_empty(self):
        """Test that a day isn't logged if empty"""
        self.workday.set_config('start_day', 0)
        self.workday.set_config('start_lunch', 0)
        self.workday.set_config('end_lunch', 0)
        self.workday.set_config('end_day', 0)
        self.workday.log_day()
        with open(self.workday.days_file) as file:
            lines = file.readlines()
            try:
                last = lines[-1]
            except IndexError:
                last = None
        self.assertIsNone(last)

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

    @freeze_time("2018-08-22 13:30")
    def test_datetime_from_string(self):
        self.assertEqual(
            timestamp_from_string('15:15'),
            1534943700,
        )

@freeze_time("2018-08-22 13:30")
class TestDay(unittest.TestCase):
    def test_day_name(self):
        day = Day()
        self.assertEqual(
            day.day_name,
            'Wednesday',
        )

    def test_week(self):
        day = Day()
        self.assertEqual(
            day.week,
            34,
        )


if __name__ == '__main__':
    unittest.main()