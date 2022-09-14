from django import forms
from apps.devops_metrics.models import Deployment, ChangeList


class DeploymentForm(forms.ModelForm):
    class Meta:
        model = Deployment
        fields = ['environment', 'change_list', 'status', 'time']

    def clean(self):
        environment = self.cleaned_data.get('environment')
        change_list = self.cleaned_data.get('change_list')
        if environment.project != change_list.project:
            raise forms.ValidationError(Deployment.VALIDATION_ERROR_NOT_SAME_PROJECT_IN_CHANGE_LIST_AND_ENVIRONMENT)
        return self.cleaned_data


class ChangeListForm(forms.ModelForm):
    class Meta:
        model = ChangeList
        fields = ['project', 'change_list_id', 'title', 'commit_hash', 'time']

    def clean(self):
        ChangeList.validate_unique_fields(
            old_instance=ChangeList.objects.get(pk=self.instance.pk) if self.instance.pk else None,
            new_project=self.cleaned_data['project'],
            new_change_list_id=self.cleaned_data['change_list_id'],
            new_commit_hash=self.cleaned_data['commit_hash'],
        )
        return self.cleaned_data
