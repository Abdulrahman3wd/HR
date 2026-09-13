"""
interview_slots.py
====================
Pure logic for generating available interview time slots from a window
(start time, end time, duration) minus any slots already booked for
the same interview_type + date across candidates.
"""

from datetime import datetime, timedelta


def generate_slots(window_start: str, window_end: str, duration_minutes: int) -> list[str]:
    """Returns a list of slot start times (HH:MM) within the window."""
    start = datetime.strptime(window_start, "%H:%M")
    end = datetime.strptime(window_end, "%H:%M")

    slots = []
    current = start
    while current + timedelta(minutes=duration_minutes) <= end:
        slots.append(current.strftime("%H:%M"))
        current += timedelta(minutes=duration_minutes)

    return slots


def get_available_slots(window_start: str, window_end: str, duration_minutes: int, booked_slots: list[str]) -> list[str]:
    all_slots = generate_slots(window_start, window_end, duration_minutes)
    return [s for s in all_slots if s not in booked_slots]