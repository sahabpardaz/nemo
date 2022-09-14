from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from apps.utils.tests.utils import TestCaseUsingUtilsModels
from apps.utils.models.test_models import ModelWithUniqueField
from apps.utils import exception_utils


class ModelWithUniqueFieldSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'national_id']
        model = ModelWithUniqueField


class UniqueConstraintExcpetionDetectionTest(TestCaseUsingUtilsModels):
    def test_misc_exception_is_not_considered_as_unique_constraint(self):
        try:
            10 / 0
        except ZeroDivisionError as e:
            self.assertFalse(exception_utils.is_exception_about_unique_constraint(e))

    def test_model_save_error_is_detected(self):
        ModelWithUniqueField.objects.create(national_id='1')
        try:
            ModelWithUniqueField.objects.create(national_id='1')
        except IntegrityError as e:
            self.assertTrue(exception_utils.is_exception_about_unique_constraint(e))

    def test_serializer_save_error_is_detected(self):
        serializer = ModelWithUniqueFieldSerializer(data={'national_id': '1'})
        serializer.is_valid(raise_exception=True)
        ModelWithUniqueField.objects.create(national_id='1')
        try:
            serializer.save()
        except IntegrityError as e:
            self.assertTrue(exception_utils.is_exception_about_unique_constraint(e))

    def test_serializer_validation_error_is_detected(self):
        ModelWithUniqueField.objects.create(national_id='1')
        serializer = ModelWithUniqueFieldSerializer(data={'national_id': '1'})
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError as e:
            self.assertTrue(exception_utils.is_exception_about_unique_constraint(e))
