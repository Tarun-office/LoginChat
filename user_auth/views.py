import random
import string
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import OTP, UserProfile, Message, Conversation
from .forms import EmailForm, OTPVerificationForm, SignUpStep1Form, ProfileUpdateForm, MessageForm

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp):
    """Send OTP to user's email"""
    subject = 'Your OTP for Authentication'
    message = f'Your OTP is: {otp}. It is valid for 10 minutes.'
    from_email = settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'noreply@example.com'
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def index(request):
    """Home page view"""
    return render(request, 'user_auth/index.html')

def login_view(request):
    """Login view - Step 1: Email input"""
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check if email exists in the system
            if not User.objects.filter(email=email).exists():
                messages.error(request, "Email not found. Please sign up first.")
                return redirect('signup_step1')
            
            # Generate and save OTP
            otp = generate_otp()
            OTP.objects.create(email=email, otp=otp)
            
            # Send OTP to email
            email_sent = send_otp_email(email, otp)
            
            # Store email in session for verification
            request.session['login_email'] = email
            request.session['otp_sent_time'] = timezone.now().timestamp()
            
            if not email_sent and settings.DEBUG:
                # In debug mode, show the OTP in a message
                messages.info(request, f"Email sending failed. For testing, your OTP is: {otp}")
            
            return redirect('verify_login_otp')
    else:
        form = EmailForm()
    
    return render(request, 'user_auth/login.html', {'form': form})

def verify_login_otp(request):
    """Login view - Step 2: OTP verification"""
    if 'login_email' not in request.session:
        return redirect('login')
    
    email = request.session['login_email']
    otp_sent_time = request.session.get('otp_sent_time', 0)
    current_time = timezone.now().timestamp()
    cooldown_remaining = max(0, 30 - int(current_time - otp_sent_time))
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            
            # Get the latest OTP for this email
            latest_otp = OTP.objects.filter(email=email).order_by('-created_at').first()
            
            if latest_otp and latest_otp.otp == entered_otp and latest_otp.is_valid():
                # OTP is correct, log in the user
                user = User.objects.get(email=email)
                login(request, user)
                
                # Clean up session
                del request.session['login_email']
                if 'otp_sent_time' in request.session:
                    del request.session['otp_sent_time']
                
                return redirect('welcome')
            else:
                messages.error(request, "Invalid or expired OTP. Please try again.")
    else:
        form = OTPVerificationForm()
    
    # If in debug mode and using console email backend, show the OTP
    if settings.DEBUG and 'console' in settings.EMAIL_BACKEND:
        latest_otp = OTP.objects.filter(email=email).order_by('-created_at').first()
        if latest_otp:
            messages.info(request, f"For testing, your OTP is: {latest_otp.otp}")
    
    return render(request, 'user_auth/verify_otp.html', {
        'form': form, 
        'email': email,
        'cooldown_remaining': cooldown_remaining
    })

def resend_otp(request):
    """Resend OTP after cooldown period"""
    if request.method == 'POST' and 'login_email' in request.session:
        email = request.session['login_email']
        otp_sent_time = request.session.get('otp_sent_time', 0)
        current_time = timezone.now().timestamp()
        
        # Check if 30 seconds have passed since the last OTP was sent
        if current_time - otp_sent_time >= 30:
            # Generate and save new OTP
            otp = generate_otp()
            OTP.objects.create(email=email, otp=otp)
            
            # Send OTP to email
            email_sent = send_otp_email(email, otp)
            
            # Update OTP sent time
            request.session['otp_sent_time'] = current_time
            
            if not email_sent and settings.DEBUG:
                # In debug mode, return the OTP in the response
                return JsonResponse({
                    'success': True, 
                    'message': 'OTP resent successfully',
                    'debug_otp': otp if settings.DEBUG else None
                })
            
            return JsonResponse({'success': True, 'message': 'OTP resent successfully'})
        else:
            cooldown_remaining = int(30 - (current_time - otp_sent_time))
            return JsonResponse({
                'success': False, 
                'message': f'Please wait {cooldown_remaining} seconds before requesting a new OTP',
                'cooldown_remaining': cooldown_remaining
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def signup_step1(request):
    """Sign up view - Step 1: Basic user info"""
    if request.method == 'POST':
        form = SignUpStep1Form(request.POST)
        if form.is_valid():
            # Store form data in session
            request.session['signup_data'] = {
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
                'age': form.cleaned_data['age'],
                'profession': form.cleaned_data['profession'],
                'business_name': form.cleaned_data['business_name'],
                'company_name': form.cleaned_data['company_name'],
                'services_provided': form.cleaned_data['services_provided'],
                'school_name': form.cleaned_data['school_name'],
                'bio': form.cleaned_data['bio'],
                'hobbies': form.cleaned_data['hobbies'],
                'username': form.cleaned_data['username'],
            }
            
            return redirect('signup_step2')
    else:
        form = SignUpStep1Form()
    
    return render(request, 'user_auth/signup_step1.html', {'form': form})

def signup_step2(request):
    """Sign up view - Step 2: Email verification"""
    if 'signup_data' not in request.session:
        return redirect('signup_step1')
    
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists. Please use a different email.")
                return render(request, 'user_auth/signup_step2.html', {'form': form})
            
            # Generate and save OTP
            otp = generate_otp()
            OTP.objects.create(email=email, otp=otp)
            
            # Send OTP to email
            email_sent = send_otp_email(email, otp)
            
            # Store email in session for verification
            request.session['signup_email'] = email
            request.session['otp_sent_time'] = timezone.now().timestamp()
            
            if not email_sent and settings.DEBUG:
                # In debug mode, show the OTP in a message
                messages.info(request, f"Email sending failed. For testing, your OTP is: {otp}")
            
            return redirect('verify_signup_otp')
    else:
        form = EmailForm()
    
    return render(request, 'user_auth/signup_step2.html', {'form': form})

def verify_signup_otp(request):
    """Sign up view - Step 3: OTP verification"""
    if 'signup_email' not in request.session or 'signup_data' not in request.session:
        return redirect('signup_step1')
    
    email = request.session['signup_email']
    otp_sent_time = request.session.get('otp_sent_time', 0)
    current_time = timezone.now().timestamp()
    cooldown_remaining = max(0, 30 - int(current_time - otp_sent_time))
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            
            # Get the latest OTP for this email
            latest_otp = OTP.objects.filter(email=email).order_by('-created_at').first()
            
            if latest_otp and latest_otp.otp == entered_otp and latest_otp.is_valid():
                # OTP is correct, create user and profile
                signup_data = request.session['signup_data']
                
                # Create User
                user = User.objects.create_user(
                    username=signup_data['username'],
                    email=email,
                    password=generate_otp()  # Generate a random password (user will login with OTP)
                )
                user.first_name = signup_data['first_name']
                user.last_name = signup_data['last_name']
                user.save()
                
                # Create UserProfile
                UserProfile.objects.create(
                    user=user,
                    age=signup_data['age'],
                    profession=signup_data['profession'],
                    business_name=signup_data['business_name'],
                    company_name=signup_data['company_name'],
                    services_provided=signup_data['services_provided'],
                    school_name=signup_data['school_name'],
                    bio=signup_data['bio'],
                    hobbies=signup_data['hobbies'],
                    username=signup_data['username']
                )
                
                # Log in the user
                login(request, user)
                
                # Clean up session
                del request.session['signup_data']
                del request.session['signup_email']
                if 'otp_sent_time' in request.session:
                    del request.session['otp_sent_time']
                
                messages.success(request, "Registration successful!")
                return redirect('welcome')
            else:
                messages.error(request, "Invalid or expired OTP. Please try again.")
    else:
        form = OTPVerificationForm()
    
    # If in debug mode and using console email backend, show the OTP
    if settings.DEBUG and 'console' in settings.EMAIL_BACKEND:
        latest_otp = OTP.objects.filter(email=email).order_by('-created_at').first()
        if latest_otp:
            messages.info(request, f"For testing, your OTP is: {latest_otp.otp}")
    
    return render(request, 'user_auth/verify_otp.html', {
        'form': form, 
        'email': email,
        'cooldown_remaining': cooldown_remaining,
        'is_signup': True
    })

@login_required
def welcome(request):
    """Welcome page after login/signup"""
    # Get unread message count
    unread_count = Message.objects.filter(receiver=request.user, is_seen=False).count()
    
    return render(request, 'user_auth/welcome.html', {'unread_count': unread_count})

@login_required
def profile_update(request):
    """Update user profile"""
    profile = request.user.profile
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Update User model
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            
            # Save profile
            form.save()
            
            messages.success(request, "Profile updated successfully!")
            return redirect('welcome')
    else:
        form = ProfileUpdateForm(instance=profile, user=request.user)
    
    return render(request, 'user_auth/profile_update.html', {'form': form})

@login_required
def user_directory(request):
    """View all users"""
    search_query = request.GET.get('search', '')
    
    if search_query:
        users = UserProfile.objects.filter(
            Q(user__first_name__icontains=search_query) | 
            Q(user__last_name__icontains=search_query) | 
            Q(username__icontains=search_query)
        ).exclude(user=request.user)
    else:
        users = UserProfile.objects.exclude(user=request.user)
    
    # Get conversations for the current user
    conversations = Conversation.objects.filter(participants=request.user)
    conversation_users = {}
    
    for conversation in conversations:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        if other_user:
            conversation_users[other_user.id] = {
                'conversation_id': conversation.id,
                'unread_count': conversation.get_unread_count(request.user)
            }
    
    return render(request, 'user_auth/user_directory.html', {
        'users': users, 
        'search_query': search_query,
        'conversation_users': conversation_users
    })

@login_required
def user_profile(request, username):
    """View a specific user's profile"""
    profile = get_object_or_404(UserProfile, username=username)
    
    # Check if there's an existing conversation
    conversation = None
    other_user = profile.user
    
    if other_user != request.user:
        # Look for an existing conversation
        conversations = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
        if conversations.exists():
            conversation = conversations.first()
        else:
            # Create a new conversation if needed
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, other_user)
            conversation.save()
    
    return render(request, 'user_auth/user_profile.html', {
        'profile': profile,
        'conversation': conversation
    })

@login_required
def conversations(request):
    """View all conversations"""
    conversations = Conversation.objects.filter(participants=request.user)
    
    # Prepare data for each conversation
    conversation_data = []
    for conversation in conversations:
        other_user = conversation.participants.exclude(id=request.user.id).first()
        if other_user:
            try:
                profile = other_user.profile
                conversation_data.append({
                    'conversation': conversation,
                    'other_user': other_user,
                    'profile': profile,
                    'unread_count': conversation.get_unread_count(request.user)
                })
            except UserProfile.DoesNotExist:
                # Skip if profile doesn't exist
                pass
    
    return render(request, 'user_auth/conversations.html', {
        'conversations': conversation_data
    })

@login_required
def conversation_detail(request, conversation_id):
    """View a specific conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    other_user = conversation.participants.exclude(id=request.user.id).first()
    
    if not other_user:
        messages.error(request, "Invalid conversation")
        return redirect('conversations')
    
    try:
        profile = other_user.profile
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found")
        return redirect('conversations')
    
    # Get messages for this conversation
    messages_list = conversation.get_messages()
    
    # Mark messages as delivered first
    for msg in messages_list.filter(receiver=request.user, is_delivered=False):
        msg.mark_as_delivered()
    
    # Then mark as seen
    for msg in messages_list.filter(receiver=request.user, is_seen=False):
        msg.mark_as_seen()
    
    # Message form
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']
            
            # Create new message
            message = Message.objects.create(
                sender=request.user,
                receiver=other_user,
                content=content
            )
            
            # Update conversation
            conversation.update_last_message(message)
            
            # Redirect to avoid form resubmission
            return redirect('conversation_detail', conversation_id=conversation_id)
    else:
        form = MessageForm()
    
    return render(request, 'user_auth/conversation_detail.html', {
        'conversation': conversation,
        'other_user': other_user,
        'profile': profile,
        'messages': messages_list,
        'form': form
    })

@login_required
@require_POST
def send_message(request):
    """API endpoint to send a message"""
    try:
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        content = data.get('content')
        
        if not receiver_id or not content:
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        
        # Get receiver
        receiver = get_object_or_404(User, id=receiver_id)
        
        # Find or create conversation
        conversations = Conversation.objects.filter(participants=request.user).filter(participants=receiver)
        if conversations.exists():
            conversation = conversations.first()
        else:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, receiver)
            conversation.save()
        
        # Create message
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content
        )
        
        # Update conversation
        conversation.update_last_message(message)
        
        return JsonResponse({
            'success': True, 
            'message_id': message.id,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'conversation_id': conversation.id
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def edit_message(request, message_id):
    """API endpoint to edit a message"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    try:
        data = json.loads(request.body)
        content = data.get('content')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'})
        
        # Update message
        message.content = content
        message.is_edited = True
        message.save()
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'updated_at': message.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def delete_message(request, message_id):
    """API endpoint to delete a message"""
    message = get_object_or_404(Message, id=message_id, sender=request.user)
    
    try:
        # Delete message
        message_id = message.id
        message.delete()
        
        return JsonResponse({
            'success': True,
            'message_id': message_id
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_messages(request, conversation_id):
    """API endpoint to get messages for a conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Get last message ID from request to implement polling
    last_message_id = request.GET.get('last_message_id', 0)
    
    # Get new messages
    messages_list = conversation.get_messages().filter(id__gt=last_message_id)
    
    # Mark messages as delivered first
    for msg in messages_list.filter(receiver=request.user, is_delivered=False):
        msg.mark_as_delivered()
    
    # Format messages
    messages_data = []
    for msg in messages_list:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_edited': msg.is_edited,
            'is_delivered': msg.is_delivered,
            'is_seen': msg.is_seen,
            'seen_at': msg.seen_at.strftime('%Y-%m-%d %H:%M:%S') if msg.seen_at else None
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })

@login_required
def mark_messages_seen(request, conversation_id):
    """API endpoint to mark all messages in a conversation as seen"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    
    # Mark all messages as seen
    messages_updated = 0
    for msg in conversation.get_messages().filter(receiver=request.user, is_seen=False):
        msg.mark_as_seen()
        messages_updated += 1
    
    return JsonResponse({
        'success': True,
        'messages_updated': messages_updated
    })

@login_required
def check_user_status(request, user_id):
    """API endpoint to check if a user is online"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        profile = user.profile
        is_online = profile.is_online()
        last_active = profile.last_active.strftime('%Y-%m-%d %H:%M:%S')
        
        return JsonResponse({
            'success': True,
            'is_online': is_online,
            'last_active': last_active
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'User profile not found'
        })

def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('index')
