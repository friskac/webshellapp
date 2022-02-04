from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from app.models import WebshellDetector, Exporter
import json, paramiko
from paramiko import sftp, sftp_client
from django.conf import settings

# Create your views here.


exporter = Exporter()
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
                context['url'] = "/app/media/traintree.png"

    return render(request, 'upload.html', context)

def table(request):
    context = {}
    filter = {}
    if "webshell" in request.GET:
        idW = request.GET["webshell"]
        try:
            ip = request.GET["alamatip"]
        except:
            ip = ''
        try:
            waktu = request.GET["waktu"]
        except:
            waktu = ''
        if idW != "Semua":
            filter["id"] = idW
        if ip != "":
            filter["ip"] = ip
        if waktu != "":
            filter["waktu"] = waktu
    # file = "media/access.log"
    # df = wsd.preprocess(file)
    df = exporter.getData(filter)
    data = []
    if (len(df) != 0):
        list_ip = exporter.exportIP()
        xtest, ypred = wsd.predict(df[predictor])
        akurasi, akurasiDataTest, akurasiPrediksi, totalData = wsd.checkAccuracy(
            df[predictor], ypred)
        df["hasil"] = ypred
        context["akurasi"] = akurasi
        context["akurasiDataTest"] = "{:.2f}".format(akurasiDataTest*100)
        context["Prediksi"] = akurasiPrediksi
        context["totalData"] = totalData
        json_ip = list_ip.to_json(orient='records')
        context["listIp"] = json.loads(json_ip)

        json_records = df.to_json(orient='records', date_format="iso")
        data = json.loads(json_records)
    context["data"] = data
    return render(request, 'home.html', context)


# file = "media/ssl_access_log"
# df = wsd.preprocess(file, "local")
# exporter.insertData(df)

# user = settings.CLIENT['default']['USER']
# password = settings.CLIENT['default']['PASSWORD']
# clientIP = settings.CLIENT['default']['NAME']
# filePath = settings.CLIENT['default']['FILEPATH']

# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect(clientIP, username=user, password=password)
# sftp_client = client.open_sftp()
# remote_file = sftp_client.open(filePath)
# try:
#     df = wsd.preprocess(remote_file, "remote")
#     exporter.insertData(df)
# finally:
#     remote_file.close()