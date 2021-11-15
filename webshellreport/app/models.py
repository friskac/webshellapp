from django.db import models, transaction
from django.conf import settings
from django.db.models.base import Model
import pandas as pd
from sqlalchemy import create_engine
import pymysql

# Create your models here.

user = settings.DATABASES['default']['USER']
password = settings.DATABASES['default']['PASSWORD']
database_name = settings.DATABASES['default']['NAME']
database_url = 'mysql+pymysql://{user}:{password}@localhost:3306/{database_name}'.format(
    user=user,
    password=password,
    database_name=database_name,
)

# engine = create_engine(database_url)
# df = pd.read_sql('SELECT * FROM table_name', con=engine)

class UploadFile(models.Model):
    file = models.FileField()

    def __str__(self):
        return self.file