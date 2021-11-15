from django import forms
from django.db import models
from django.forms import fields, ModelForm
from django.forms.forms import Form
from .models import UploadFile

class UploadForm(forms.Form):
    file = forms.FileField()