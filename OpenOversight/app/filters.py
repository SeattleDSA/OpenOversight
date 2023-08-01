"""Contains all templates filters."""
from datetime import datetime

import pytz as pytz
from flask import Flask, session

from OpenOversight.app.utils.constants import KEY_TIMEZONE


def instantiate_filters(app: Flask):
    """Instantiate all template filters"""

    def get_timezone() -> str:
        """Return the applicable timezone for the filter."""
        return (
            session[KEY_TIMEZONE]
            if KEY_TIMEZONE in session
            else app.config.get(KEY_TIMEZONE)
        )

    @app.template_filter("capfirst")
    def capfirst_filter(s: str) -> str:
        return s[0].capitalize() + s[1:]  # only change 1st letter

    @app.template_filter("get_age")
    def get_age_from_birth_year(birth_year) -> int:
        if birth_year:
            return int(datetime.now(pytz.timezone(get_timezone())).year - birth_year)

    @app.template_filter("field_in_query")
    def field_in_query(form_data, field):
        """
        Determine if a field is specified in the form data, and if so return a Bootstrap
        class which will render the field accordion open.
        """
        return " in " if form_data.get(field) else ""

    @app.template_filter("local_date")
    def local_date(value: datetime) -> str:
        """Convert UTC datetime.datetime into a localized date string."""
        return value.astimezone(pytz.timezone(get_timezone())).strftime("%b %d, %Y")

    @app.template_filter("local_date_time")
    def local_date_time(value: datetime) -> str:
        """Convert UTC datetime.datetime into a localized date time string."""
        return value.astimezone(pytz.timezone(get_timezone())).strftime(
            "%I:%M %p on %b %d, %Y"
        )

    @app.template_filter("local_time")
    def local_time(value: datetime) -> str:
        """Convert UTC datetime.datetime into a localized time string."""
        return value.astimezone(pytz.timezone(get_timezone())).strftime("%I:%M %p")

    @app.template_filter("thousands_seperator")
    def thousands_seperator(value: int) -> str:
        """Convert int to string with the appropriately applied commas."""
        return f"{value:,}"
