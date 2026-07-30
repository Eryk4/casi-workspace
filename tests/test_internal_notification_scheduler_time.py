from __future__ import annotations

import unittest
from datetime import date, datetime, timezone

from app.domain.internal_notification_schedule import (
    calculate_next_run_at_utc,
    occurrence_for_due_schedule,
    scheduled_local_datetime_utc,
)


UTC = timezone.utc


class InternalNotificationSchedulerTimeTests(unittest.TestCase):
    def test_before_and_after_local_time_select_today_or_tomorrow(self) -> None:
        before = calculate_next_run_at_utc(
            enabled=True,
            local_time="08:00",
            timezone_name="Europe/Warsaw",
            now_utc=datetime(2026, 1, 15, 6, 30, tzinfo=UTC),
        )
        after = calculate_next_run_at_utc(
            enabled=True,
            local_time="08:00",
            timezone_name="Europe/Warsaw",
            now_utc=datetime(2026, 1, 15, 8, 30, tzinfo=UTC),
        )
        self.assertEqual(before, "2026-01-15T07:00:00+00:00")
        self.assertEqual(after, "2026-01-16T07:00:00+00:00")
        self.assertIsNone(calculate_next_run_at_utc(
            enabled=False,
            local_time="08:00",
            timezone_name="Europe/Warsaw",
            now_utc=datetime(2026, 1, 15, 6, 30, tzinfo=UTC),
        ))

    def test_warsaw_winter_summer_and_local_as_of_date(self) -> None:
        winter = scheduled_local_datetime_utc(date(2026, 1, 15), "08:00", "Europe/Warsaw")
        summer = scheduled_local_datetime_utc(date(2026, 7, 15), "08:00", "Europe/Warsaw")
        self.assertEqual(winter.isoformat(), "2026-01-15T07:00:00+00:00")
        self.assertEqual(summer.isoformat(), "2026-07-15T06:00:00+00:00")
        occurrence = occurrence_for_due_schedule(
            local_time="23:30",
            timezone_name="Europe/Warsaw",
            now_utc=datetime(2026, 7, 15, 22, 10, tzinfo=UTC),
        )
        self.assertEqual(occurrence.as_of_date, "2026-07-16")
        self.assertEqual(occurrence.scheduled_local_date, "2026-07-16")

    def test_dst_gap_moves_forward_and_overlap_uses_first_occurrence(self) -> None:
        spring = scheduled_local_datetime_utc(date(2026, 3, 29), "02:30", "Europe/Warsaw")
        autumn = scheduled_local_datetime_utc(date(2026, 10, 25), "02:30", "Europe/Warsaw")
        self.assertEqual(spring.isoformat(), "2026-03-29T01:00:00+00:00")
        self.assertEqual(autumn.isoformat(), "2026-10-25T00:30:00+00:00")

    def test_last_success_prevents_second_run_on_same_local_date(self) -> None:
        result = calculate_next_run_at_utc(
            enabled=True,
            local_time="18:00",
            timezone_name="Europe/Warsaw",
            now_utc=datetime(2026, 7, 15, 8, 0, tzinfo=UTC),
            last_succeeded_local_date="2026-07-15",
        )
        self.assertEqual(result, "2026-07-16T16:00:00+00:00")

    def test_invalid_time_and_timezone_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_next_run_at_utc(enabled=True, local_time="24:00", timezone_name="Europe/Warsaw", now_utc=datetime.now(UTC))
        with self.assertRaises(ValueError):
            calculate_next_run_at_utc(enabled=True, local_time="08:00", timezone_name="Mars/Olympus", now_utc=datetime.now(UTC))


if __name__ == "__main__":
    unittest.main()
