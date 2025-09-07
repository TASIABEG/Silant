from django.db import models
from django.contrib.auth.models import AbstractUser

# Базовый класс для справочников (чтобы не дублировать __str__)
class BaseReference(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


# Модели справочников
class MachineModel(BaseReference):
    pass


class EngineModel(BaseReference):
    pass


class TransmissionModel(BaseReference):
    pass


class DriveAxleModel(BaseReference):
    pass


class SteeringAxleModel(BaseReference):
    pass


class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return self.name


class ServiceOrganization(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название организации")
    address = models.TextField(verbose_name="Адрес")
    contact_person = models.CharField(max_length=255, verbose_name="Контактное лицо")
    contact_phone = models.CharField(max_length=20, verbose_name="Контактный телефон")

    def __str__(self):
        return self.name


class FailureNode(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return self.name


class RecoveryMethod(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = (
        ('client', 'Клиент'),
        ('service', 'Сервисная организация'),
        ('manager', 'Менеджер ЧЗСА'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    company = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def can_edit_machines(self):
        """Может ли пользователь редактировать машины"""
        return self.role == 'manager'

    def can_edit_references(self):
        """Может ли пользователь редактировать справочники"""
        return self.role == 'manager'

    def get_accessible_machines(self):
        """Получить машины, доступные пользователю"""
        if self.role == 'client':
            return Machine.objects.filter(client=self)
        elif self.role == 'service':
            return Machine.objects.filter(service_company=self)
        elif self.role == 'manager':
            return Machine.objects.all()
        return Machine.objects.none()

    def can_edit_reclamations(self):
        """Может ли пользователь редактировать рекламации"""
        return self.role in ['service', 'manager']

    def save(self, *args, **kwargs):
        """Запрет изменения username после создания"""
        if self.pk:
            orig = User.objects.get(pk=self.pk)
            if orig.username != self.username:
                raise ValueError("Изменение логина запрещено")
        super().save(*args, **kwargs)

    def set_password_restricted(self, raw_password):
        """Специальный метод, чтобы запретить пользователю менять пароль"""
        raise PermissionError("Самостоятельная смена пароля запрещена")

    def can_be_edited_by(self, user):
        return user.role == 'manager'


class Machine(models.Model):
    # Основная информация
    serial_number = models.CharField(max_length=50, unique=True, verbose_name="Зав. № машины")

    # Ссылки на справочники
    machine_model = models.ForeignKey(
        MachineModel,
        on_delete=models.PROTECT,
        verbose_name="Модель техники"
    )
    engine_model = models.ForeignKey(
        EngineModel,
        on_delete=models.PROTECT,
        verbose_name="Модель двигателя"
    )
    transmission_model = models.ForeignKey(
        TransmissionModel,
        on_delete=models.PROTECT,
        verbose_name="Модель трансмиссии"
    )
    drive_axle_model = models.ForeignKey(
        DriveAxleModel,
        on_delete=models.PROTECT,
        verbose_name="Модель ведущего моста"
    )
    steering_axle_model = models.ForeignKey(
        SteeringAxleModel,
        on_delete=models.PROTECT,
        verbose_name="Модель управляемого моста"
    )

    # Заводские номера компонентов
    engine_serial = models.CharField(max_length=50, verbose_name="Зав. № двигателя")
    transmission_serial = models.CharField(max_length=50, verbose_name="Зав. № трансмиссии")
    drive_axle_serial = models.CharField(max_length=50, verbose_name="Зав. № ведущего моста")
    steering_axle_serial = models.CharField(max_length=50, verbose_name="Зав. № управляемого моста")

    # Договор и поставка
    supply_contract = models.CharField(
        max_length=255,
        verbose_name="Договор поставки №, дата"
    )
    shipment_date = models.DateField(verbose_name="Дата отгрузки с завода")

    # Информация о клиенте и месте эксплуатации
    consignee = models.CharField(max_length=255, verbose_name="Грузополучатель")
    delivery_address = models.TextField(verbose_name="Адрес поставки (эксплуатации)")
    equipment = models.TextField(verbose_name="Комплектация (доп. опции)")

    # Связи с пользователями
    client = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_machines',
        limit_choices_to={'role': 'client'},
        verbose_name="Клиент"
    )
    service_company = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='serviced_machines',
        limit_choices_to={'role': 'service'},
        verbose_name="Сервисная компания"
    )

    current_hours = models.PositiveIntegerField(
        default=0,
        verbose_name="Наработка, м/час"
    )

    # Дополнительные поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.machine_model.name} ({self.serial_number})"

    @property
    def requires_maintenance(self):
        """Проверяет, требуется ли обслуживание машине"""
        return any(comp.wear_percentage > 85 for comp in self.components.all())

    @property
    def in_service(self):
        """Проверяет, находится ли машина в сервисе"""
        return self.maintenance_history.filter(end_date__isnull=True).exists()

    @property
    def basic_info(self):
        """Основная информация (поля 1-10) для гостей"""
        return {
            'serial_number': self.serial_number,
            'machine_model': self.machine_model.name,
            'engine_model': self.engine_model.name,
            'transmission_model': self.transmission_model.name,
            'drive_axle_model': self.drive_axle_model.name,
            'steering_axle_model': self.steering_axle_model.name,
            'engine_serial': self.engine_serial,
            'transmission_serial': self.transmission_serial,
            'drive_axle_serial': self.drive_axle_serial,
            'steering_axle_serial': self.steering_axle_serial,
        }

    @property
    def full_info(self):
        """Полная информация о машине"""
        info = self.basic_info
        info.update({
            'supply_contract': self.supply_contract,
            'shipment_date': self.shipment_date,
            'consignee': self.consignee,
            'delivery_address': self.delivery_address,
            'equipment': self.equipment,
            'client': self.client.username if self.client else None,
            'service_company': self.service_company.username if self.service_company else None,
            'current_hours': self.current_hours,
        })
        return info

    class Meta:
        ordering = ['-shipment_date']


class Component(models.Model):
    name = models.CharField(max_length=100)
    part_number = models.CharField(max_length=50)
    lifetime_hours = models.PositiveIntegerField()
    install_date = models.DateField()
    current_hours = models.PositiveIntegerField(default=0)

    # Связь с машиной через компонентную модель
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='components')

    @property
    def wear_percentage(self):
        if self.lifetime_hours == 0:
            return 0
        return min(100, int((self.current_hours / self.lifetime_hours) * 100))

    def __str__(self):
        return f"{self.name} ({self.part_number})"

    def can_be_edited_by(self, user):
        if user.role == 'manager':
            return True
        elif user.role == 'service':
            return self.machine.service_company == user
        return False


class Maintenance(models.Model):
    TYPE_CHOICES = (
        ('service', 'Техническое обслуживание'),
        ('repair', 'Ремонт'),
        ('failure', 'Поломка'),
    )
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='maintenance_history')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField()
    service_company = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'service'}
    )
    replaced_components = models.ManyToManyField(Component, blank=True)

    def __str__(self):
        return f"{self.get_type_display()} для {self.machine} ({self.start_date})"

    def can_be_edited_by(self, user):
        if user.role == 'manager':
            return True
        elif user.role == 'service':
            return self.service_company == user
        return False


class TechnicalService(models.Model):
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='technical_services',
        verbose_name="Машина"
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        verbose_name="Вид ТО"
    )
    service_date = models.DateField(verbose_name="Дата проведения ТО")
    operating_hours = models.PositiveIntegerField(verbose_name="Наработка, м/час")
    work_order_number = models.CharField(max_length=50, verbose_name="№ заказ-наряда")
    work_order_date = models.DateField(verbose_name="Дата заказ-наряда")
    service_organization = models.ForeignKey(
        ServiceOrganization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Организация, проводившая ТО"
    )
    service_organization_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Название организации (текст, если не в справочнике)"
    )
    service_company = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'service'},
        verbose_name="Сервисная компания"
    )

    def __str__(self):
        return f"ТО {self.service_type} для {self.machine} ({self.service_date})"

    @classmethod
    def get_visible_to_user(cls, user):
        """Получить ТО, видимые пользователю"""
        if user.role == 'client':
            return cls.objects.filter(machine__client=user)
        elif user.role == 'service':
            return cls.objects.filter(service_company=user)
        elif user.role == 'manager':
            return cls.objects.all()
        return cls.objects.none()

    def can_be_edited_by(self, user):
        """Может ли пользователь редактировать это ТО"""
        if user.role == 'manager':
            return True
        elif user.role == 'service':
            return self.service_company == user
        return False

    class Meta:
        ordering = ['-service_date']


# Основная модель рекламаций
class Reclamation(models.Model):
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='reclamations',
        verbose_name="Машина"
    )
    failure_date = models.DateField(verbose_name="Дата отказа")
    operating_hours = models.PositiveIntegerField(verbose_name="Наработка, м/час")
    failure_node = models.ForeignKey(
        FailureNode,
        on_delete=models.PROTECT,
        verbose_name="Узел отказа"
    )
    failure_description = models.TextField(verbose_name="Описание отказа")
    recovery_method = models.ForeignKey(
        RecoveryMethod,
        on_delete=models.PROTECT,
        verbose_name="Способ восстановления"
    )
    spare_parts_used = models.TextField(blank=True, verbose_name="Используемые запасные части")
    recovery_date = models.DateField(verbose_name="Дата восстановления")
    service_company = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'service'},
        verbose_name="Сервисная компания"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Рекламация по {self.machine} ({self.failure_date})"

    @property
    def downtime(self):
        """Расчет времени простоя техники в днях"""
        if self.failure_date and self.recovery_date:
            return (self.recovery_date - self.failure_date).days
        return None

    @classmethod
    def get_visible_to_user(cls, user):
        """Получить рекламации, видимые пользователю"""
        if user.role == 'client':
            return cls.objects.filter(machine__client=user)
        elif user.role == 'service':
            return cls.objects.filter(service_company=user)
        elif user.role == 'manager':
            return cls.objects.all()
        return cls.objects.none()

    def can_be_edited_by(self, user):
        """Может ли пользователь редактировать рекламацию"""
        if user.role == 'manager':
            return True
        elif user.role == 'service':
            return self.service_company == user
        return False

    class Meta:
        ordering = ['-failure_date']


class Reference(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Справочник"
        verbose_name_plural = "Справочники"

    def __str__(self):
        return self.name
