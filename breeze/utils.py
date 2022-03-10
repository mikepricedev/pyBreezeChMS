from datetime import date, datetime
import json
from typing import Union
from .breeze_types import AccountLogActions


def datetime_to_date(date: Union[date, datetime]) -> date:
    if isinstance(date, datetime):
        return date.date()
    else:
        return date


class JSONSerial(json.JSONEncoder):
    """Adds ISO date serialization for datetime and date objects."""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, AccountLogActions):
            return obj.name
        else:
            return json.JSONEncoder.default(self, obj)
