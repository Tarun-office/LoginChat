from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator, MaxLengthValidator
from django.utils import timezone
import os
from datetime import timedelta

class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.email} - {self.otp}"
    
    def is_valid(self):
        # OTP is valid for 10 minutes
        expiry_time = self.created_at + timezone.timedelta(minutes=10)
        return timezone.now() <= expiry_time

class UserProfile(models.Model):
    PROFESSION_CHOICES = [
        ('business', 'Business'),
        ('employee', 'Employee'),
        ('freelancer', 'Freelancer'),
        ('student', 'Student'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.IntegerField(validators=[MinValueValidator(18)])
    profession = models.CharField(max_length=20, choices=PROFESSION_CHOICES)
    
    # Profession-specific fields
    business_name = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    services_provided = models.CharField(max_length=200, blank=True, null=True)
    school_name = models.CharField(max_length=100, blank=True, null=True)
    
    bio = models.TextField(validators=[MinLengthValidator(50), MaxLengthValidator(150)])
    hobbies = models.CharField(max_length=200)
    username = models.CharField(max_length=30, unique=True)
    
    # Profile images
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    card_image1 = models.ImageField(upload_to='card_images/', blank=True, null=True)
    card_image2 = models.ImageField(upload_to='card_images/', blank=True, null=True)
    card_image3 = models.ImageField(upload_to='card_images/', blank=True, null=True)
    card_image4 = models.ImageField(upload_to='card_images/', blank=True, null=True)
    
    # Online status tracking
    last_active = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.get_full_name() or self.username
    
    def get_profession_detail(self):
        if self.profession == 'business':
            return self.business_name
        elif self.profession == 'employee':
            return self.company_name
        elif self.profession == 'freelancer':
            return self.services_provided
        elif self.profession == 'student':
            return self.school_name
        return ""
    
    def is_online(self):
        """Check if user is online (active in the last 5 minutes)"""
        return timezone.now() - self.last_active < timedelta(minutes=5)
    
    def save(self, *args, **kwargs):
        # Process images before saving
        self.process_image(self.profile_image)
        self.process_image(self.card_image1)
        self.process_image(self.card_image2)
        self.process_image(self.card_image3)
        self.process_image(self.card_image4)
        
        super().save(*args, **kwargs)
    
    def process_image(self, image_field):
        # Skip if no image
        if not image_field or not hasattr(image_field, 'path') or not os.path.exists(image_field.path):
            return
        
        try:
            from PIL import Image
            from io import BytesIO
            from django.core.files.base import ContentFile
            
            # Open image
            img = Image.open(image_field)
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large (max 1200px width)
            if img.width > 1200:
                ratio = 1200 / img.width
                new_height = int(img.height * ratio)
                img = img.resize((1200, new_height), Image.LANCZOS)
            
            # Save with optimized quality
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Get the filename and extension
            filename = os.path.basename(image_field.name)
            
            # Save the processed image
            image_field.save(filename, ContentFile(output.read()), save=False)
        except Exception as e:
            # Log the error but don't crash
            print(f"Error processing image: {e}")

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)
    seen_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    
    def mark_as_delivered(self):
        if not self.is_delivered:
            self.is_delivered = True
            self.delivered_at = timezone.now()
            self.save(update_fields=['is_delivered', 'delivered_at'])
    
    def mark_as_seen(self):
        if not self.is_seen:
            self.is_seen = True
            self.seen_at = timezone.now()
            self.save(update_fields=['is_seen', 'seen_at'])

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    last_message = models.ForeignKey(Message, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversation_last_message')
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation {self.id}"
    
    def get_messages(self):
        user_ids = self.participants.values_list('id', flat=True)
        return Message.objects.filter(
            sender__id__in=user_ids,
            receiver__id__in=user_ids
        ).order_by('created_at')
    
    def update_last_message(self, message):
        self.last_message = message
        self.save(update_fields=['last_message'])
    
    def get_unread_count(self, user):
        return Message.objects.filter(
            receiver=user,
            is_seen=False,
            sender__in=self.participants.exclude(id=user.id)
        ).count()
