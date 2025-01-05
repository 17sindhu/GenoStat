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
import io
from scipy.stats import chi2_contingency
import numpy as np
from .forms import UploadCSVForm, ChiSquareForm
import csv
from scipy.stats import chisquare,f_oneway  
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from .models import TestResult  # Assuming TestResult is the model for test results
from io import TextIOWrapper


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
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = UploadedFile(
            user=request.user,
            file=request.FILES['file']
        )
        uploaded_file.save()
        return HttpResponseRedirect('/')
    return render(request, 'upload.html')

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
# Home view to process CSV file upload
@login_required
def home(request):
    tests = [
        {"name": "Hardy-Weinberg Equilibrium Test", "url": "hardy-weinberg-test"},
        {"name": "Chi-Square Test for Independence", "url": "chi-square-test"},
        {"name": "ANOVA Test", "url": "anova-test"},
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
    user = request.user
    results = TestResult.objects.filter(user=user).order_by('-created_at')  # Changed timestamp to created_at
    return render(request, 'previous_results.html', {'results': results})
 #Hardy-Weinberg Test View


def hardy_weinberg_view(request):
    chi_square = None
    p_value = None
    p = None
    q = None
    equilibrium_status = None
    plot_url = None

    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            data = parse_csv(file)  # Parse the uploaded CSV to extract the observed genotypes
            
            # Count observed genotypes
            observed_AA = int(data[1][0])
            observed_AG = int(data[1][1])
            observed_GG = int(data[1][2])
            total = observed_AA + observed_AG + observed_GG  # Total number of individuals

            # Calculate allele frequencies (p and q)
            p = (2 * observed_AA + observed_AG) / (2 * total)  # Frequency of A allele
            q = 1 - p  # Frequency of G allele

            # Calculate expected frequencies based on Hardy-Weinberg equilibrium
            expected_AA = p**2 * total
            expected_AG = 2 * p * q * total
            expected_GG = q**2 * total

            # Perform Chi-Square test
            observed = [observed_AA, observed_AG, observed_GG]
            expected = [expected_AA, expected_AG, expected_GG]
            chi_square, p_value = chisquare(observed, expected)

            # Check if the population is in Hardy-Weinberg equilibrium
            if p_value > 0.05:
                equilibrium_status = "The population is in Hardy-Weinberg equilibrium."
            else:
                equilibrium_status = "The population is not in Hardy-Weinberg equilibrium."

            # Plotting the observed vs expected frequencies
            fig, ax = plt.subplots()
            ax.bar(['AA', 'AG', 'GG'], observed, width=0.4, label='Observed', align='center', alpha=0.7)
            ax.bar(['AA', 'AG', 'GG'], expected, width=0.4, label='Expected', align='edge', alpha=0.7)

            ax.set_xlabel('Genotype')
            ax.set_ylabel('Frequency')
            ax.set_title(f'Hardy-Weinberg Test: Observed vs Expected\nChi-Square = {chi_square:.2f}, p-value = {p_value:.4f}')
            ax.legend()

            # Save the plot to a BytesIO object and encode it in base64 for embedding in HTML
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plot_url = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()

    else:
        form = UploadCSVForm()

    return render(request, 'hardy_weinberg.html', {
        'form': form,
        'chi_square': chi_square,
        'p_value': p_value,
        'p': p,
        'q': q,
        'equilibrium_status': equilibrium_status,
        'plot_url': plot_url
    })



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

def chi_square_view(request):
    if request.method == 'POST':
        form = ChiSquareForm(request.POST)
        if form.is_valid():
            observed_AA = form.cleaned_data['observed_AA']
            observed_AG = form.cleaned_data['observed_AG']
            observed_GG = form.cleaned_data['observed_GG']
            expected_AA = form.cleaned_data['expected_AA']
            expected_AG = form.cleaned_data['expected_AG']
            expected_GG = form.cleaned_data['expected_GG']

            chi_square, p_value = perform_chi_square_test(observed_AA, observed_AG, observed_GG, expected_AA, expected_AG, expected_GG)

            # Plotting the observed vs expected frequencies
            observed = [observed_AA, observed_AG, observed_GG]
            expected = [expected_AA, expected_AG, expected_GG]

            # Create the plot
            fig, ax = plt.subplots()
            ax.bar(['AA', 'AG', 'GG'], observed, width=0.4, label='Observed', align='center', alpha=0.7)
            ax.bar(['AA', 'AG', 'GG'], expected, width=0.4, label='Expected', align='edge', alpha=0.7)

            ax.set_xlabel('Genotype')
            ax.set_ylabel('Frequency')
            ax.set_title(f'Chi-Square Test: Observed vs Expected\nChi-Square = {chi_square:.2f}, p-value = {p_value:.4f}')
            ax.legend()

            # Save the plot to a BytesIO object and encode it in base64 for embedding in HTML
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            plot_url = base64.b64encode(buf.read()).decode('utf-8')
            buf.close()

            return render(request, 'chi_square.html', {
                'chi_square': chi_square,
                'p_value': p_value,
                'plot_url': plot_url
            })
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
