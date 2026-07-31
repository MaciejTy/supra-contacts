from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# The router generates /api/contacts/ and /api/contacts/{id}/ automatically.
router = DefaultRouter()
router.register("contacts", views.ContactViewSet, basename="contact")

urlpatterns = [
    path("", views.contact_list, name="contact_list"),
    path("add/", views.contact_create, name="contact_create"),
    path("<int:pk>/edit/", views.contact_update, name="contact_update"),
    path("<int:pk>/delete/", views.contact_delete, name="contact_delete"),
    path("api/weather/", views.weather_api, name="weather_api"),
    path("api/", include(router.urls)),
]