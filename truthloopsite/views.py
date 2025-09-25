from django.shortcuts import render
from .forms import MemeUploadForm

def upload_meme(request):
    uploaded = False
    if request.method == "POST":
        form = MemeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            uploaded = True
            form = MemeUploadForm()  # Reset form after successful upload
    else:
        form = MemeUploadForm()
    return render(request, "upload.html", {"form": form, "uploaded": uploaded})
