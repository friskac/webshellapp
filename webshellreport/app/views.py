from os import name
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from app.models import WebshellDetector, Exporter
import json

# Create your views here.

wsd = WebshellDetector()
predictor = ['Byte', 'PanjangParam', 'PHP', 'Percent', 'JenisWebshell']


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
            wsd.makeTree(df[predictor])
            name = wsd.exportTree(df[predictor])
            if name:
                context['url'] = "media/traintree.png"

    return render(request, 'upload.html', context)

# /index


def table(request):
    exporter = Exporter()
    context = {}
    file = "media/access.log"
    df = wsd.preprocess(file)
    exporter.insertData(df)
    xtest, ypred = wsd.predict(df[predictor])
    akurasi, akurasiDataTest, akurasiPrediksi, totalData = wsd.checkAccuracy(
        df[predictor], ypred)
    print(akurasiPrediksi)
    context["akurasi"] = akurasi
    context["akurasiDataTest"] = akurasiDataTest
    context["Prediksi"] = akurasiPrediksi
    context["totalData"] = totalData
    json_records = df.reset_index().to_json(orient='records')
    data = []
    data = json.loads(json_records)
    context["data"] = data
    return render(request, 'home.html', context)
