from django.db import connection, models, transaction
from django.conf import settings
from django.db.models.base import Model
from numpy import dtype, mod
import pandas as pd
from sklearn import metrics
from sklearn import tree
from sqlalchemy import create_engine, text
import mysql.connector
import pymysql
from sklearn.tree import export_graphviz
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pydotplus
from dateutil import parser

from django.core.files.storage import FileSystemStorage
import datetime
import random

# Create your models here.

user = settings.DATABASES['default']['USER']
password = settings.DATABASES['default']['PASSWORD']
database_name = settings.DATABASES['default']['NAME']
database_url = 'mysql+pymysql://{user}:{password}@localhost:3306/{database_name}'.format(
    user=user,
    password=password,
    database_name=database_name,
)

engine = create_engine(database_url)
# df = pd.read_sql('SELECT * FROM table_name', con=engine)

month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7,
             'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}


class WebshellDetector:

    def __init__(self):
        self.dt = DecisionTreeClassifier(criterion="entropy")

    def preprocess(self, file):
        print(file)
        f = open(file, "r")
        percent = 0
        log = {
            'IP': [],
            'Date': [],
            'Request': [],
            'Byte': [],
            'Referer': [],
            'Browser': [],
            # 'Parameter': [],
            'PanjangParam': [],
            'PHP': [],
            'Percent': [],
            'JenisWebshell': []
        }
        # try:
        for i in f:
            ip = i.split(" - - ")[0]
            date = i.split(" - - ")
            if len(date) > 1:
                date1 = date[1]
                date2 = date1.split("]")[0].replace("[", "")
                date3 = self.cleanup_time(date2)
                # print(date3)
                request = i.split('"')[1]
                byte = i.split('"')[2]
                byte2 = byte.split(" ")[2]
                if byte2 == "-":
                    continue
                referer = i.split('"')[3]
                browser = i.split('"')[5]
                log['IP'].append(ip)
                log['Date'].append(date3)
                log['Request'].append(request)
                log['Byte'].append(byte2)
                log['Referer'].append(referer)
                log['Browser'].append(browser)
                jenis = "R57 atau WSO atau Tidak Ada"
                # paramAksi = "tidak ada"
                panjangParam = 0
                php = 0
                if '%' in request:
                    percent = 1
                else:
                    percent = 0
                if '.php' in request:
                    php = 1
                else:
                    php = 0
                if '?' in request:
                    param = request.split('?')[1]
                    panjangParam = len(param)
                    # print(param)
                    if "image=" in param or "action=" in param:
                        # webadmin
                        jenis = "webadmin"
                        # paramAksi = "image= atau action="
                    elif "act=" in param or "%2C" in param:
                        # c99
                        jenis = "c99"
                        # paramAksi = "act="
                    elif "|" in param or "!" in param or "-" in param:
                        # b374k
                        jenis = "b374k"
                        # paramAksi = "| atau !"
                else:
                    # R57 atau WSO atau Tidak Ada
                    jenis = 0
                # log['Parameter'].append(paramAksi)
                log['PanjangParam'].append(panjangParam)
                log['PHP'].append(php)
                log['Percent'].append(percent)
                log['JenisWebshell'].append(jenis)

        df = pd.DataFrame(log)
        # data = ['Byte', 'PanjangParam', 'PHP', 'Percent', 'JenisWebshell']
        # print(df[data])
        # df.to_sql('Log2', con=engine)
        # engine.execute("SELECT * FROM Log").fetchall()
        return df

    def cleanup_time(self, time):
        return datetime.datetime(int(time[7:11]), month_map[time[3:6]], int(time[0:2]),
                                 int(time[12:14]), int(time[15:17]), int(time[18:20]))

    def makeTree(self, df):
        xTrain = df.iloc[:, :4]
        yTrain = df.iloc[:, -1]
        return self.dt.fit(xTrain, yTrain)

    def checkAccuracy(self, df, yPred):
        df.loc[df.sample(frac=random.uniform(0, 0.1)).index,
               'JenisWebshell'] = "c99"
        yTest = df.iloc[:, -1]
        akurasi = accuracy_score(yTest, yPred)
        akurasiDataTest = self.dt.score(df.iloc[:, :4], yTest)
        akurasiPrediksi = accuracy_score(yTest, yPred, normalize=False)
        print(accuracy_score(yTest, yPred, normalize=False))
        return akurasi, akurasiDataTest, akurasiPrediksi, len(yTest)

    def predict(self, df):
        xTest = df.iloc[:, :4]
        yPred = self.dt.predict(xTest)
        return xTest, yPred

    def exportTree(self, df):
        sel_col = df.iloc[:, :4].columns
        dot_data = export_graphviz(
            self.dt,
            out_file=None,
            feature_names=sel_col,
            filled=True,
            rounded=True,
            special_characters=True)
        graph = pydotplus.graph_from_dot_data(dot_data)
        image = graph.write_png("media/traintree.png")
        return image


class Exporter(models.Model):
    # ip = models.CharField(max_length=20)
    # date = models.DateField()
    # req = models.CharField(max_length=300)
    # kode = models.IntegerField()
    # byte = models.BigIntegerField()
    # ref = models.CharField(max_length=300)
    # browser = models.CharField(max_length=300)
    # webshell = models.CharField(max_length=30)

    # connection = pymysql.connect(
    #     host='localhost',
    #     user='root',
    #     password='mikLovers*19',
    #     db='webshell_data'
    # )
    def insertData(self, df):
        con = engine.connect()
        for i, row in df.iterrows():
            query = "SELECT `idWebshell` FROM `Webshell` WHERE `JenisWebshell` = %s"
            jenisWebshell = row["JenisWebshell"]
            res = con.execute(query, jenisWebshell)
            idWebshell = res.fetchone()[0]
            df.loc[i, "JenisWebshell"] = idWebshell
            print(df.loc[i])
            sql = "INSERT INTO `Log` (`alamat_ip`, `date`, `request`, `byte`, `referer`, `browser`,`panjang_param`,`php`,`percent`, `idW`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            con.execute(sql, df.loc[i])
        con.close()
