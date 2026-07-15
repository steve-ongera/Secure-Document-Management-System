from rest_framework import serializers

from .models import Document, DocumentAuditLog, Patient


class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    document_count = serializers.IntegerField(
        source="documents.count", read_only=True
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "national_id",
            "date_of_birth",
            "gender",
            "phone_number",
            "document_count",
            "created_at",
        ]


class DocumentAuditLogSerializer(serializers.ModelSerializer):
    user_display = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = DocumentAuditLog
        fields = ["id", "action", "user_display", "timestamp", "ip_address"]


class DocumentSerializer(serializers.ModelSerializer):
    """
    Handles upload (write) and listing (read).
    File validation (type/size) happens here — before it ever touches
    disk or the model's clean() — so bad uploads fail fast with a
    clear 400 instead of a 500 from a storage/DB error.
    """

    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    uploaded_by_display = serializers.CharField(
        source="uploaded_by.username", read_only=True
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "patient",
            "patient_name",
            "document_type",
            "file",
            "file_url",
            "original_filename",
            "content_type",
            "file_size",
            "description",
            "uploaded_by_display",
            "uploaded_at",
            "is_archived",
        ]
        read_only_fields = [
            "original_filename",
            "content_type",
            "file_size",
            "uploaded_by_display",
            "uploaded_at",
        ]
        extra_kwargs = {"file": {"write_only": True}}

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def validate_file(self, value):
        if value.content_type not in Document.ALLOWED_CONTENT_TYPES:
            raise serializers.ValidationError(
                f"Unsupported file type: {value.content_type}. "
                f"Allowed: {', '.join(Document.ALLOWED_CONTENT_TYPES)}"
            )
        max_size_mb = 10
        if value.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(
                f"File size cannot exceed {max_size_mb}MB."
            )
        return value

    def create(self, validated_data):
        file_obj = validated_data["file"]
        validated_data["original_filename"] = file_obj.name
        validated_data["content_type"] = file_obj.content_type
        validated_data["file_size"] = file_obj.size

        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["uploaded_by"] = request.user

        return super().create(validated_data)


class DocumentDetailSerializer(DocumentSerializer):
    """Adds the audit trail for a single-document view."""

    audit_logs = DocumentAuditLogSerializer(many=True, read_only=True)

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + ["audit_logs"]