def get_readable_time_from_seconds(seconds: int, granularity=2) -> str:
    intervals = (
        ('months', 2628000),
        ('days', 86400),
        ('hours', 3600),
        ('minutes', 60),
        ('seconds', 1),
    )
    result = []

    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip('s')
            result.append(f"{value} {name}")
    return ', '.join(result[:granularity])


def get_percentage_from_float(value: float) -> str:
    return '{0:.2f} %'.format(value)
