import binascii
import os
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import models
from hitcount.models import HitCountMixin
from fernet_fields import EncryptedTextField
from model_utils import FieldTracker
from apps.dashboard.constants import DEFAULT_BRANCH_MAX_LENGTH
from apps.dashboard.models.maturity_model import MaturityModel


class Project(models.Model, HitCountMixin):
    name = models.CharField(
        max_length=500,
        unique=True,
    )
    maturity_model = models.ForeignKey(
        MaturityModel,
        on_delete=models.PROTECT,
    )
    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    default_environment = models.OneToOneField(
        'Environment',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='project_as_default_environment',
        #limit_choices_to="I wish I could use this!",
    )

    tracker = FieldTracker(fields=['name'])

    @property
    def default_environment_name(self):
        default_env = self.default_environment
        return default_env.name if default_env is not None else None

    @property
    def creator_username(self):
        return self.creator.username if hasattr(self, 'creator') else None

    def save(self, *args, **kwargs):
        # I wish I could use 'limit_choices_to' instead of this!
        default_env = self.default_environment
        if default_env is not None and default_env.project.id != self.id:
            raise ValidationError("The default environment is not an environment of this project.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProjectAPIToken(models.Model):
    project = models.OneToOneField(
        Project,
        related_name='auth_token',
        on_delete=models.CASCADE,
    )
    key = models.CharField(
        max_length=40,
        primary_key=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key


class GitlabProject(models.Model):
    nemo_project = models.OneToOneField(
        Project,
        related_name='version_control',
        on_delete=models.CASCADE,
    )
    project_id = models.IntegerField(
        blank=True,
        null=True,
    )
    token = models.CharField(
        max_length=40,
        blank=True,
    )
    default_branch = models.CharField(
        max_length=DEFAULT_BRANCH_MAX_LENGTH,
        blank=True,
    )


class SonarProject(models.Model):
    COVERAGE_BRANCH_MAX_LENGTH = 200
    COVERAGE_BRANCH_DEFAULT_VALUE = 'master'
    PROJECT_KEY_MAX_LENGTH = 127
    API_BASE_URL_MAX_LENGTH = 127
    AUTH_TOKEN_LENGTH = 40

    nemo_project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='sonarprojects',
    )
    api_base_url = models.CharField(max_length=API_BASE_URL_MAX_LENGTH,
                                    help_text="E.g. https://sonarqube.com/api")
    project_key = models.CharField(max_length=PROJECT_KEY_MAX_LENGTH)
    auth_token = models.CharField(max_length=AUTH_TOKEN_LENGTH,
                                  null=True,
                                  blank=True)
    coverage_branch = models.CharField(
        help_text="The branch that the coverage data reporting with",
        max_length=COVERAGE_BRANCH_MAX_LENGTH,
        default=COVERAGE_BRANCH_DEFAULT_VALUE,
        null=False,
        blank=True,
    )

class GitRepo(models.Model):
    DEFAULT_BRANCH_MAX_LENGTH = 40
    DEFAULT_BRANCH_DEFAULT = 'master'
    USER_PASS_MAX_LENGTH = 100
    GIT_ECOSYSTEM_GITLAB = 'GL'
    GIT_ECOSYSTEM_GITHUB = 'GH'
    GIT_ECOSYSTEM_GERRIT = 'GR'
    GIT_ECOSYSTEM_OTHER = 'O'
    GIT_ECOSYSTEM_CHOICES = (
        (GIT_ECOSYSTEM_GITLAB, 'GitLab'),
        (GIT_ECOSYSTEM_GITHUB, 'GitHub'),
        (GIT_ECOSYSTEM_GERRIT, 'Gerrit'),
        (GIT_ECOSYSTEM_OTHER, 'Other...'),
    )

    nemo_project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='gitrepo'
    )
    git_http_url = models.URLField(
        help_text="E.g. https://gitlab.com/group/project.git"
    )
    default_branch = models.CharField(
        max_length=DEFAULT_BRANCH_MAX_LENGTH,
        default=DEFAULT_BRANCH_DEFAULT
    )
    username = models.CharField(
        max_length=USER_PASS_MAX_LENGTH,
        null=True,
        blank=True,
    )
    password = EncryptedTextField(
        null=True,
        blank=True,
    )
    git_ecosystem = models.CharField(
        max_length=2,
        choices=GIT_ECOSYSTEM_CHOICES,
        default=GIT_ECOSYSTEM_OTHER
    )
    changelist_collection_enabled = models.BooleanField(null=False, default=False)
