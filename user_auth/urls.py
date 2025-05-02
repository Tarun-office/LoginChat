from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('verify-login-otp/', views.verify_login_otp, name='verify_login_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('signup/step1/', views.signup_step1, name='signup_step1'),
    path('signup/step2/', views.signup_step2, name='signup_step2'),
    path('verify-signup-otp/', views.verify_signup_otp, name='verify_signup_otp'),
    path('welcome/', views.welcome, name='welcome'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('users/', views.user_directory, name='user_directory'),
    path('users/<str:username>/', views.user_profile, name='user_profile'),
    path('conversations/', views.conversations, name='conversations'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/edit-message/<int:message_id>/', views.edit_message, name='edit_message'),
    path('api/delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('api/get-messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
    path('api/mark-messages-seen/<int:conversation_id>/', views.mark_messages_seen, name='mark_messages_seen'),
    path('api/check-user-status/<int:user_id>/', views.check_user_status, name='check_user_status'),
    path('logout/', views.logout_view, name='logout'),
]
