from django.urls import path
from .views import invitation_page, submit_rsvp

urlpatterns = [
    path("Invitation/<str:token>/", invitation_page, name="invitation_page"),
    path("api/invitation/<str:token>/submit/", submit_rsvp, name="submit_rsvp"),
]

