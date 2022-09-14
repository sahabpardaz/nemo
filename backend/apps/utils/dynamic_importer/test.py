import sys
from contextlib import contextmanager
from io import StringIO
from django.test import TestCase
from apps.utils.dynamic_importer import scan


@contextmanager
def capture_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class DynamicImporterScannerTest(TestCase):
    def test_calling_normal_import_and_scan_method_together_should_load_modules_once(self):
        with capture_output() as (out, err):

            import apps.utils.dynamic_importer.test_files.module
            scan('apps.utils.dynamic_importer.test_files')

            output = out.getvalue().strip()
            self.assertEqual(output.count('run'), 1)
