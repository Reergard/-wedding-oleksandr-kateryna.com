from django.core.management.base import BaseCommand
from apps.invitations.models import Question, Choice


class Command(BaseCommand):
    help = 'Добавляет Choice "Друга половинка" и "Дитина" к вопросу о "+1"'

    def handle(self, *args, **options):
        q = Question.objects.filter(text__icontains='+1').first()
        if not q:
            self.stdout.write(self.style.ERROR('Вопрос о "+1" не найден'))
            return
        
        c1, created1 = Choice.objects.get_or_create(
            question=q,
            text='Друга половинка',
            defaults={'order': 3}
        )
        if created1:
            self.stdout.write(self.style.SUCCESS(f'Добавлен Choice: "Друга половинка"'))
        else:
            self.stdout.write(f'Choice "Друга половинка" уже существует')
        
        c2, created2 = Choice.objects.get_or_create(
            question=q,
            text='Дитина',
            defaults={'order': 4}
        )
        if created2:
            self.stdout.write(self.style.SUCCESS(f'Добавлен Choice: "Дитина"'))
        else:
            self.stdout.write(f'Choice "Дитина" уже существует')
        
        self.stdout.write(f'\nВсе Choice для вопроса "{q.text}":')
        for c in Choice.objects.filter(question=q).order_by('order'):
            self.stdout.write(f'  - {c.text} (order: {c.order})')

