import django_filters
from django import forms
from .models import Machine, User, TechnicalService, Reclamation


class MachineFilter(django_filters.FilterSet):
    machine_model = django_filters.CharFilter(
        field_name='machine_model__name',
        lookup_expr='icontains',
        label='Модель техники'
    )
    engine_model = django_filters.CharFilter(
        field_name='engine_model__name',
        lookup_expr='icontains',
        label='Модель двигателя'
    )
    transmission_model = django_filters.CharFilter(
        field_name='transmission_model__name',
        lookup_expr='icontains',
        label='Модель трансмиссии'
    )
    drive_axle_model = django_filters.CharFilter(
        field_name='drive_axle_model__name',
        lookup_expr='icontains',
        label='Модель ведущего моста'
    )
    steering_axle_model = django_filters.CharFilter(
        field_name='steering_axle_model__name',
        lookup_expr='icontains',
        label='Модель управляемого моста'
    )

    class Meta:
        model = Machine
        fields = [
            'machine_model',
            'engine_model',
            'transmission_model',
            'drive_axle_model',
            'steering_axle_model',
        ]


class TechnicalServiceFilter(django_filters.FilterSet):
    service_type = django_filters.CharFilter(
        field_name='service_type__name',
        lookup_expr='icontains',
        label='Вид ТО'
    )
    machine_serial_number = django_filters.CharFilter(
        field_name='machine__serial_number',
        lookup_expr='icontains',
        label='Зав.номер машины'
    )

    class Meta:
        model = TechnicalService
        fields = [
            'service_type',
            'machine_serial_number',
        ]


class ReclamationFilter(django_filters.FilterSet):
    failure_node = django_filters.CharFilter(
        field_name='failure_node__name',
        lookup_expr='icontains',
        label='Узел отказа'
    )
    recovery_method = django_filters.CharFilter(
        field_name='recovery_method__name',
        lookup_expr='icontains',
        label='Способ восстановления'
    )

    class Meta:
        model = Reclamation
        fields = [
            'failure_node',
            'recovery_method',
        ]
