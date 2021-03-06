import re
from django.db import models
from django.conf import settings
import pandas as pd
from sqlalchemy import create_engine
from sklearn.tree import export_graphviz
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pydotplus
import datetime

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

    def preprocess(self, file, source="local"):
        if source == "local":
            f = open(file, "r")
        else:
            f = file    
        percent = 0
        log = {
            'IP': [],
            'Date': [],
            'Request': [],
            'Byte': [],
            'Referer': [],
            'Browser': [],
            'PanjangParam': [],
            'PHP': [],
            'Percent': [],
            'JenisWebshell': []
        }
                # byte3 = byte2
                # if '\n' in byte3:
                #     byte3 = byte2.replace('\n', '') 
                # # if len(referer) < 4:
                #     referer2 = "-"
                #     browser2 = "-"
                # else:
                    # referer2 = referer[3]
                    # browser2 = browser[5]
        # try:
        for i in f:
            ip = i.split(" - - ")[0]
            date = i.split(" - - ")
            if len(date) > 1:
                date1 = date[1]
                date2 = date1.split("]")[0].replace("[", "")
                date3 = self.cleanup_time(date2)
                request = i.split('"')[1]
                byte = i.split('"')[2]
                byte2 = byte.split(" ")[2]
                if byte2 == "-":
                    byte2 = 0
                referer = i.split('"')[3]
                browser = i.split('"')[5]
                log['IP'].append(ip)
                log['Date'].append(date3)
                log['Request'].append(request)
                log['Byte'].append(byte2)
                log['Referer'].append(referer)
                log['Browser'].append(browser)
                jenis = "R57 atau WSO atau Tidak Ada"
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
                #     # print(param)
                    if "image=" in param or "action=" in param:
                    # webadmin
                        jenis = "webadmin"
                    elif "act=" in param or "%2C" in param or "img=" in param:
                        # c99
                        jenis = "c99"
                    elif "/upload" in request and ( "|" in param or "!" in param or "-" in param):
                        # b374k
                        jenis = "b374k"
                else:
                    # R57 atau WSO atau Tidak Ada
                    jenis = "R57 atau WSO atau Tidak Ada"
            log['PanjangParam'].append(panjangParam)
            log['PHP'].append(php)
            log['Percent'].append(percent)
            log['JenisWebshell'].append(jenis)
        df = pd.DataFrame(log)
        return df

    def cleanup_time(self, time):
        return datetime.datetime(int(time[7:11]), month_map[time[3:6]], int(time[0:2]),
                                 int(time[12:14]), int(time[15:17]), int(time[18:20]))

    def makeTree(self, df):
        xTrain = df.iloc[:, :4]
        yTrain = df.iloc[:, -1]
        print(xTrain)
        return self.dt.fit(xTrain, yTrain)

    def checkAccuracy(self, df, yPred):
        # df.loc[df.sample(frac=random.uniform(0, 0.1)).index,
        #        'JenisWebshell'] = "c99"
        yTest = df.iloc[:, -1]
        akurasi = accuracy_score(yTest, yPred)
        akurasiDataTest = self.dt.score(df.iloc[:, :4], yTest)
        akurasiPrediksi = accuracy_score(yTest, yPred, normalize=False)
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
    def insertData(self, df):
        con = engine.connect()
        for i, row in df.iterrows():
            query = "SELECT `idWebshell` FROM `Webshell` WHERE `JenisWebshell` = %s"
            jenisWebshell = row["JenisWebshell"]
            res = con.execute(query, jenisWebshell)
            idWebshell = res.fetchone()[0]
            df.loc[i, "JenisWebshell"] = idWebshell
            # print(df.loc[i])
            sql = "INSERT INTO `Log` (`alamat_ip`, `date`, `request`, `byte`, `referer`, `browser`,`panjang_param`,`is_php`,`is_percent`, `idW`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            con.execute(sql, df.loc[i])
        con.close()

    def getData(self, filter):
        con = engine.connect()
        query = "SELECT `alamat_ip`, CAST(`date` AS CHAR) AS 'Date', `request`, `byte` AS 'Byte', `panjang_param` AS 'PanjangParam',`is_php` AS 'PHP',`is_percent` AS 'Percent', `JenisWebshell` FROM `Log` INNER JOIN `Webshell` ON `Log`.`idW` = `Webshell`.`idWebshell`"
        if len(filter) > 0:
            query += " WHERE "
            firstFilter = True
            for key in filter:
                if not firstFilter:
                    query += ' AND '
                if key == "id":
                    query += "`Log`.`idW` = " + filter["id"]
                elif key == "ip":
                    query += "`Log`.`alamat_ip` = '" + filter["ip"] + "'"
                elif key == "waktu":
                    startVal = filter["waktu"].split(" - ")[0]
                    endVal = filter["waktu"].split(" - ")[1]
                    startDate = startVal.split(" ")[0]
                    startMonth = month_map[startVal.split(" ")[1]]
                    startYear = startVal.split(" ")[2]
                    startTime = startVal.split(" ")[3]
                    endDate = endVal.split(" ")[0]
                    endMonth = month_map[endVal.split(" ")[1]]
                    endYear = endVal.split(" ")[2]
                    endTime = endVal.split(" ")[3]
                    start = str(startYear) + "-" + str(startMonth) + "-" + str(startDate) + " " + str(startTime)
                    end = str(endYear) + "-" + str(endMonth) + "-" + str(endDate) + " " + str(endTime)
                    query += "`Log`.`date` BETWEEN '" + start + "' AND '" + end + "'"
                firstFilter = False
        query += " ORDER BY `Log`.`date` ASC"
        print(query)
        # res = con.execute(query)
        df = pd.read_sql_query(query, con)
        return df

    def exportIP(self):
        con = engine.connect()
        query = "SELECT DISTINCT(`Log`.`alamat_ip`) FROM `Log`"
        list_ip = pd.read_sql_query(query, con)
        con.close()
        return list_ip
