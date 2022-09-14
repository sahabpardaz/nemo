from django.contrib import admin
from rangefilter.filter import DateRangeFilter
from apps.devops_metrics.models import \
    ChangeList, Deployment, ServiceStatusReport
from apps.devops_metrics.forms import DeploymentForm, ChangeListForm


@admin.register(ChangeList)
class ChangeListAdmin(admin.ModelAdmin):
    form = ChangeListForm
    list_display = ('id', 'title', 'project', 'change_list_id', 'commit_hash', 'time')
    list_filter = (('time', DateRangeFilter), 'project')
    search_fields = ('commit_hash', 'title',)


@admin.register(Deployment)
class DeploymentAdmin(admin.ModelAdmin):
    form = DeploymentForm
    list_display = ('id', 'get_project', 'environment', 'status',
                    'time', 'change_list', 'get_commit_hash_of_change_list')
    list_filter = (('time', DateRangeFilter), 'environment__project', 'status')
    search_fields = ('change_list__commit_hash',)

    def get_project(self, obj):
        return obj.environment.project
    get_project.short_description = 'Project'

    def get_commit_hash_of_change_list(self, obj):
        return obj.change_list.commit_hash
    get_commit_hash_of_change_list.short_description = 'Commit hash'


@admin.register(ServiceStatusReport)
class ServiceStatusReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_project', 'environment', 'status', 'time')
    list_filter = (('time', DateRangeFilter), 'environment__project', 'status')

    def get_project(self, obj):
        return obj.environment.project
    get_project.short_description = 'Project'
