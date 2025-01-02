from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from scipy.stats import chisquare, f_oneway
import matplotlib.pyplot as plt
import base64
from io import BytesIO, TextIOWrapper
import csv
from .forms import UploadCSVForm, ChiSquareForm, AnovaForm, HardyWeinbergForm
from .models import TestResult, UploadedFile
import hashlib
import uuid
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.forms import PasswordResetForm


# Helper function for plotting
def create_bar_plot(labels, observed, expected, title):
    fig, ax = plt.subplots()
    ax.bar(labels, observed, width=0.4, label='Observed', align='center', alpha=0.7)
    ax.bar(labels, expected, width=0.4, label='Expected', align='edge', alpha=0.7)
    ax.set_xlabel('Genotype')
    ax.set_ylabel('Frequency')
    ax.set_title(title)
    ax.legend()

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_url = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return plot_url

def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = UploadedFile(
            user=request.user,
            file=request.FILES['file']
        )
        uploaded_file.save()
        return HttpResponseRedirect('/')
    return render(request, 'core/upload.html')


# Registration View
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})


# Login View
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# Logout View
def user_logout(request):
    logout(request)
    return redirect('login')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect('login')  # Redirect to login page after successful sign-up
        else:
            messages.error(request, "There were errors in your form. Please check below.")
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})

# Home View
@login_required
def home(request):
    tests = [
        {"name": "Hardy-Weinberg Equilibrium Test", "url": "hardy-weinberg-test"},
        {"name": "Chi-Square Test for Independence", "url": "chi-square-test"},
        {"name": "ANOVA Test", "url": "anova-test"},
    ]
    return render(request, 'core/home.html', {'tests': tests})


# Hardy-Weinberg Test View
@login_required
def hardy_weinberg_view(request):
    chi_square, p_value, plot_url = None, None, None
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['csv_file']
                data = list(csv.reader(TextIOWrapper(file.file, encoding='utf-8')))
                observed = [int(data[1][0]), int(data[1][1]), int(data[1][2])]
                total = sum(observed)
                p = (2 * observed[0] + observed[1]) / (2 * total)
                q = 1 - p
                expected = [p**2 * total, 2 * p * q * total, q**2 * total]
                chi_square, p_value = chisquare(observed, expected)
                plot_url = create_bar_plot(['AA', 'AG', 'GG'], observed, expected,
                                           f'Hardy-Weinberg Test\nChi-Square = {chi_square:.2f}, p-value = {p_value:.4f}')
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = UploadCSVForm()
    return render(request, 'hardy_weinberg.html', {
        'form': form, 'chi_square': chi_square, 'p_value': p_value, 'plot_url': plot_url
    })


# Chi-Square Test View
@login_required
def chi_square_view(request):
    chi_square, p_value, plot_url = None, None, None
    if request.method == 'POST':
        form = ChiSquareForm(request.POST)
        if form.is_valid():
            try:
                observed = [form.cleaned_data[f'observed_{geno}'] for geno in ['AA', 'AG', 'GG']]
                expected = [form.cleaned_data[f'expected_{geno}'] for geno in ['AA', 'AG', 'GG']]
                chi_square, p_value = chisquare(observed, expected)
                plot_url = create_bar_plot(['AA', 'AG', 'GG'], observed, expected,
                                           f'Chi-Square Test\nChi-Square = {chi_square:.2f}, p-value = {p_value:.4f}')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    else:
        form = ChiSquareForm()
    return render(request, 'chi_square.html', {
        'form': form, 'chi_square': chi_square, 'p_value': p_value, 'plot_url': plot_url
    })


# ANOVA Test View
@login_required
def anova_test(request):
    f_statistic, p_value, error = None, None, None
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            try:
                file = request.FILES['csv_file']
                data = list(csv.reader(TextIOWrapper(file.file, encoding='utf-8')))
                groups = [list(map(float, column)) for column in zip(*data[1:])]
                f_statistic, p_value = f_oneway(*groups)
            except Exception as e:
                error = f"Error: {str(e)}"
    return render(request, 'anova_test.html', {
        'f_statistic': f_statistic, 'p_value': p_value, 'error': error
    })
@login_required
def previous_results(request):
    user = request.user
    results = TestResult.objects.filter(user=user).order_by('-created_at')  # Assuming TestResult is the model for test results
    return render(request, 'previous_results.html', {'results': results})

from .forms import PasswordResetRequestForm



def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                user = None

            if user:
                # Generate token and uid
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(user.pk.encode())

                # Send email
                domain = get_current_site(request).domain
                reset_link = f'http://{domain}/password-reset/{uid}/{token}/'
                subject = 'Password Reset Request'
                message = render_to_string('core/password_reset_email.html', {
                    'user': user,
                    'reset_link': reset_link
                })
                send_mail(subject, message, 'noreply@yourdomain.com', [email])
            return redirect('password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request, 'password_reset_request.html', {'form': form})


def password_reset_done(request):
    return render(request, 'password_reset_done.html')



def password_reset_confirm(request, uidb64, token):
    try:
        # Decode UID and get user
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)

        # Validate the token
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                password_form = PasswordChangeForm(user, request.POST)
                if password_form.is_valid():
                    password_form.save()
                    return redirect('password_reset_complete')
            else:
                password_form = PasswordChangeForm(user)
            return render(request, 'password_reset_confirm.html', {'form': password_form})

        else:
            return redirect('password_reset_failed')

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return redirect('password_reset_failed')
def password_reset_failed(request):
    return render(request, 'password_reset_failed.html')

def password_reset_complete(request):
    return render(request, 'password_reset_complete.html')
