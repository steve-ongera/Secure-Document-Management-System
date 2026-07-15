from django.contrib import admin

from .models import Document, DocumentAuditLog, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["full_name", "national_id", "gender", "date_of_birth"]
    search_fields = ["first_name", "last_name", "national_id"]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "patient",
        "document_type",
        "original_filename",
        "file_size",
        "uploaded_by",
        "uploaded_at",
        "is_archived",
    ]
    list_filter = ["document_type", "is_archived"]
    search_fields = ["patient__first_name", "patient__last_name", "original_filename"]


@admin.register(DocumentAuditLog)
class DocumentAuditLogAdmin(admin.ModelAdmin):
    list_display = ["document", "action", "user", "timestamp", "ip_address"]
    list_filter = ["action"]
    readonly_fields = [f.name for f in DocumentAuditLog._meta.fields]