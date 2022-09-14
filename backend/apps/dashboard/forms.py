from django import forms
from apps.dashboard.models import EvaluationType, CoverageReport


class EvaluationTypeForm(forms.ModelForm):
    class Meta:
        model = EvaluationType
        fields = ['kind', 'validity_period_days', 'checking_period_days']

    def clean_kind(self):
        kind = self.cleaned_data['kind']
        EvaluationType.validate_kind_uniqueness(kind, self.instance.pk)
        return kind


class CoverageReportForm(forms.ModelForm):
    class Meta:
        model = CoverageReport
        fields = '__all__'

    def clean(self):
        CoverageReport.validate_version_and_coverage_type_uniqueness_in_project(
            old_instance=CoverageReport.objects.get(pk=self.instance.pk) if self.instance.pk else None,
            new_project=self.cleaned_data['project'],
            new_coverage_type=self.cleaned_data['coverage_type'],
            new_version=self.cleaned_data['version'],
        )
        return super().clean()
