from django.urls import path,include
from core import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),  # Add this line for the root path
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),  # This should call the correct login view
    path('logout/', views.user_logout, name='logout'),
    path('upload/', views.upload_file, name='upload'),
    path('signup/', views.signup, name='signup'),  # URL for the sign-up page
    
    # Correct paths for chi-square and hardy-weinberg tests
    path('chi-square-test/', views.chi_square_view, name='chi-square-test'),  # Corrected function call
    path('hardy-weinberg-test/', views.hardy_weinberg_view, name='hardy-weinberg-test'),  # Corrected function call
    path('previous-results/', views.previous_results, name='previous-results'),
    path('anova-test/', views.anova_test, name='anova-test'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
