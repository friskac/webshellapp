from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from app.models import WebshellDetector

# Create your views here.


def sayHello(request):
    return render(request, 'home.html')


def landingPage(request):
    return render(request, 'landingpage.html')


wsd = WebshellDetector()


def upload_file(request):
    filelog = ""
    context = {}
    if request.method == 'POST':
        if "uploadfile" in request.POST:
            uploadedfile = request.FILES['file']
            fs = FileSystemStorage()
            filelog = fs.save(uploadedfile.name, uploadedfile)
            # form = UploadForm(request.POST, request.FILES)
            # print(filelog)
            df = wsd.preprocess(fs.url(filelog))
            wsd.makeTree(df)
            name = wsd.exportTree(df)
            if name:
                context['url'] = "media/traintree.png"
        elif "predict" in request.POST:
            df = wsd.preprocess("media/c99.log")
            xtest, ypred = wsd.predict(df)
            akurasi, akurasiDataTest, akurasiPrediksi, totalData = wsd.checkAccuracy(
                df, ypred)
            print(akurasiPrediksi)
            context["akurasi"] = akurasi
            context["akurasiDataTest"] = akurasiDataTest
            context["Prediksi"] = akurasiPrediksi
            context["totalData"] = totalData

    return render(request, 'upload.html', context)
