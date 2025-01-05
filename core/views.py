from scipy import stats
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UploadedFile
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserLoginForm, UserSignupForm
from django.contrib import messages
import csv
from django.shortcuts import render
from django.http import HttpResponse
from .forms import HardyWeinbergForm, AlleleFrequencyForm, ChiSquareForm, UploadCSVForm
import scipy.stats as stat
from .forms import UploadCSVForm
import io
from scipy.stats import chi2_contingency
import numpy as np
from .forms import UploadCSVForm, ChiSquareForm
import csv
from scipy.stats import chisquare  
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from .models import TestResult  # Assuming TestResult is the model for test results
from .forms import HardyWeinbergForm  # import the appropriate form
from .forms import AnovaForm
from .models import AnovaTest  # Assuming you have a model to save results


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

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

def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def upload_file(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            # Logic to handle file upload (if applicable)
            messages.success(request, "File uploaded successfully!")
            return redirect('home')
    else:
        form = UploadCSVForm()
    return render(request, 'upload.html', {'form': form})
@login_required
def home(request):
    return render(request, 'core/home.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/home/')  # Redirect to home page after successful login
        else:
            return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")

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
from .forms import UploadCSVForm, ChiSquareForm

 #Hardy-Weinberg Test View


@login_required
def hardy_weinberg_view(request):
    if request.method == 'POST':
        form = HardyWeinbergForm(request.POST)
        if form.is_valid():
            observed_AA = form.cleaned_data['observed_AA']
            observed_AG = form.cleaned_data['observed_AG']
            observed_GG = form.cleaned_data['observed_GG']
            
            # Save to the database
            data = HardyWeinbergData.objects.create(
                user=request.user,
                observed_AA=observed_AA,
                observed_AG=observed_AG,
                observed_GG=observed_GG,
            )
            return redirect('perform_test', dataset_id=data.id, test_name='hardy-weinberg')
    else:
        form = HardyWeinbergForm()
    return render(request, 'hardy_weinberg.html', {'form': form})



def hardy_weinberg_test(AA_observed, AG_observed, GG_observed, total_observed):
    # Calculate expected frequencies based on Hardy-Weinberg equilibrium
    p = (2 * AA_observed + AG_observed) / (2 * total_observed)  # allele frequency for A
    q = 1 - p  # allele frequency for G

    expected_AA = p ** 2 * total_observed
    expected_AG = 2 * p * q * total_observed
    expected_GG = q ** 2 * total_observed

    # Perform chi-square test
    observed = [AA_observed, AG_observed, GG_observed]
    expected = [expected_AA, expected_AG, expected_GG]

    chi_square_stat, p_value = chisquare(observed, expected)

    return chi_square_stat, p_value

# Chi-Square Test View

@login_required
def chi_square_view(request):
    if request.method == 'POST':
        form = ChiSquareForm(request.POST)
        if form.is_valid():
            observed = form.cleaned_data['observed_values']
            expected = form.cleaned_data['expected_values']
            
            # Save to the database
            data = ChiSquareData.objects.create(
                user=request.user,
                observed_values=observed,
                expected_values=expected,
            )
            return redirect('perform_test', dataset_id=data.id, test_name='chi-square')
    else:
        form = ChiSquareForm()
    return render(request, 'chi_square.html', {'form': form})



def perform_chi_square_test(observed_AA, observed_AG, observed_GG, expected_AA, expected_AG, expected_GG):
    # Calculate the observed and expected frequency totals
    observed = [observed_AA, observed_AG, observed_GG]
    expected = [expected_AA, expected_AG, expected_GG]

    # Normalize expected frequencies so that their sum matches the observed frequencies
    total_observed = sum(observed)
    total_expected = sum(expected)

    if total_observed != total_expected:
        # Scale the expected frequencies to match the sum of observed frequencies
        scale_factor = total_observed / total_expected
        expected = [e * scale_factor for e in expected]

    # Perform the Chi-Square test
    chi_square_stat, p_value = chisquare(observed, expected)

    return chi_square_stat, p_value

# Function to handle CSV data parsing

def parse_csv(file):
    data = []
    decoded_file = file.read().decode('utf-8').splitlines()
    csv_reader = csv.reader(decoded_file)
    
    for row in csv_reader:
        if len(row) >= 6:  # Ensure each row has the expected number of columns
            data.append(row)
        else:
            print(f"Skipping row: {row} (not enough columns)")
    
    return data


# Home view to process CSV file upload
def home(request):
    tests = [
        {"name": "Hardy-Weinberg Equilibrium Test", "url": "hardy-weinberg-test"},
        {"name": "Chi-Square Test for Independence", "url": "chi-square-test"},
        # Add more tests here
    ]

    if request.method == 'POST':
        if 'upload_csv' in request.POST:
            # Handling CSV Upload
            csv_form = UploadCSVForm(request.POST, request.FILES)
            if csv_form.is_valid():
                file = request.FILES['csv_file']
                data = parse_csv(file)

                # Assuming data is a dictionary with observed and expected keys
                try:
                    observed = [int(data[1][0]), int(data[1][1]), int(data[1][2])]
                    expected = [int(data[1][3]), int(data[1][4]), int(data[1][5])]
                except (IndexError, ValueError) as e:
                    # Handle incorrect CSV format or parsing errors
                    return render(request, 'core/home.html', {
                        'csv_form': csv_form,
                        'error': 'Invalid CSV format. Please ensure the file has correct data.',
                        'tests': tests
                    })

                # Perform Hardy-Weinberg test
                chi_square, p_value = hardy_weinberg_test(
                    observed[0], observed[1], observed[2], sum(observed)
                )

                # Pass the data to the template
                csv_data = {
                    'observed': observed,
                    'expected': expected
                }

                return render(request, 'core/home.html', {
                    'csv_form': csv_form,
                    'chi_square': chi_square,
                    'p_value': p_value,
                    'data': csv_data,
                    'tests': tests
                })
    else:
        csv_form = UploadCSVForm()

    return render(request, 'core/home.html', {
        'csv_form': csv_form,
        'tests': tests
    })

@login_required
def previous_results(request):
    chi_square_results = ChiSquareData.objects.filter(user=request.user)
    hardy_weinberg_results = HardyWeinbergData.objects.filter(user=request.user)
    return render(request, 'previous_results.html', {
        'chi_square_results': chi_square_results,
        'hardy_weinberg_results': hardy_weinberg_results,
    })

# Function to perform tests (stub for now)
@login_required
def perform_test(request, dataset_id, test_name):
    # Logic to fetch the data, perform the test, and return results
    # Example: redirect to results page
    messages.success(request, f"Performed {test_name} test successfully!")
    return redirect('previous-results')


def perform_test(request):
    if request.method == 'POST':
        form = HardyWeinbergForm(request.POST)
        if form.is_valid():
            # Handle form data here (save results, etc.)
            return redirect('home')  # Redirect to home page or any other page after successful submission
    else:
        form = HardyWeinbergForm()

    return render(request, 'perform_test.html', {'form': form})



# View for the ANOVA test
def anova_test_view(request):
    if request.method == 'POST':
        form = AnovaForm(request.POST)
        if form.is_valid():
            # Get data from the form (convert string input to list of floats)
            group1_data = list(map(float, form.cleaned_data['group1'].split(',')))
            group2_data = list(map(float, form.cleaned_data['group2'].split(',')))
            group3_data = form.cleaned_data['group3']
            if group3_data:
                group3_data = list(map(float, group3_data.split(',')))

            # Perform ANOVA test
            if group3_data:
                # Perform one-way ANOVA for three groups
                f_statistic, p_value = stats.f_oneway(group1_data, group2_data, group3_data)
            else:
                # Perform two-group ANOVA if group3 is not provided
                f_statistic, p_value = stats.f_oneway(group1_data, group2_data)

            # Prepare result data
            result_data = {
                'f_statistic': f_statistic,
                'p_value': p_value
            }

            # Save result to the database (optional)
            AnovaTest.objects.create(user=request.user, input_data=form.cleaned_data['group1'] + "," + form.cleaned_data['group2'] + ("," + form.cleaned_data['group3'] if form.cleaned_data['group3'] else ""), result=str(result_data))

            return render(request, 'anova_result.html', {'result_data': result_data})
    else:
        form = AnovaForm()

    return render(request, 'anova_test.html', {'form': form})
