import pandas as pd
from django.core.management.base import BaseCommand
from monitoring.models import *


class Command(BaseCommand):
    help = 'Импорт данных из Excel файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к Excel файлу')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']

        def get_column(df, possible_names, required=True):
            for name in possible_names:
                for col in df.columns:
                    if col.strip().lower() == name.strip().lower():
                        return col
            if required:
                raise ValueError(f"Не найдена обязательная колонка: {possible_names}")
            return None

        # --- Импорт машин ---
        df_machines = pd.read_excel(file_path, sheet_name=0, header=2)
        df_machines.columns = df_machines.columns.str.strip()

        for _, row in df_machines.iterrows():
            machine_model = self.get_or_create_model(MachineModel, row.get('Модель техники'))
            engine_model = self.get_or_create_model(EngineModel, row.get('Модель двигателя'))
            transmission_model = self.get_or_create_model(
                TransmissionModel, row.get('Модель трансмиссии (производитель, артикул)')
            )
            drive_axle_model = self.get_or_create_model(DriveAxleModel, row.get('Модель ведущего моста'))
            steering_axle_model = self.get_or_create_model(SteeringAxleModel, row.get('Модель управляемого моста'))

            client = User.objects.get_or_create(username=row.get('Покупатель'), defaults={'role': 'client'})[0]
            service_company = User.objects.filter(role='service', company__iexact=row.get('Сервисная компания')).first()
            if not service_company:
                service_company, _ = User.objects.get_or_create(
                    username=row.get('Сервисная компания'),
                    defaults={'role': 'service', 'company': row.get('Сервисная компания')}
                )

            Machine.objects.update_or_create(
                serial_number=row.get('Зав. № машины'),
                defaults={
                    'machine_model': machine_model,
                    'engine_model': engine_model,
                    'engine_serial': row.get('Зав. № двигателя'),
                    'transmission_model': transmission_model,
                    'transmission_serial': row.get('Зав. № трансмиссии'),
                    'drive_axle_model': drive_axle_model,
                    'drive_axle_serial': row.get('Зав. № ведущего моста'),
                    'steering_axle_model': steering_axle_model,
                    'steering_axle_serial': row.get('Зав. № управляемого моста'),
                    'shipment_date': row.get('Дата отгрузки с завода'),
                    'client': client,
                    'consignee': row.get('Грузополучатель (конечный потребитель)'),
                    'delivery_address': row.get('Адрес поставки (эксплуатации)'),
                    'equipment': row.get('Комплектация (доп. опции)'),
                    'service_company': service_company
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Импортировано/обновлено {len(df_machines)} машин'))

        # --- Импорт ТО ---
        df_to = pd.read_excel(file_path, sheet_name='ТО output', header=0)
        df_to.columns = df_to.columns.str.strip()

        serial_col = get_column(df_to, ['Зав. № машины'])
        service_type_col = get_column(df_to, ['Вид ТО'])
        service_date_col = get_column(df_to, ['Дата проведения ТО'])
        operating_hours_col = get_column(df_to, ['Наработка, м/час'])
        work_order_number_col = get_column(df_to, ['№ заказ-наряда'], required=False)
        work_order_date_col = get_column(df_to, ['Дата заказ-наряда'], required=False)
        service_org_col = get_column(df_to, ['Организация, проводившая ТО'], required=False)

        for _, row in df_to.iterrows():
            try:
                machine = Machine.objects.get(serial_number=row[serial_col])
            except Machine.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Машина с номером {row[serial_col]} не найдена"))
                continue

            ts_type = self.get_or_create_model(ServiceType, row[service_type_col])

            # --- Определяем организацию ТО ---
            service_org_value = row[service_org_col] if service_org_col and pd.notna(row[service_org_col]) else None
            service_org_obj = None
            service_org_text = ''
            ts_company = machine.service_company

            if service_org_value:
                service_org_value = service_org_value.strip()
                # Если совпадает с сервисной компанией машины, используем её
                service_user = User.objects.filter(role='service', company__iexact=service_org_value).first()
                if service_user:
                    ts_company = service_user
                    # Также создаём ServiceOrganization, если нужно
                    service_org_obj, _ = ServiceOrganization.objects.get_or_create(
                        name=service_org_value,
                        defaults={'address': '', 'contact_person': '', 'contact_phone': ''}
                    )
                else:
                    # Это просто текст — создаём ServiceOrganization с текстом
                    service_org_obj, _ = ServiceOrganization.objects.get_or_create(
                        name=service_org_value,
                        defaults={'address': '', 'contact_person': '', 'contact_phone': ''}
                    )
                    service_org_text = service_org_value

            TechnicalService.objects.update_or_create(
                machine=machine,
                service_date=row[service_date_col],
                defaults={
                    'service_type': ts_type,
                    'operating_hours': row[operating_hours_col] if pd.notna(row[operating_hours_col]) else 0,
                    'work_order_number': row[work_order_number_col] if work_order_number_col and pd.notna(row[work_order_number_col]) else '',
                    'work_order_date': row[work_order_date_col] if work_order_date_col and pd.notna(row[work_order_date_col]) else None,
                    'service_organization': service_org_obj,
                    'service_organization_name': service_org_text,
                    'service_company': ts_company
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Импортировано/обновлено {len(df_to)} ТО'))

        # --- Импорт рекламаций ---
        df_rec = pd.read_excel(file_path, sheet_name='рекламация output', header=1)
        df_rec.columns = df_rec.columns.str.strip()

        serial_col_rec = get_column(df_rec, ['Зав. № машины'])
        failure_date_col = get_column(df_rec, ['Дата отказа'])
        operating_hours_col_rec = get_column(df_rec, ['Наработка, м/час'])
        failure_node_col = get_column(df_rec, ['Узел отказа'], required=False)
        failure_desc_col = get_column(df_rec, ['Описание отказа'], required=False)
        recovery_method_col = get_column(df_rec, ['Способ восстановления'], required=False)
        used_parts_col = get_column(df_rec, ['Используемые запасные части'], required=False)
        recovery_date_col = get_column(df_rec, ['Дата восстановления'], required=False)
        service_company_col = get_column(df_rec, ['Сервисная компания'], required=False)

        for _, row in df_rec.iterrows():
            try:
                machine = Machine.objects.get(serial_number=row[serial_col_rec])
            except Machine.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Машина с номером {row[serial_col_rec]} не найдена для рекламации"))
                continue

            failure_node = self.get_or_create_model(FailureNode, row[failure_node_col]) if failure_node_col else None
            recovery_method = self.get_or_create_model(RecoveryMethod, row[recovery_method_col]) if recovery_method_col else None

            service_user = None
            if service_company_col and pd.notna(row[service_company_col]):
                service_user = User.objects.filter(role='service', company__iexact=row[service_company_col].strip()).first()
            if not service_user:
                service_user = machine.service_company  # fallback

            Reclamation.objects.update_or_create(
                machine=machine,
                failure_date=row[failure_date_col],
                defaults={
                    'operating_hours': row[operating_hours_col_rec] if pd.notna(row[operating_hours_col_rec]) else 0,
                    'failure_node': failure_node,
                    'failure_description': row[failure_desc_col] if failure_desc_col and pd.notna(row[failure_desc_col]) else '',
                    'recovery_method': recovery_method,
                    'spare_parts_used': row[used_parts_col] if used_parts_col and pd.notna(row[used_parts_col]) else '',
                    'recovery_date': row[recovery_date_col] if recovery_date_col and pd.notna(row[recovery_date_col]) else None,
                    'service_company': service_user
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Импортировано/обновлено {len(df_rec)} рекламаций'))

    def get_or_create_model(self, model_class, name):
        if pd.isna(name) or not name:
            return None
        obj, _ = model_class.objects.get_or_create(name=name.strip())
        return obj
