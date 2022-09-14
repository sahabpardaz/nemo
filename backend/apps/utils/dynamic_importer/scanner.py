import importlib
import pkgutil


def scan(namespace):
    """
        Scans the namespace for modules and imports them.
        Usage:
            - Activate register decorators

        https://play.pixelblaster.ro/blog/2017/12/18/a-quick-and-dirty-mini-plugin-system-for-python/
    """
    name = importlib.util.resolve_name(namespace, package=__package__)
    spec = importlib.util.find_spec(name)

    if spec is not None:
        module = importlib.util.module_from_spec(spec)
        importlib.import_module(module.__name__)

        for finder, name, ispkg in pkgutil.iter_modules(module.__path__, prefix=module.__name__ + '.'):
            spec = finder.find_spec(name)
            module = importlib.util.module_from_spec(spec)
            importlib.import_module(module.__name__)
