"""Utility functions for date and time rendering.

"""

import time
from datetime import datetime, UTC

from utilities.parameters import param


def utc_now_iso():
    return datetime.now(UTC).isoformat()


def sleep_to_avoid_quota_exceeding():
    time.sleep(param('sleep_time', float))
