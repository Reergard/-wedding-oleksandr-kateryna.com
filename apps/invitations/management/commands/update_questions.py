from django.core.management.base import BaseCommand
from apps.invitations.models import Question


class Command(BaseCommand):
    help = 'Обновляет тексты существующих вопросов'

    def handle(self, *args, **options):
        # Обновляем вопрос 3 (аллергии) - убираем двойное "є"
        q3 = Question.objects.filter(id=3).first()
        if q3:
            old_text = q3.text
            q3.text = "Чи є у вас харчові алергії або продукти, які вам не можна:"
            q3.save()
            if old_text != q3.text:
                self.stdout.write(self.style.SUCCESS(f'Обновлен вопрос 3: "{old_text}" -> "{q3.text}"'))
            else:
                self.stdout.write(f'Вопрос 3 уже имеет правильный текст: "{q3.text}"')

        # Обновляем вопрос 5 (трансфер) - меняем "потрібен" на "потрібна"
        q5 = Question.objects.filter(id=5).first()
        if q5:
            old_text = q5.text
            q5.text = "Чи потрібна вам трансфер до місця проведення або назад:"
            q5.save()
            if old_text != q5.text:
                self.stdout.write(self.style.SUCCESS(f'Обновлен вопрос 5: "{old_text}" -> "{q5.text}"'))
            else:
                self.stdout.write(f'Вопрос 5 уже имеет правильный текст: "{q5.text}"')

        # Проверяем все вопросы
        self.stdout.write("\nВсе активные вопросы в БД:")
        for q in Question.objects.filter(is_active=True).order_by('id'):
            self.stdout.write(f"ID {q.id}: {q.text}")

