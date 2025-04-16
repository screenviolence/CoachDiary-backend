import datetime
import random
import time

from django.core.management.base import BaseCommand
from django.core import management

from common.models import GenderChoices
from users.models import User
from standards.models import Standard, Level, StudentStandard
from students.models import Student, StudentClass

FIRST_NAMES = ["Иван", "Петр", "Алексей", "Дмитрий", "Николай", "Сергей", "Антон", "Максим", "Егор", "Владимир"]
LAST_NAMES = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Попов", "Васильев", "Зайцев", "Морозов", "Козлов"]
PATRONYMICS = ["Алексеевич", "Иванович", "Петрович", "Николаевич", "Дмитриевич", "Сергеевич", "Анатольевич",
               "Егорович", "Владимирович", "Максимович"]
FEMALE_FIRST_NAMES = ["Анна", "Мария", "Екатерина", "Дарья", "Ольга", "Наталья", "Татьяна", "Виктория", "Елена",
                      "Жанна"]
FEMALE_LAST_NAMES = ["Иванова", "Петрова", "Сидорова", "Кузнецова", "Смирнова", "Попова", "Васильева", "Зайцева",
                     "Морозова", "Козлова"]
FEMALE_PATRONYMICS = ["Алексеевна", "Ивановна", "Петровна", "Николаевна", "Дмитриевна", "Сергеевна", "Анатольевна",
                      "Егоровна", "Владимировна", "Максимовна"]

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

        users = [
            User.objects.create_user(first_name=f'Аккаунт №{i}', last_name='Тестовый', email=f'user{i}@example.com',
                                     password='password') for i in range(3)]

        student_classes = [
            StudentClass.objects.create(number=number, class_name=class_name, class_owner=random.choice(users))
            for number in range(1, 12) for class_name in ['А', 'Б', 'В']]

        students = []
        for _ in range(100):
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
            student = Student.objects.create(
                first_name=first_name,
                last_name=last_name,
                patronymic=patronymic,
                student_class=student_class,
                birthday=datetime.date(datetime.datetime.now().year - student_class.number - 7 + 1,
                                       random.randint(1, 12),
                                       random.randint(1, 28)),
                gender=gender,
            )
            students.append(student)

        standards = []
        for i in range(3):
            for st in NUMERIC_STANDARDS[i]:
                standards.append(Standard.objects.create(name=st, who_added=users[i], has_numeric_value=True))
            for st in NON_NUMERIC_STANDARDS[i]:
                standards.append(Standard.objects.create(name=st, who_added=users[i], has_numeric_value=False))

        levels = []
        for standard in standards:
            for i in range(1, 12):
                for gender in [GenderChoices.MALE, GenderChoices.FEMALE]:
                    level = Level.objects.create(
                        level_number=i,
                        low_value=random.randint(1, 10) if standard.has_numeric_value else None,
                        middle_value=random.randint(10, 20) if standard.has_numeric_value else None,
                        high_value=random.randint(20, 30) if standard.has_numeric_value else None,
                        standard=standard,
                        gender=gender,
                    )
                    levels.append(level)

        for student in students:
            user = student.student_class.class_owner
            user_standards = Standard.objects.filter(who_added=user)

            for standard in user_standards:
                student_class_number = student.student_class.number
                level = Level.objects.get(standard=standard, level_number=student_class_number,
                                          gender=student.gender)
                if standard.has_numeric_value:
                    value = random.randint(1, 50)
                    grade = level.calculate_grade(value)
                else:
                    value = random.randint(2, 20)
                    grade = value

                StudentStandard.objects.create(
                    student=student,
                    standard=standard,
                    value=value,
                    grade=grade,
                    level=level
                )

        elapsed_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f'Тестовые данные успешно созданы за {elapsed_time:.2f} секунд.'))
