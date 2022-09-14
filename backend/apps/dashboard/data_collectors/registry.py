data_collector_registry = set()


def register():
    """Simple class decorator to register data collector classes."""
    def decorator(klass):
        data_collector_registry.add(klass)
        return klass
    return decorator
