from django import forms
from django.contrib.auth.models import User

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")

        return cleaned_data

# Form for Hardy-Weinberg Test
class HardyWeinbergForm(forms.Form):
    AA = forms.IntegerField(label='Observed AA', min_value=0)
    AG = forms.IntegerField(label='Observed AG', min_value=0)
    GG = forms.IntegerField(label='Observed GG', min_value=0)
    expected_AA = forms.IntegerField(label='Expected AA', min_value=0)
    expected_AG = forms.IntegerField(label='Expected AG', min_value=0)
    expected_GG = forms.IntegerField(label='Expected GG', min_value=0)

# Form for Allele Frequency Calculation
class AlleleFrequencyForm(forms.Form):
    AA = forms.IntegerField(label='AA', min_value=0)
    Aa = forms.IntegerField(label='Aa', min_value=0)
    N = forms.IntegerField(label='Total Population Size (N)', min_value=1)

# Form for Chi-Square Test
class ChiSquareForm(forms.Form):
    observed_AA = forms.IntegerField(label='Observed AA', min_value=0)
    observed_AG = forms.IntegerField(label='Observed AG', min_value=0)
    observed_GG = forms.IntegerField(label='Observed GG', min_value=0)
    expected_AA = forms.IntegerField(label='Expected AA', min_value=0)
    expected_AG = forms.IntegerField(label='Expected AG', min_value=0)
    expected_GG = forms.IntegerField(label='Expected GG', min_value=0)
 #Form for uploading CSV
class UploadCSVForm(forms.Form):
    csv_file = forms.FileField(label='Upload CSV File', required=True)

class AnovaForm(forms.Form):
    group1 = forms.CharField(widget=forms.Textarea, help_text="Enter data for Group 1 (comma-separated)")
    group2 = forms.CharField(widget=forms.Textarea, help_text="Enter data for Group 2 (comma-separated)")
    group3 = forms.CharField(required=False, widget=forms.Textarea, help_text="Enter data for Group 3 (optional, comma-separated)")

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Enter your email")
