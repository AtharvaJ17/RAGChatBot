from django.urls import path
from . import views

urlpatterns = [
  path("set-video/", views.set_video, name="set-video"),
  path("chat/", views.rag_chat, name="chat"),
]