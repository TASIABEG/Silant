from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from .models import (
    MachineModel, EngineModel, TransmissionModel, DriveAxleModel,
    SteeringAxleModel, Machine, Component, Maintenance, ServiceType,
    ServiceOrganization, TechnicalService, FailureNode, RecoveryMethod,
    Reclamation, User
)

@admin.register(MachineModel)
class MachineModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(EngineModel)
class EngineModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(TransmissionModel)
class TransmissionModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(DriveAxleModel)
class DriveAxleModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(SteeringAxleModel)
class SteeringAxleModelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = (
        'serial_number',
        'machine_model',
        'client',
        'service_company',
        'shipment_date',
        'current_hours'
    )
    list_filter = ('machine_model', 'client', 'service_company')
    search_fields = ('serial_number', 'engine_serial', 'transmission_serial')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'serial_number',
                'machine_model',
                'current_hours'
            )
        }),
        ('Компоненты', {
            'fields': (
                'engine_model', 'engine_serial',
                'transmission_model', 'transmission_serial',
                'drive_axle_model', 'drive_axle_serial',
                'steering_axle_model', 'steering_axle_serial',
            )
        }),
        ('Поставка', {
            'fields': (
                'supply_contract',
                'shipment_date',
                'consignee',
                'delivery_address'
            )
        }),
        ('Эксплуатация', {
            'fields': (
                'equipment',
                'client',
                'service_company'
            )
        }),
        ('Системная информация', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.role == 'manager':
            return qs
        elif user.role == 'client':
            return qs.filter(client=user)
        elif user.role == 'service':
            return qs.filter(service_company=user)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return request.user.can_edit_machines()

    def has_add_permission(self, request):
        return request.user.can_edit_machines()


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'part_number', 'machine', 'wear_percentage')
    readonly_fields = ('wear_percentage',)
    list_select_related = ('machine',)


@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('machine', 'type', 'start_date', 'end_date', 'service_company')
    list_filter = ('type', 'service_company')
    list_select_related = ('machine', 'service_company')


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(ServiceOrganization)
class ServiceOrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'contact_phone')
    search_fields = ('name', 'address')


@admin.register(TechnicalService)
class TechnicalServiceAdmin(admin.ModelAdmin):
    list_display = (
        'machine',
        'service_type',
        'service_date',
        'operating_hours',
        'service_organization',
        'service_company'
    )
    list_filter = ('service_type', 'service_organization', 'service_company')
    search_fields = ('work_order_number', 'machine__serial_number')
    date_hierarchy = 'service_date'

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'machine',
                'service_type',
                'service_date',
                'operating_hours'
            )
        }),
        ('Документы', {
            'fields': (
                'work_order_number',
                'work_order_date',
            )
        }),
        ('Организации', {
            'fields': (
                'service_organization',
                'service_company',
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return TechnicalService.get_visible_to_user(request.user)

    def has_change_permission(self, request, obj=None):
        if obj:
            return obj.can_be_edited_by(request.user)
        return super().has_change_permission(request, obj)


@admin.register(FailureNode)
class FailureNodeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(RecoveryMethod)
class RecoveryMethodAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Reclamation)
class ReclamationAdmin(admin.ModelAdmin):
    list_display = [
        'machine', 'failure_date', 'operating_hours',
        'failure_node', 'recovery_method', 'service_company',
        'downtime_display'
    ]
    list_filter = ['service_company', 'failure_node', 'recovery_method']
    search_fields = ['machine__serial_number', 'failure_description', 'spare_parts_used']
    readonly_fields = ['downtime_display']

    fields = [
        'machine',
        'failure_date',
        'operating_hours',
        'failure_node',
        'failure_description',
        'recovery_method',
        'spare_parts_used',
        'recovery_date',
        'service_company',
        'downtime_display',
    ]

    def downtime_display(self, obj):
        """Отображение времени простоя в днях"""
        return obj.downtime or '-'
    downtime_display.short_description = "Простой (дни)"


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    change_password_form = AdminPasswordChangeForm

    list_display = ('username', 'role', 'company', 'is_active')
    list_filter = ('role', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'email', 'company', 'phone')
        }),
        ('Права доступа', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'company'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if 'password' in form.cleaned_data:
            obj.set_password(form.cleaned_data['password'])
        super().save_model(request, obj, form, change)
