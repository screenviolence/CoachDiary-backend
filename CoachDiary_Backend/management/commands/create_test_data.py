import datetime
import random
import time

from django.core import management
from django.core.management.base import BaseCommand
from django.db import transaction

from common.models import GenderChoices
from standards.models import Standard, Level, StudentStandard
from students.models import Student, StudentClass, Invitation
from users.models import User

FIRST_NAMES = [
    "Иван", "Петр", "Алексей", "Дмитрий", "Николай", "Сергей", "Антон", "Максим", "Егор", "Владимир",
    "Александр", "Михаил", "Игорь", "Константин", "Юрий", "Валерий", "Владислав", "Григорий", "Роман", "Денис",
]

LAST_NAMES = [
    "Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Попов", "Васильев", "Зайцев", "Морозов", "Козлов",
    "Новиков", "Федоров", "Михайлов", "Захаров", "Павлов", "Семёнов", "Голубев", "Виноградов", "Богданов", "Никитин",
]

PATRONYMICS = [
    "Алексеевич", "Иванович", "Петрович", "Николаевич", "Дмитриевич", "Сергеевич", "Анатольевич", "Егорович",
    "Владимирович", "Максимович", "Михайлович", "Юрьевич", "Константинович", "Григорьевич", "Романович",
    "Денисович", "Игоревич", "Валериевич", "Владиславович", "Александрович",
]

FEMALE_FIRST_NAMES = [
    "Анна", "Мария", "Екатерина", "Дарья", "Ольга", "Наталья", "Татьяна", "Виктория", "Елена", "Жанна", "Александра",
    "Валентина", "Людмила", "Светлана", "Ксения", "Ирина", "Алина", "Полина", "Марина", "Юлия",
]

FEMALE_LAST_NAMES = [
    "Иванова", "Петрова", "Сидорова", "Кузнецова", "Смирнова", "Попова", "Васильева", "Зайцева", "Морозова", "Козлова",
    "Новикова", "Федорова", "Михайлова", "Захарова", "Павлова", "Семёнова", "Голубева", "Виноградова", "Богданова",
    "Никитина",
]

FEMALE_PATRONYMICS = [
    "Алексеевна", "Ивановна", "Петровна", "Николаевна", "Дмитриевна", "Сергеевна", "Анатольевна", "Егоровна",
    "Владимировна", "Максимовна", "Михайловна", "Юрьевна", "Константиновна", "Григорьевна", "Романовна",
    "Денисовна", "Игоревна", "Валериевна", "Владиславовна", "Александровна",
]

NUMERIC_STANDARDS = [
    ["Бег 100 м", "Прыжки в длину", "Отжимания", "Бег 1000 м", ],
    ["Челночный бег", "Метание мяча", "Гибкость", "Приседания", "Подтягивания", ],
    ["Бег 2000 м", "Плавание 100 м", "Плавание 200 м", "Плавание 400 м", ]
]

NON_NUMERIC_STANDARDS = [
    ["Вскок на козла", "Кувырок вперёд", ],
    ["Перестановка в 2 шеренги", "Ловля", ],
    ["Мост из положения лежа", "Подача волейбольного мяча", ]
]


class Command(BaseCommand):
    help = "Создаёт тестовые данные"

    def handle(self, *args, **kwargs):
        confirm = input(
            f"Вы уверены, что хотите наполнить базу данных тестовыми данными? ВСЕ ДАННЫЕ В ТЕКУЩЕЙ БАЗЕ ДАННЫХ БУДУТ УДАЛЕНЫ! [y/N]: ")
        if confirm.lower() != 'y':
            self.stdout.write(self.style.WARNING("Операция отменена"))
            return
        management.call_command('flush', '--noinput')
        management.call_command('makemigrations')
        management.call_command('migrate')

        start_time = time.time()

        with transaction.atomic():
            users = [
                User.objects.create_user(first_name=f'Аккаунт №{i}', last_name='Тестовый', email=f'user{i}@example.com',
                                         password='password', is_test_data=True) for i in range(2)]

            student_class_objects = [
                StudentClass(number=number, class_name=class_name, class_owner=random.choice(users))
                for number in range(1, 12) for class_name in ['А', 'Б', 'В']
            ]
            student_classes = StudentClass.objects.bulk_create(student_class_objects)

            student_objects = []
            for _ in range(800):
                gender = random.choice([GenderChoices.MALE, GenderChoices.FEMALE])
                if gender == GenderChoices.MALE:
                    last_name = random.choice(LAST_NAMES)
                    first_name = random.choice(FIRST_NAMES)
                    patronymic = random.choice(PATRONYMICS)
                else:
                    last_name = random.choice(FEMALE_LAST_NAMES)
                    first_name = random.choice(FEMALE_FIRST_NAMES)
                    patronymic = random.choice(FEMALE_PATRONYMICS)

                student_class = random.choice(student_classes)
                student_objects.append(Student(
                    first_name=first_name,
                    last_name=last_name,
                    patronymic=patronymic,
                    student_class=student_class,
                    birthday=datetime.date(datetime.datetime.now().year - student_class.number - 7 + 1,
                                          random.randint(1, 12),
                                          random.randint(1, 28)),
                    gender=gender,
                ))
            students = Student.objects.bulk_create(student_objects)

            invitation_objects = []
            for student in students:
                invite_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))

                invitation_objects.append(Invitation(
                    student=student,
                    invite_code=invite_code,
                    is_used=False,
                ))

            if invitation_objects:
                Invitation.objects.bulk_create(invitation_objects, batch_size=1000)

            standard_objects = []
            for i in range(2):
                for st in NUMERIC_STANDARDS[i]:
                    standard_objects.append(Standard(name=st, who_added=users[i], has_numeric_value=True))
                for st in NON_NUMERIC_STANDARDS[i]:
                    standard_objects.append(Standard(name=st, who_added=users[i], has_numeric_value=False))
            standards = Standard.objects.bulk_create(standard_objects)

            level_objects = []
            for standard in standards:
                for i in range(1, 12):
                    for gender in [GenderChoices.MALE, GenderChoices.FEMALE]:
                        level_objects.append(Level(
                            level_number=i,
                            low_value=random.randint(1, 10) if standard.has_numeric_value else None,
                            middle_value=random.randint(10, 20) if standard.has_numeric_value else None,
                            high_value=random.randint(20, 30) if standard.has_numeric_value else None,
                            standard=standard,
                            gender=gender,
                        ))
            levels = Level.objects.bulk_create(level_objects, batch_size=1000)

            level_map = {}
            for level in Level.objects.all():
                key = (level.standard_id, level.level_number, level.gender)
                level_map[key] = level

            student_standard_objects = []
            for student in students:
                user = student.student_class.class_owner
                user_standards = Standard.objects.filter(who_added=user)

                for class_number in range(1, student.student_class.number + 1):
                    for standard in user_standards:
                        key = (standard.id, class_number, student.gender)
                        level = level_map.get(key)
                        if level:
                            if standard.has_numeric_value:
                                value = random.randint(1, 50)
                                grade = level.calculate_grade(value)
                            else:
                                value = random.randint(2, 5)
                                grade = value

                            student_standard_objects.append(StudentStandard(
                                student=student,
                                standard=standard,
                                value=value,
                                grade=grade,
                                level=level
                            ))

            StudentStandard.objects.bulk_create(student_standard_objects, batch_size=1000)

        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'Тестовые данные успешно созданы за {elapsed_time:.2f} секунд.'))