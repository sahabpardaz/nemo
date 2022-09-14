from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from guardian.admin import GuardedModelAdmin
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from ordered_model.admin import OrderedInlineModelAdminMixin
from rangefilter.filter import DateRangeFilter
from apps.dashboard.forms import EvaluationTypeForm, CoverageReportForm
from apps.dashboard.models import (
    Project,
    Environment,
    MaturityModel,
    MaturityModelLevel,
    MaturityModelItem,
    EvaluationReport,
    EvaluationRequest,
    ProjectAPIToken,
    GitlabProject,
    SonarProject,
    Goal,
    EvaluationType,
    CoverageReport,
    MaturityModelItemToggleRequest,
    MaturityModelItemToggleApproval,
    GitRepo,
    DoryEvaluation,
    UserProjectNotifSetting,
)
from apps.utils.ordered_model_improvement import ImprovedOrderedInlineMixin


class CustomizedUserAdmin(UserAdmin):
    list_filter = UserAdmin.list_filter + ('date_joined',)
    ordering = ('-date_joined',)


admin.site.unregister(User)
admin.site.register(User, CustomizedUserAdmin)


class MaturityModelItemInline(ImprovedOrderedInlineMixin, NestedStackedInline):
    model = MaturityModelItem
    fields = (
        'code',
        'name',
        'description',
        ('acceptable_value', 'acceptable_value_type'),
        'evaluation_type',
        ('order', 'move_up_down_links'),
    )
    readonly_fields = ('order', 'move_up_down_links',)
    extra = 1
    ordering = ('order',)


class MaturityModelLevelInline(OrderedInlineModelAdminMixin, ImprovedOrderedInlineMixin, NestedStackedInline):
    model = MaturityModelLevel
    fields = (
        'name',
        'description',
        ('order', 'move_up_down_links'),
    )
    readonly_fields = ('order', 'move_up_down_links',)
    extra = 1
    ordering = ('order',)
    inlines = (MaturityModelItemInline,)


@admin.register(MaturityModel)
class MaturityModelAdmin(OrderedInlineModelAdminMixin, NestedModelAdmin):
    list_display = ('name', 'levels_count', 'items_count')
    search_fields = ("MaturityModel__name",)
    inlines = (MaturityModelLevelInline,)

    def levels_count(self, obj):
        return obj.levels.count()

    def items_count(self, obj):
        return obj.levels \
            .aggregate(number_of_items=Count('items')).get('number_of_items')

    levels_count.short_description = "Levels count"
    items_count.short_description = "Items count"


@admin.register(EvaluationReport)
class EvaluationReportAdmin(admin.ModelAdmin):
    list_display = (
        'maturity_model_item',
        'project',
        'status',
        'creation_time',
        'last_update_time',
        'latest_evaluation_time',
        'current_value',
        'expected_value',
        'reporter',
    )
    readonly_fields = (
        'creation_time',
        'last_update_time',
        'latest_evaluation_time',
    )
    list_filter = (
        'status',
        'project',
        'maturity_model_item',
        ('creation_time', DateRangeFilter),
        ('last_update_time', DateRangeFilter),
        ('latest_evaluation_time', DateRangeFilter),
    )


@admin.register(EvaluationRequest)
class EvaluationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'maturity_model_item',
                    'status', 'time', 'applicant')
    list_filter = ('project', 'maturity_model_item',
                   'status', ('time', DateRangeFilter))
    raw_id_fields = ('closing_report',)


class EnvironmentInline(admin.TabularInline):
    model = Environment
    fields = (
        'name',
        'is_default_in_project',
    )
    readonly_fields = ('is_default_in_project',)
    extra = 1


@admin.register(Project)
class ProjectAdmin(GuardedModelAdmin):
    list_display = ('id', 'name', 'maturity_model',
                    'default_environment', 'creator')
    list_filter = ('maturity_model',)
    search_fields = ('name',)
    inlines = (EnvironmentInline,)

    def get_form(self, request, obj=None, **kwargs):
        # I wish I could use 'limit_choices_to' instead of this method!
        form = super().get_form(request, obj, **kwargs)
        env_qs = getattr(form.base_fields['default_environment'], 'queryset', None)
        if env_qs is None:
            env_qs = Environment.objects
        env_qs = env_qs.none() if obj is None else env_qs.filter(project=obj)
        form.base_fields['default_environment'].queryset = env_qs
        return form


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'project', 'is_default_in_project',)
    list_filter = ('project',)
    search_fields = ('name',)


@admin.register(ProjectAPIToken)
class ProjectAPITokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'project', 'created')
    fields = ('project',)
    ordering = ('-created',)
    search_fields = ('project__name',)


@admin.register(GitlabProject)
class GitlabProjectAdmin(admin.ModelAdmin):
    list_display = ('nemo_project',)
    search_fields = ('nemo_project__name',)


@admin.register(SonarProject)
class SonarProjectAdmin(admin.ModelAdmin):
    list_display = ('nemo_project', 'project_key', 'api_base_url')
    list_filter = ('nemo_project', 'project_key', 'api_base_url')
    search_fields = ('nemo_project__name', 'project_key')


@admin.register(Goal)
class GoalAdmin(GuardedModelAdmin):
    fields = (
        'id',
        'project',
        'due_date',
        'maturity_model_items',
        ('creation_time', 'last_update_time'),
        'status',
    )
    readonly_fields = (
        'id',
        'creation_time',
        'last_update_time',
        'status',
    )
    list_display = (
        'id',
        'project',
        'due_date',
        'creation_time',
        'last_update_time',
        'status',
    )
    list_filter = (
        'project',
        ('due_date', DateRangeFilter),
        ('creation_time', DateRangeFilter),
        ('last_update_time', DateRangeFilter),
    )
    search_fields = (
        'project__name',
    )


@admin.register(CoverageReport)
class CoverageReportAdmin(admin.ModelAdmin):
    form = CoverageReportForm
    list_display = ('project', 'value', 'coverage_type', 'creation_time', 'last_update_time', 'version')
    list_filter = ('project', 'value', 'coverage_type', ('creation_time', DateRangeFilter), ('last_update_time', DateRangeFilter))
    search_fields = ('project__name', 'version')


@admin.register(EvaluationType)
class EvaluationTypeAdmin(admin.ModelAdmin):
    form = EvaluationTypeForm
    fields = ['kind', 'validity_period_days', 'checking_period_days']
    list_display = ('kind', 'validity_period_days', 'checking_period_days')
    list_filter = ('kind',)


class MaturityModelItemToggleApprovalInline(admin.StackedInline):
    model = MaturityModelItemToggleApproval
    readonly_fields = ['creation_time']


class HasApprovalFilter(admin.SimpleListFilter):
    title = 'approval'
    parameter_name = 'has_approval'

    def lookups(self, request, model_admin):
        return (
            ('True', 'has approval'),
            ('False', 'has no approval'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(approval__isnull=False)
        if self.value() == 'False':
            return queryset.filter(approval__isnull=True)


@admin.register(MaturityModelItemToggleRequest)
class MaturityModelItemToggleAdmin(admin.ModelAdmin):
    inlines = [MaturityModelItemToggleApprovalInline]
    readonly_fields = ['creation_time']
    list_display = [
        'project',
        'maturity_model_item',
        'creation_time',
        'disable',
        'is_approved',
    ]
    list_filter = [
        'project',
        'maturity_model_item',
        'disable',
        HasApprovalFilter,
    ]
    actions = [
        'approve_maturity_model_item_toggle_requests',
        'refuse_maturity_model_item_toggle_requests',
    ]

    @staticmethod
    def handle_maturity_model_item_toggle_requests(request, queryset, approved):
        for toggle_request in queryset:
            if hasattr(toggle_request, 'approval'):
                if toggle_request.approval.approved == approved:
                    continue

                toggle_request.approval.delete()

            MaturityModelItemToggleApproval.objects.create(
                maturity_model_item_toggle_request_id=toggle_request.id,
                user=request.user,
                approved=approved,
            )

    def approve_maturity_model_item_toggle_requests(self, request, queryset):
        self.handle_maturity_model_item_toggle_requests(request, queryset, True)

    approve_maturity_model_item_toggle_requests.short_description = "Approve selected requests"

    def refuse_maturity_model_item_toggle_requests(self, request, queryset):
        self.handle_maturity_model_item_toggle_requests(request, queryset, False)

    refuse_maturity_model_item_toggle_requests.short_description = "Refuse selected requests"

    def is_approved(self, obj):
        return obj.approval.approved

    is_approved.short_description = is_approved.admin_order_field = 'Approved'


@admin.register(GitRepo)
class GitRepoAdmin(admin.ModelAdmin):
    list_display = ('nemo_project', 'default_branch', 'git_http_url')
    list_filter = ('nemo_project__name',)


@admin.register(DoryEvaluation)
class DoryEvaluationAdmin(admin.ModelAdmin):
    list_filter = ('project__name',)
    list_display = ('project', 'submission_time', 'first_completed_poll_time', 'evaluation_approximated_duration')

    def evaluation_approximated_duration(self, obj):
        if not obj.first_completed_poll_time:
            return None

        return obj.first_completed_poll_time - obj.submission_time

    evaluation_approximated_duration.short_description = "Approximated Duration"


@admin.register(UserProjectNotifSetting)
class UserProjectNotifSettingAdmin(admin.ModelAdmin):
    list_filter = ('project', 'user', 'receive_notifications')
    list_display = ('project', 'user', 'receive_notifications')
