from django.db import models


class ModelWithUniqueField(models.Model):
    NATIONAL_ID_MAX_LENGTH = 100

    national_id = models.CharField(max_length=NATIONAL_ID_MAX_LENGTH, unique=True)
