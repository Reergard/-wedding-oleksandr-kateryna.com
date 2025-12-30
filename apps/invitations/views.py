import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import Invitation, Question, Choice, Answer


def invitation_page(request, token: str):
    invitation = get_object_or_404(Invitation, token=token)

    # отметить opened_at
    if not invitation.opened_at:
        invitation.opened_at = timezone.now()
        invitation.save(update_fields=["opened_at"])

    # важно: передаём guest в шаблон, чтобы в modal.html подставить имя
    return render(
        request,
        "main/index.html",  # главная страница, где подключается модалка
        {
            "invitation": invitation,
            "guest": invitation.guest,
            "token": invitation.token,
        }
    )


@require_POST
@csrf_protect
def submit_rsvp(request, token: str):
    invitation = get_object_or_404(Invitation, token=token)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    # ожидаем:
    # payload = {
    #   "attendance": "Так, з радістю буду!" / "На жаль, не зможу бути.",
    #   "answers": {
    #      "Відмітьте, будь ласка, ваші вподобання:": ["Лосось", "Курятина", ...],
    #      "Чи потрібен вам трансфер до місця проведення або назад:": "Так",
    #      ...
    #   },
    #   "note": "..."
    # }

    note = (payload.get("note") or "").strip()
    attendance = (payload.get("attendance") or "").strip()
    answers = payload.get("answers") or {}

    # 1) статус по attendance
    if attendance:
        if "не зможу" in attendance.lower() or "не сможу" in attendance.lower():
            invitation.status = Invitation.Status.DECLINED
        else:
            invitation.status = Invitation.Status.ACCEPTED
    else:
        # если не прислали attendance — оставляем pending
        pass

    invitation.note = note
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=["status", "note", "responded_at"])

    # 2) сохранение ответов
    # грузим активные вопросы
    questions = {q.text.strip(): q for q in Question.objects.filter(is_active=True)}

    for q_text, selected in answers.items():
        q_text_norm = (q_text or "").strip()
        if not q_text_norm:
            continue

        question = questions.get(q_text_norm)
        if not question:
            # если текста вопроса нет в БД — игнорируем (или можно вернуть ошибку)
            continue

        # MULTI: список строк
        if question.kind == Question.Kind.MULTI:
            if isinstance(selected, str):
                selected_list = [selected]
            else:
                selected_list = list(selected or [])

            selected_list = [s.strip() for s in selected_list if str(s).strip()]

            # удалим старые ответы на этот вопрос
            Answer.objects.filter(invitation=invitation, question=question).delete()

            for choice_text in selected_list:
                choice = Choice.objects.filter(question=question, text=choice_text).first()
                if choice:
                    Answer.objects.get_or_create(
                        invitation=invitation,
                        question=question,
                        choice=choice
                    )

        # SINGLE: одна строка
        else:
            if isinstance(selected, list):
                # если пришёл список — возьмём первый
                selected_value = (selected[0] if selected else "")
            else:
                selected_value = selected

            selected_value = str(selected_value).strip()
            if not selected_value:
                continue

            choice = Choice.objects.filter(question=question, text=selected_value).first()
            if not choice:
                continue

            # удаляем старое, сохраняем одно
            Answer.objects.filter(invitation=invitation, question=question).delete()
            Answer.objects.create(invitation=invitation, question=question, choice=choice)

    return JsonResponse({"ok": True})

