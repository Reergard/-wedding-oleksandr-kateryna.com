from django.core.management.base import BaseCommand
from apps.invitations.models import Question, Choice


class Command(BaseCommand):
    help = 'Создает вопросы и варианты ответов из модального окна'

    def handle(self, *args, **options):
        # Вопрос 1: Присутствие на свадьбе (SINGLE)
        q1, created = Question.objects.get_or_create(
            text="Чи зможете ви бути присутніми на весіллі?",
            defaults={'order': 1, 'kind': Question.Kind.SINGLE, 'is_active': True}
        )
        if created:
            Choice.objects.get_or_create(question=q1, text="Так, з радістю буду!", defaults={'order': 1})
            Choice.objects.get_or_create(question=q1, text="На жаль, не зможу бути.", defaults={'order': 2})
            self.stdout.write(self.style.SUCCESS(f'Создан вопрос: {q1.text}'))

        # Вопрос 2: Предпочтения в еде (MULTI)
        q2, created = Question.objects.get_or_create(
            text="Відмітьте, будь ласка, ваші вподобання:",
            defaults={'order': 2, 'kind': Question.Kind.MULTI, 'is_active': True}
        )
        if created:
            Choice.objects.get_or_create(question=q2, text="Лосось", defaults={'order': 1})
            Choice.objects.get_or_create(question=q2, text="Курятина", defaults={'order': 2})
            Choice.objects.get_or_create(question=q2, text="Свинина", defaults={'order': 3})
            Choice.objects.get_or_create(question=q2, text="Яловичина", defaults={'order': 4})
            Choice.objects.get_or_create(question=q2, text="Овочі", defaults={'order': 5})
            Choice.objects.get_or_create(question=q2, text="Неважливо", defaults={'order': 6})
            self.stdout.write(self.style.SUCCESS(f'Создан вопрос: {q2.text}'))

        # Вопрос 3: Аллергии (SINGLE)
        q3, created = Question.objects.get_or_create(
            text="Чи є у вас харчові алергії або продукти, які вам не можна:",
            defaults={'order': 3, 'kind': Question.Kind.SINGLE, 'is_active': True}
        )
        if created:
            Choice.objects.get_or_create(question=q3, text="Так", defaults={'order': 1})
            Choice.objects.get_or_create(question=q3, text="Ні", defaults={'order': 2})
            self.stdout.write(self.style.SUCCESS(f'Создан вопрос: {q3.text}'))

        # Вопрос 4: Предпочтения в напитках (MULTI)
        q4, created = Question.objects.get_or_create(
            text="Відмітьте, будь ласка, ваші уподобання щодо напоїв:",
            defaults={'order': 4, 'kind': Question.Kind.MULTI, 'is_active': True}
        )
        if created:
            Choice.objects.get_or_create(question=q4, text="Шампанське", defaults={'order': 1})
            Choice.objects.get_or_create(question=q4, text="Біле вино", defaults={'order': 2})
            Choice.objects.get_or_create(question=q4, text="Червоне вино", defaults={'order': 3})
            Choice.objects.get_or_create(question=q4, text="Міцний алкголь", defaults={'order': 4})
            Choice.objects.get_or_create(question=q4, text="Безалкогольні напої", defaults={'order': 5})
            self.stdout.write(self.style.SUCCESS(f'Создан вопрос: {q4.text}'))

        # Вопрос 5: Трансфер (SINGLE)
        q5, created = Question.objects.get_or_create(
            text="Чи потрібна вам трансфер до місця проведення або назад:",
            defaults={'order': 5, 'kind': Question.Kind.SINGLE, 'is_active': True}
        )
        if created:
            Choice.objects.get_or_create(question=q5, text="Так", defaults={'order': 1})
            Choice.objects.get_or_create(question=q5, text="Ні", defaults={'order': 2})
            self.stdout.write(self.style.SUCCESS(f'Создан вопрос: {q5.text}'))

        # Вопрос 6: Запрос "+1" (SINGLE)
        q6, created = Question.objects.get_or_create(
            text="Чи потрібно вам запрошення \"+1\"?",
            defaults={'order': 6, 'kind': Question.Kind.SINGLE, 'is_active': True}
        )
        if created:
            Choice.objects.get_or_create(question=q6, text="Так", defaults={'order': 1})
            Choice.objects.get_or_create(question=q6, text="Ні", defaults={'order': 2})
            self.stdout.write(self.style.SUCCESS(f'Создан вопрос: {q6.text}'))

        self.stdout.write(self.style.SUCCESS('Все вопросы созданы!'))

