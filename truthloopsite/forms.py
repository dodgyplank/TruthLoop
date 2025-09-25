from django import forms
from .models import MemeUpload

class MemeUploadForm(forms.ModelForm):
    class Meta:
        model = MemeUpload
        fields = ["image"]
