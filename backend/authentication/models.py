from django.db import models
from django.contrib.auth.models import User

class CompanyContact(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['email', 'company']

    def __str__(self):
        return f"{self.name} - {self.company}"

class UserResume(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')
    position = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Current Resume of {self.user.email} for position '{self.position}'"

class ApplicationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=255)
    resume = models.FileField(upload_to='resumes/history/')  # Different folder for historical resumes
    contacts_csv = models.FileField(upload_to='contacts_csv/', null=True, blank=True)
    application_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-application_date']  # Most recent first
        
    def __str__(self):
        return f"{self.user.email} - {self.position} ({self.application_date})"

class EmailHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    sent_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-sent_date']
        
    def __str__(self):
        return f"{self.subject} - {self.recipient}"
    
class GmailCredentials(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    refresh_token = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255, null=True)
    token_expiry = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gmail Credentials for {self.user.email}"
