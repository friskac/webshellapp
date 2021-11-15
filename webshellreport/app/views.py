from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage

# Create your views here.

def sayHello(request):
    return render(request, 'home.html')

def landingPage(request):
    return render(request, 'landingpage.html')

def upload_file(request):
    context = {}
    # form = UploadForm()
    if request.method == 'POST':
        uploadedfile = request.FILES['file']
        fs = FileSystemStorage()
        name = fs.save(uploadedfile.name, uploadedfile)
        # form = UploadForm(request.POST, request.FILES)
        print(name)
        context['url'] = fs.url(name)
    return render(request, 'upload.html', context)