from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Guest, Invitation, Question, Choice, Answer


@admin.action(description="Создать приглашения (сгенерировать токены) выбранным гостям")
def create_invitations(modeladmin, request, queryset):
    for guest in queryset:
        Invitation.objects.create(guest=guest)


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "telegram", "instagram", "invitations_count")
    search_fields = ("full_name", "email", "telegram", "instagram")
    actions = [create_invitations]
    
    def invitations_count(self, obj):
        count = obj.invitations.count()
        if count > 0:
            return format_html('<strong>{}</strong>', count)
        return "0"
    invitations_count.short_description = "Приглашений"


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "kind", "order", "is_active")
    list_editable = ("kind", "order", "is_active")
    inlines = [ChoiceInline]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("guest", "status", "opened_at", "responded_at", "public_link")
    list_filter = ("status", "responded_at")
    search_fields = ("guest__full_name", "token")
    readonly_fields = ("token", "opened_at", "responded_at", "public_link", "answers_table", "note_display")
    fields = ("guest", "status", "token", "public_link", "opened_at", "responded_at", "answers_table", "note_display")
    
    def note_display(self, obj: Invitation):
        if obj.note:
            return format_html('<div style="padding: 10px; background: #f5f5f5; border-radius: 4px; white-space: pre-wrap;">{}</div>', obj.note)
        return "Комментарий не оставлен"
    note_display.short_description = "Комментарий гостя"

    def public_link(self, obj: Invitation):
        from django.conf import settings
        # Получаем домен из настроек
        if hasattr(settings, 'ALLOWED_HOSTS') and settings.ALLOWED_HOSTS:
            domain = settings.ALLOWED_HOSTS[0]
        else:
            domain = 'wedding-oleksandr-kateryna.com'
        
        protocol = 'https' if not settings.DEBUG else 'http'
        full_url = f"{protocol}://{domain}/Invitation/{obj.token}/"
        return format_html('<a href="{}" target="_blank" style="word-break: break-all;">{}</a>', full_url, full_url)
    public_link.short_description = "Ссылка для отправки"
    public_link.admin_order_field = 'token'  # Позволяет сортировать по токену

    def answers_table(self, obj: Invitation):
        # группируем ответы по вопросу (для MULTI — выводим через запятую)
        qs = obj.answers.select_related("question", "choice").order_by("question__order", "question__id", "choice__order", "choice__id")
        if not qs:
            return "Ответов еще нет"

        grouped = {}
        for a in qs:
            grouped.setdefault(a.question.text, []).append(a.choice.text)

        rows = []
        for q_text, choices in grouped.items():
            rows.append(f"""
              <tr>
                <td style="padding:6px 10px; border:1px solid #ddd; width:65%">{q_text}</td>
                <td style="padding:6px 10px; border:1px solid #ddd">{", ".join(choices)}</td>
              </tr>
            """)

        html = f"""
        <table style="border-collapse:collapse; width:100%; max-width:1100px;">
          <thead>
            <tr>
              <th style="text-align:left; padding:6px 10px; border:1px solid #ddd;">Питання</th>
              <th style="text-align:left; padding:6px 10px; border:1px solid #ddd;">Відповідь</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
        """
        return format_html(html)
    answers_table.short_description = "Вопросы и ответы"


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("invitation", "question", "choice")
    search_fields = ("invitation__guest__full_name", "invitation__token", "question__text", "choice__text")
    list_filter = ("question", "choice")
