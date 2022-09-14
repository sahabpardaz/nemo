from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestForwardMigration(MigratorTestCase):
    migrate_from = ('dashboard', '0001_initial')
    migrate_to = ('dashboard', '0002_quality_committee_group')

    def _pre_setup(self):
        # Because the ContentType cache needs to be cleared before running tests.
        # For more details see: https://code.djangoproject.com/ticket/10827
        # It may be fixed in newer Django releases.
        ContentType.objects.clear_cache()
        super()._pre_setup()

    def prepare(self):
        self.assertEqual(Group.objects.count(), 0)

    def test_quality_committee_group_should_be_created(self):
        self.assertEqual(Group.objects.count(), 1)


class TestBackwardMigration(MigratorTestCase):
    migrate_from = ('dashboard', '0002_quality_committee_group')
    migrate_to = ('dashboard', '0001_initial')

    def _pre_setup(self):
        # Because the ContentType cache needs to be cleared before running tests.
        # For more details see: https://code.djangoproject.com/ticket/10827
        # It may be fixed in newer Django releases.
        ContentType.objects.clear_cache()
        super()._pre_setup()

    def prepare(self):
        self.assertEqual(Group.objects.count(), 1)

    def test_quality_committee_group_should_be_deleted(self):
        self.assertEqual(Group.objects.count(), 0)
