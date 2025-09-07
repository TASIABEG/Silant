from django import forms
from .models import Machine, TechnicalService, Reclamation, Reference

class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = '__all__'
        widgets = {
            'shipment_date': forms.DateInput(attrs={'type': 'date'}),
            'created_at': forms.DateTimeInput(attrs={'disabled': True}),
            'updated_at': forms.DateTimeInput(attrs={'disabled': True}),
        }

class TechnicalServiceForm(forms.ModelForm):
    class Meta:
        model = TechnicalService
        fields = '__all__'
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date'}),
            'work_order_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        machine = kwargs.pop('machine', None)
        super().__init__(*args, **kwargs)
        if machine:
            self.fields['machine'].initial = machine
            self.fields['machine'].widget = forms.HiddenInput()

class ReclamationForm(forms.ModelForm):
    class Meta:
        model = Reclamation
        fields = [
            'failure_date',
            'operating_hours',
            'failure_node',
            'failure_description',
            'recovery_method',
            'spare_parts_used',
            'recovery_date',
            'service_company',
        ]
        widgets = {
            'failure_date': forms.DateInput(attrs={'type': 'date'}),
            'recovery_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = ['name', 'description']