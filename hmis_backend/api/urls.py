from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet, PatientViewSet

router = DefaultRouter()
router.register(r"patients", PatientViewSet, basename="patient")
router.register(r"documents", DocumentViewSet, basename="document")

urlpatterns = [
    path("", include(router.urls)),
]

# Resulting endpoints:
# GET/POST         /api/patients/
# GET/PUT/PATCH/DELETE /api/patients/{id}/
# GET/POST         /api/documents/
# GET/PUT/PATCH/DELETE /api/documents/{id}/
# GET              /api/documents/{id}/download/
# POST             /api/documents/{id}/archive/