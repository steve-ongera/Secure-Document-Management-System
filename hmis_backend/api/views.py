from django.http import FileResponse, Http404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Document, DocumentAuditLog, Patient
from .serializers import (
    DocumentDetailSerializer,
    DocumentSerializer,
    PatientSerializer,
)


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _log(document, user, action_name, request):
    DocumentAuditLog.objects.create(
        document=document,
        user=user if user.is_authenticated else None,
        action=action_name,
        ip_address=_client_ip(request),
    )


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["first_name", "last_name", "national_id"]

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                first_name__icontains=search
            ) | qs.filter(last_name__icontains=search) | qs.filter(
                national_id__icontains=search
            )
        return qs


class DocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD + secure retrieval for patient documents.

    - `list` / `retrieve` require authentication (role checks can be
      layered on with a custom permission class per document_type).
    - Every view/download is written to DocumentAuditLog, so access
      to sensitive files (lab reports, IDs, insurance docs) is always
      traceable.
    - Soft delete via `archive` instead of hard delete, to preserve
      the audit trail and satisfy compliance requirements.
    """

    queryset = Document.objects.select_related("patient", "uploaded_by")
    permission_classes = [permissions.IsAuthenticated]
    parser_classes_note = "multipart/form-data for uploads"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return DocumentDetailSerializer
        return DocumentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        patient_id = self.request.query_params.get("patient")
        document_type = self.request.query_params.get("document_type")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if document_type:
            qs = qs.filter(document_type=document_type)
        if self.request.query_params.get("include_archived") != "true":
            qs = qs.filter(is_archived=False)
        return qs

    def perform_create(self, serializer):
        document = serializer.save()
        _log(document, self.request.user, "upload", self.request)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        _log(instance, request.user, "view", request)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def download(self, request, pk=None):
        """Stream the file and record a 'download' audit entry."""
        document = self.get_object()
        if not document.file:
            raise Http404("File not found.")
        _log(document, request.user, "download", request)
        return FileResponse(
            document.file.open("rb"),
            as_attachment=True,
            filename=document.original_filename,
        )

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        """Soft-delete: keep the file + audit trail, hide from normal lists."""
        document = self.get_object()
        document.is_archived = True
        document.save(update_fields=["is_archived"])
        _log(document, request.user, "archive", request)
        return Response(
            {"status": "archived"}, status=status.HTTP_200_OK
        )