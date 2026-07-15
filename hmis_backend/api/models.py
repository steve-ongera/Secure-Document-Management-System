import os
import uuid 

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models 


def validate_file_size(file):
    """ Reject files larger than 10MB."""
    max_size_mb = 10
    if file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File size cannot exceed {max_size_mb}MB.")
    
    
def patient_document_path(instance , filename):
    """
    Store files under per-patient, per-type folder with a UUID filename
    so the original name is never trusted  and collisions are impossible.
    
    e.g. patients_docs/12/lab_report/9c1e2b73...pdf
    """
    
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join(
        "patient_docs",
        str(instance.patient_id),
        instance.document_type,
        new_name,
    )
    

class Patient(models.model0):
    """Minimal patient record - just enough to link documents to a person"""
    
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
    ]  
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_id = models.CharField(max_length=20 , unique=True)
    date_of_birth = models.DateField()
    gender= models.CharField( max_length=1, choices=GENDER_CHOICES)  
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["last_name", "first_name"]
        
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.national_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    
    
class Document(models.model):
    """
    A singele uploaded files linked to a patient record.
    
    Only the files *path* and metadata live in postgres -  the binary
    content lives on disk /  objects storage. this keeps the DB small 
    backups fast and lets us swap the storage backend (eg S3)
    """
    
    DOCUMENT_TYPES = [
        ("photo", "Patient Photo"),
        ("national_id", "National ID"),
        ("lab_report", "Lab Report"),
        ("xray", "X-Ray / Imaging"),
        ("prescription", "Prescription"),
        ("discharge_summary", "Discahrge Summary"),
        ("insurance", " Insurance Document"),
        ("other", " Other"),
        
    ]
    
    ALLOWED_CONTENT_TYPES = [
        "image/jpeg",
        "images/png",
        "application/pdf",
    ]
    
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name = "documents"
    )
    document_type= models.CharField(max_length=30 , choices=DOCUMENT_TYPES)
    file = models.FileField(
        upload_to=patient_document_path,
        validators=[validate_file_size]
    )
    original_filename =  models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_size= models.PositiveIntegerField(help_text="size in bytes")
    description = models.CharField(max_length=255 , blank=True)
    uploaded_by =  models.ForeignKey(
        settings.AUTH_USER_MODEL , on_delete=models.SET_NULL , null=True
    )
    uploaded_at =  models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        ordering =  ["-uploaded_at"]
        indexes = [
            models.Index(fields=["patient", "document_type"]),
        ]
        
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.patient.full_name}"
    
    def clean(self):
        if self.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise ValidationError(
                f"Unsupported files type: {self.content_type}."
                f"Allowed: {', '.join(self.ALLOWED_CONTENT_TYPES)}"
            )
    
    

class DocumentAuditLog(models.Model):
    """

    Append-only trail of who touched a document and when.
    Required for any system holding medical/PII data.
    """
    
    ACTIONS =  [
        ("upload", "Uplaoded"),
        ("view", "Viewed"),
        ("download", "Downloaded"),
        ("archive", "Archived"),
        ("delete", "Deleted"),
        
    ]
    
    document = models.ForeignKey(
        Document , on_delete=models.CASCADE , related_name="audit_logs"
    )
    user =  models.ForeignKey(
        settings.AUTH_USER_MODEL , on_delete=models.SET_NULL , null=True
    )
    action=models.CharField(max_length=20 , choices=ACTIONS)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ["-timestamp"]
        
    def __str__(self):
        return f"{self.action} on Documents#{self.document_id} ny {self.user}"