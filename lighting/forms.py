"""
Forms for AutoLight Analyser application
"""
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json

from .models import CADFile, LightingCatalog


class CADUploadForm(forms.ModelForm):
    """Form for uploading CAD files"""
    
    legend_json = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': '{"CAD_SYMBOL_1": "CATALOG_NAME_1", "CAD_SYMBOL_2": "CATALOG_NAME_2"}',
            'class': 'form-control'
        }),
        help_text='Optional: Provide a JSON mapping of CAD symbols to catalog names'
    )
    
    class Meta:
        model = CADFile
        fields = ['project_name', 'file']
        widgets = {
            'project_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project name'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.dwg,.dxf'}),
        }
    
    def clean_file(self):
        """Validate uploaded file"""
        file = self.cleaned_data.get('file')
        if file:
            # Check file extension
            filename = file.name.lower()
            if not (filename.endswith('.dwg') or filename.endswith('.dxf')):
                raise ValidationError('Only .dwg and .dxf files are allowed.')
            
            # Check file size (max 50MB)
            if file.size > 50 * 1024 * 1024:
                raise ValidationError('File size must not exceed 50MB.')
        
        return file
    
    def clean_legend_json(self):
        """Validate and parse legend JSON"""
        legend_json = self.cleaned_data.get('legend_json')
        if legend_json:
            try:
                legend = json.loads(legend_json)
                if not isinstance(legend, dict):
                    raise ValidationError('Legend must be a JSON object (dictionary).')
                return legend
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON format.')
        return None
    
    def cleaned_data_with_legend(self):
        """Get cleaned data with parsed legend"""
        data = super().clean()
        data['legend'] = self.clean_legend_json()
        return data


class UserRegistrationForm(forms.ModelForm):
    """Form for user registration"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        min_length=8
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )
    role = forms.ChoiceField(
        choices=[
            ('Architect', 'Architect'),
            ('Vendor', 'Vendor'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='Architect'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }
    
    def clean_password_confirm(self):
        """Validate password confirmation"""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError('Passwords do not match.')
        
        return password_confirm
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email


class LightingCatalogForm(forms.ModelForm):
    """Form for adding/editing lighting catalog entries"""
    
    class Meta:
        model = LightingCatalog
        fields = ['symbol_name', 'model_number', 'brand', 'lumens', 'wattage', 
                  'beam_angle', 'color_temp', 'unit_cost', 'image']
        widgets = {
            'symbol_name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_number': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'lumens': forms.NumberInput(attrs={'class': 'form-control'}),
            'wattage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'beam_angle': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'color_temp': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
