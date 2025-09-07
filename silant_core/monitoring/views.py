from django.views.generic import DetailView, ListView, UpdateView, CreateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django_filters.views import FilterView
from django.contrib.auth.views import LoginView, LogoutView
from .models import Machine, User, TechnicalService, Reclamation, Reference
from .forms import MachineForm, TechnicalServiceForm, ReclamationForm, ReferenceForm
from .filters import MachineFilter, TechnicalServiceFilter, ReclamationFilter

# ======================== MACHINES ========================
class MachineListView(LoginRequiredMixin, FilterView):
    model = Machine
    template_name = 'monitoring/machine_list.html'
    context_object_name = 'machine_list'
    filterset_class = MachineFilter
    paginate_by = 10

    def get_queryset(self):
        queryset = self.request.user.get_accessible_machines().order_by('-shipment_date')
        self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        context['total_machines'] = self.request.user.get_accessible_machines().count()
        context['in_service'] = sum(1 for machine in context['object_list'] if machine.in_service)
        return context


class MachineDetailView(LoginRequiredMixin, DetailView):
    model = Machine
    template_name = 'monitoring/machine_detail.html'
    context_object_name = 'machine'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        machine = self.object
        user = self.request.user

        # Проверка прав для добавления и редактирования
        context['can_edit_machine'] = user.can_edit_machines()
        context['can_add_service'] = user.role in ['service', 'manager']
        context['can_add_reclamation'] = user.role in ['service', 'manager']

        # ТО с проверкой прав редактирования
        technical_services = TechnicalService.get_visible_to_user(user).filter(machine=machine).order_by('-service_date')
        context['to_with_permissions'] = [
            {
                'object': ts,
                'can_edit': user.role in ['service', 'manager']
            } for ts in technical_services
        ]

        # Рекламации с проверкой прав редактирования
        reclamations = Reclamation.get_visible_to_user(user).filter(machine=machine).order_by('-failure_date')
        context['reclamations_with_permissions'] = [
            {
                'object': r,
                'can_edit': r.can_be_edited_by(user)
            } for r in reclamations
        ]

        return context


class MachineCreateView(LoginRequiredMixin, CreateView):
    model = Machine
    form_class = MachineForm
    template_name = 'monitoring/machine_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.can_edit_machines():
            messages.error(request, "У вас нет прав для добавления машин")
            return redirect('monitoring:machine_list')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('monitoring:machine_detail', kwargs={'pk': self.object.pk})


class MachineUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Machine
    form_class = MachineForm
    template_name = 'monitoring/machine_form.html'

    def test_func(self):
        return self.request.user.can_edit_machines()

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для редактирования машин")
        return redirect('monitoring:machine_list')

    def get_success_url(self):
        return reverse('monitoring:machine_detail', kwargs={'pk': self.object.pk})


class MachineSearchView(TemplateView):
    template_name = 'monitoring/machine_search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        serial_number = self.request.GET.get('serial_number', '').strip()
        machine = None
        if serial_number:
            try:
                machine = Machine.objects.get(serial_number=serial_number)
            except Machine.DoesNotExist:
                pass
        context['serial_number'] = serial_number
        context['machine'] = machine
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('monitoring:machine_list')
        return super().get(request, *args, **kwargs)


# ======================== AUTH ========================
class CustomLoginView(LoginView):
    template_name = 'monitoring/login.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Добро пожаловать, {self.request.user.username}!")
        return response


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('monitoring:login')

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, "Вы успешно вышли из системы")
        return super().dispatch(request, *args, **kwargs)


# ======================== TECHNICAL SERVICE ========================
class TechnicalServiceListView(LoginRequiredMixin, FilterView):
    model = TechnicalService
    template_name = 'monitoring/technical_service_list.html'
    filterset_class = TechnicalServiceFilter
    context_object_name = 'technical_service_list'

    def get_queryset(self):
        return TechnicalService.get_visible_to_user(self.request.user).order_by('-service_date')


class TechnicalServiceDetailView(LoginRequiredMixin, DetailView):
    model = TechnicalService
    template_name = 'monitoring/technical_service_detail.html'
    context_object_name = 'service'


class TechnicalServiceCreateView(LoginRequiredMixin, CreateView):
    model = TechnicalService
    form_class = TechnicalServiceForm
    template_name = 'monitoring/technical_service_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['service', 'manager']:
            messages.error(request, "У вас нет прав для создания ТО")
            return redirect('monitoring:machine_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        machine_id = self.kwargs.get('machine_id')
        if machine_id:
            machine = get_object_or_404(Machine, pk=machine_id)
            kwargs['machine'] = machine  # передаём в форму
        return kwargs

    def form_valid(self, form):
        # machine уже установлен в __init__ формы, можно не дублировать
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['technical_service'] = None
        return context

    def get_success_url(self):
        return reverse('monitoring:machine_detail', kwargs={'pk': self.object.machine.pk})

class TechnicalServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TechnicalService
    form_class = TechnicalServiceForm
    template_name = 'monitoring/technical_service_form.html'

    def test_func(self):
        return self.request.user.role in ['service', 'manager']

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для редактирования ТО")
        return redirect('monitoring:technical_service_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['technical_service'] = self.object
        return context

    def get_success_url(self):
        return reverse('monitoring:technical_service_detail', kwargs={'pk': self.object.pk})


# ======================== RECLAMATION ========================
class ReclamationListView(LoginRequiredMixin, FilterView):
    model = Reclamation
    template_name = 'monitoring/reclamation_list.html'
    filterset_class = ReclamationFilter
    context_object_name = 'reclamation_list'

    def get_queryset(self):
        return Reclamation.get_visible_to_user(self.request.user).order_by('-failure_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for reclamation in context['reclamation_list']:
            reclamation.can_edit = reclamation.can_be_edited_by(self.request.user)
        return context


class ReclamationDetailView(LoginRequiredMixin, DetailView):
    model = Reclamation
    template_name = 'monitoring/reclamation_detail.html'
    context_object_name = 'reclamation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем флаг can_edit для шаблона
        context['can_edit'] = self.object.can_be_edited_by(self.request.user)
        return context


class ReclamationCreateView(LoginRequiredMixin, CreateView):
    model = Reclamation
    form_class = ReclamationForm
    template_name = 'monitoring/reclamation_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in ['service', 'manager']:
            messages.error(request, "У вас нет прав для создания рекламации")
            return redirect('monitoring:machine_list')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        machine_id = self.kwargs.get('machine_id')
        form.instance.machine = get_object_or_404(Machine, pk=machine_id)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('monitoring:machine_detail', kwargs={'pk': self.object.machine.pk})


class ReclamationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Reclamation
    form_class = ReclamationForm
    template_name = 'monitoring/reclamation_form.html'

    def test_func(self):
        return self.request.user.role in ['service', 'manager']

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для редактирования рекламации")
        return redirect('monitoring:reclamation_list')

    def get_success_url(self):
        return reverse('monitoring:reclamation_detail', kwargs={'pk': self.object.pk})


# ======================== REFERENCE ========================
class ReferenceListView(LoginRequiredMixin, ListView):
    model = Reference
    template_name = 'monitoring/reference_list.html'
    context_object_name = 'references'


class ReferenceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Reference
    form_class = ReferenceForm
    template_name = 'monitoring/reference_form.html'

    def test_func(self):
        return self.request.user.role == 'manager'

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для создания справочника")
        return redirect('monitoring:reference_list')

    def get_success_url(self):
        return reverse('monitoring:reference_list')


class ReferenceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Reference
    form_class = ReferenceForm
    template_name = 'monitoring/reference_form.html'

    def test_func(self):
        return self.request.user.role == 'manager'

    def handle_no_permission(self):
        messages.error(self.request, "У вас нет прав для редактирования справочника")
        return redirect('monitoring:reference_list')

    def get_success_url(self):
        return reverse('monitoring:reference_list')
