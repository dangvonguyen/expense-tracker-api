from enum import Enum


class ExpenseCategory(str, Enum):
    GROCERIES = "groceries"
    LEISURE = "leisure"
    ELECTRONICS = "electronics"
    UTILITIES = "utilities"
    CLOTHING = "clothing"
    HEALTH = "health"
    OTHER = "other"


class TimePeriod(str, Enum):
    DAY = ("day", 1)
    WEEK = ("week", 7)
    MONTH = ("month", 30)
    YEAR = ("year", 365)

    def __new__(cls, value: str, days: int):
        instance = super().__new__(cls)
        instance._value_ = value
        instance._days = days
        return instance

    def get_days(self) -> int:
        return self._days
