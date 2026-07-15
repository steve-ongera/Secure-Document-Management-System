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
    
    