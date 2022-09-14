import datetime
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, compat


class TimestampField(serializers.Field):
    """
    https://gist.github.com/arkanister/e45a91c1d77bc4ed40e57d14c7644cb2
    """

    default_error_messages = {
        'invalid': _('Datetime has wrong format. Use one of these formats instead: {format}.'),
        'date': _('Expected a datetime but got a date.'),
        'make_aware': _('Invalid datetime for the timezone "{timezone}".'),
        'overflow': _('Datetime value out of range.')
    }

    def __init__(self, default_timezone=None, *args, **kwargs):
        self._timezone = default_timezone
        super().__init__(*args, **kwargs)

    @property
    def timezone(self):
        if not settings.USE_TZ:
            return None

        return self._timezone or timezone.get_current_timezone()

    def enforce_timezone(self, value):
        """
        When `self.timezone` is `None`, always return naive datetimes.
        When `self.timezone` is not `None`, always return aware datetimes.
        """
        field_timezone = self.timezone

        if field_timezone is not None:
            if timezone.is_aware(value):
                try:
                    return value.astimezone(field_timezone)
                except OverflowError:
                    self.fail('overflow')
            try:
                return timezone.make_aware(value, field_timezone)
            except compat.InvalidTimeError:
                self.fail('make_aware', timezone=field_timezone)

        elif (field_timezone is None) and timezone.is_aware(value):
            return timezone.make_naive(value, timezone.utc)
        return value

    def to_internal_value(self, value):
        if not value:
            return None

        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            self.fail('date')

        if isinstance(value, datetime.datetime):
            return self.enforce_timezone(value)

        try:
            value = float(value)

        except (TypeError, ValueError):
            self.fail('invalid')

        dt_value = None

        for value in [value, value / 1e3]:
            try:
                dt_value = datetime.datetime.utcfromtimestamp(value)

            except (TypeError, ValueError):
                continue

            else:
                break

        if not dt_value:
            self.fail('invalid')

        return self.enforce_timezone(dt_value)

    def to_representation(self, value):
        if not value:
            return None

        value = self.enforce_timezone(value)

        return datetime.datetime.timestamp(value)
