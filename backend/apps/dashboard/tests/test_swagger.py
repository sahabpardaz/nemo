from django.test import TestCase
from rest_framework import status


class SwaggerTest(TestCase):
    def test_swagger_ui_should_return_ok_status(self):
        response = self.client.get('/v1/documentation/swagger/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_openapi_data_should_return_ok_status(self):
        response = self.client.get('/v1/documentation/swagger/?format=openapi')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
