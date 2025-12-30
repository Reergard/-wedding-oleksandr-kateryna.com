from __future__ import annotations

import secrets

from django.db import models
from django.utils import timezone


class Guest(models.Model):
    full_name = models.CharField(max_length=255)
    # контакты опционально (для тебя)
    email = models.EmailField(blank=True, null=True)
    telegram = models.CharField(max_length=255, blank=True, null=True)
    instagram = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self) -> str:
        return self.full_name


class Invitation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "В ожидании"
        ACCEPTED = "accepted", "Приняли"
        DECLINED = "declined", "Отклонили"

    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="invitations")
    token = models.CharField(max_length=32, unique=True, db_index=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    opened_at = models.DateTimeField(blank=True, null=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    # общий текст, который гость написал в конце
    note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    def ensure_token(self) -> None:
        if not self.token:
            # 10-14 символов обычно достаточно, но можно 16+
            self.token = secrets.token_urlsafe(9)[:12]  # например: 'ABCD1234EfGh'

    def mark_opened(self):
        if not self.opened_at:
            self.opened_at = timezone.now()
            self.save(update_fields=["opened_at"])

    def mark_responded(self):
        self.responded_at = timezone.now()
        self.save(update_fields=["responded_at"])

    def save(self, *args, **kwargs):
        self.ensure_token()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.guest.full_name} ({self.token})"


class Question(models.Model):
    class Kind(models.TextChoices):
        SINGLE = "single", "Один вариант"
        MULTI = "multi", "Несколько вариантов"

    text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.SINGLE)

    def __str__(self) -> str:
        return self.text[:80]


class Choice(models.Model):
    """
    Варианты ответа на вопрос.
    Например: "Так", "Ні"
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.question_id}: {self.text}"


class Answer(models.Model):
    """
    Ответ на конкретный вопрос в рамках конкретного Invitation.
    """
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("invitation", "question", "choice")

    def __str__(self) -> str:
        return f"{self.invitation_id} -> {self.question_id}: {self.choice.text}"
