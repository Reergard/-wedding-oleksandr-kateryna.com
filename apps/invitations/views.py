import json
import logging

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import Invitation, Question, Choice, Answer
from apps.main.utils import is_mobile_device, ua_genitive_phrase


logger = logging.getLogger(__name__)


def invitation_page(request, token: str):
    invitation = get_object_or_404(Invitation, token=token)

    # отметить opened_at
    if not invitation.opened_at:
        invitation.opened_at = timezone.now()
        invitation.save(update_fields=["opened_at"])

    # Определяем устройство
    user_agent = request.META.get("HTTP_USER_AGENT", "")
    is_mobile = is_mobile_device(user_agent)

    template = "main/home_mobile.html" if is_mobile else "main/home_pc.html"

    response = render(
        request,
        template,
        {
            "invitation": invitation,
            "guest": invitation.guest,
            "token": invitation.token,
            "absolute_url": request.build_absolute_uri(),
            # ✅ ВАЖНО: имя в родительном падеже для preview/карточек ссылок
            "guest_name_for_link": ua_genitive_phrase(invitation.guest.full_name) if invitation.guest else "",
        },
    )

    # Настройка кэширования
    response["Vary"] = "User-Agent"
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response


@require_POST
@csrf_protect
def submit_rsvp(request, token: str):
    invitation = get_object_or_404(Invitation, token=token)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    note = (payload.get("note") or "").strip()
    attendance = (payload.get("attendance") or "").strip()
    answers = payload.get("answers") or {}

    logger.info(f"=== ОБРАБОТКА RSVP ДЛЯ {invitation.guest.full_name} (token: {token}) ===")
    logger.info(f"Attendance: {attendance}")
    logger.info(f"Note: {note[:100] if note else '(пусто)'}")
    logger.info(f"Всего вопросов в answers: {len(answers)}")
    logger.info(f"Вопросы в answers: {list(answers.keys())}")

    # 1) статус по attendance
    if attendance:
        att_lower = attendance.lower()
        if "не зможу" in att_lower or "не сможу" in att_lower:
            invitation.status = Invitation.Status.DECLINED
        else:
            invitation.status = Invitation.Status.ACCEPTED

    invitation.note = note
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=["status", "note", "responded_at"])

    # Счётчики
    saved_count = 0
    skipped_count = 0

    # 1.5) ДОПОЛНИТЕЛЬНО: сохранить attendance как Answer (чтобы в админке был ответ на 1-й вопрос)
    # ВАЖНО: ищем мягко (icontains), чтобы не сломалось из-за "?" и пробелов
    ATTENDANCE_Q_TEXT = "Чи зможете ви бути присутніми на весіллі"
    attendance_q = Question.objects.filter(is_active=True, text__icontains=ATTENDANCE_Q_TEXT).first()

    if attendance:
        if attendance_q:
            # Пытаемся найти Choice под пришедший текст
            attendance_choice = Choice.objects.filter(
                question=attendance_q,
                text__iexact=attendance
            ).first()

            # Запасной вариант: сравнение по началу строки (если чуть отличается пунктуация/окончание)
            if not attendance_choice:
                attendance_choice = Choice.objects.filter(
                    question=attendance_q,
                    text__istartswith=attendance.strip()[:10]
                ).first()

            if attendance_choice:
                Answer.objects.filter(invitation=invitation, question=attendance_q).delete()
                Answer.objects.create(
                    invitation=invitation,
                    question=attendance_q,
                    choice=attendance_choice
                )
                saved_count += 1
                logger.info(f"✓ Attendance сохранён в Answer: {attendance_choice.text}")
            else:
                logger.warning(f"✗ Choice для attendance не найден: '{attendance}'")
                logger.warning(
                    f"  Доступные choices: {list(Choice.objects.filter(question=attendance_q).values_list('text', flat=True))}"
                )
                skipped_count += 1
        else:
            logger.warning(f"✗ Вопрос attendance не найден в БД (icontains): '{ATTENDANCE_Q_TEXT}'")
            skipped_count += 1

    # 2) сохранение ответов из payload["answers"]
    all_questions = Question.objects.filter(is_active=True)

    questions_exact = {q.text.strip(): q for q in all_questions}
    questions_normalized = {}
    for q in all_questions:
        normalized = q.text.strip().lower().replace("  ", " ")
        questions_normalized[normalized] = q

    logger.info(f"Активных вопросов в БД: {len(questions_exact)}")
    logger.info(f"Тексты вопросов в БД: {list(questions_exact.keys())}")

    for q_text, selected in answers.items():
        q_text_norm = (q_text or "").strip()
        if not q_text_norm:
            logger.warning("Пропущен пустой вопрос")
            skipped_count += 1
            continue

        # точное совпадение
        question = questions_exact.get(q_text_norm)

        # нормализованное
        if not question:
            normalized = q_text_norm.lower().replace("  ", " ")
            question = questions_normalized.get(normalized)
            if question:
                logger.info(f"Вопрос найден по нормализованному тексту: '{q_text_norm}' → '{question.text}'")

        # частичное совпадение
        if not question:
            for db_q in all_questions:
                db_text_norm = db_q.text.strip()
                if q_text_norm in db_text_norm or db_text_norm in q_text_norm:
                    question = db_q
                    logger.info(f"Вопрос найден по частичному совпадению: '{q_text_norm}' → '{question.text}'")
                    break

        if not question:
            logger.warning(f"Вопрос не найден в БД: '{q_text_norm}'")
            logger.warning(f"  Полученный ответ: {selected}")
            logger.warning(f"  Доступные вопросы в БД: {list(questions_exact.keys())}")
            skipped_count += 1
            continue

        logger.info(f"Обработка вопроса: '{q_text_norm}' → {selected}")

        # MULTI
        if question.kind == Question.Kind.MULTI:
            if isinstance(selected, str):
                selected_list = [selected]
            else:
                selected_list = list(selected or [])

            selected_list = [str(s).strip() for s in selected_list if str(s).strip()]

            Answer.objects.filter(invitation=invitation, question=question).delete()

            for choice_text in selected_list:
                choice = Choice.objects.filter(question=question, text=choice_text).first()
                if choice:
                    Answer.objects.create(
                        invitation=invitation,
                        question=question,
                        choice=choice
                    )
                    saved_count += 1
                    logger.info(f"  ✓ Сохранен ответ: {choice_text}")
                else:
                    logger.warning(f"  ✗ Choice не найден: '{choice_text}' для вопроса '{q_text_norm}'")
                    skipped_count += 1

        # SINGLE
        else:
            if isinstance(selected, list):
                selected_value = (selected[0] if selected else "")
            else:
                selected_value = selected

            selected_value = str(selected_value).strip()
            if not selected_value:
                skipped_count += 1
                continue

            # Специальная обработка для "+1" формата "Так (....)"
            if "+1" in q_text_norm and "(" in selected_value and selected_value.startswith("Так"):
                base_text = "Так"
                base_choice = Choice.objects.filter(question=question, text=base_text).first()

                companion_types_text = selected_value.split("(", 1)[1].split(")", 1)[0].strip()
                companion_types = [t.strip() for t in companion_types_text.split(",") if t.strip()]

                Answer.objects.filter(invitation=invitation, question=question).delete()

                if base_choice:
                    Answer.objects.create(invitation=invitation, question=question, choice=base_choice)
                    saved_count += 1
                    logger.info(f"  ✓ Сохранен ответ: {base_text}")
                else:
                    logger.warning(f"  ✗ Base choice не найден: '{base_text}'")
                    skipped_count += 1

                for companion_type in companion_types:
                    type_choice = Choice.objects.filter(question=question, text=companion_type).first()
                    if type_choice:
                        Answer.objects.create(invitation=invitation, question=question, choice=type_choice)
                        saved_count += 1
                        logger.info(f"  ✓ Сохранен ответ: {companion_type}")
                    else:
                        logger.warning(f"  ✗ Choice не найден для типа спутника: '{companion_type}'")
                        skipped_count += 1

                continue

            # точное совпадение choice
            choice = Choice.objects.filter(question=question, text=selected_value).first()

            # если "Так (....)" → пробуем "Так"
            if not choice:
                base_text = selected_value.split("(", 1)[0].strip()
                if base_text and base_text != selected_value:
                    choice = Choice.objects.filter(question=question, text=base_text).first()
                    if choice:
                        logger.info(f"  Найден choice по базовому тексту: '{base_text}' вместо '{selected_value}'")

            # частичное совпадение
            if not choice:
                for c in Choice.objects.filter(question=question):
                    if c.text in selected_value or selected_value in c.text:
                        choice = c
                        logger.info(f"  Найден choice по частичному совпадению: '{c.text}' для '{selected_value}'")
                        break

            if not choice:
                logger.warning(f"  ✗ Choice не найден для значения: '{selected_value}' (вопрос: '{q_text_norm}')")
                logger.warning(
                    f"  Доступные choices: {list(Choice.objects.filter(question=question).values_list('text', flat=True))}"
                )
                skipped_count += 1
                continue

            Answer.objects.filter(invitation=invitation, question=question).delete()
            Answer.objects.create(invitation=invitation, question=question, choice=choice)
            saved_count += 1
            logger.info(f"  ✓ Сохранен ответ: {selected_value}")

    logger.info("=== ИТОГИ ОБРАБОТКИ ===")
    logger.info(f"Сохранено ответов: {saved_count}")
    logger.info(f"Пропущено: {skipped_count}")
    logger.info(f"Всего обработано answers: {len(answers)}")

    return JsonResponse({"ok": True, "saved": saved_count, "skipped": skipped_count})
