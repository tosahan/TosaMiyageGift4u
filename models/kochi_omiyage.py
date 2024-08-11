from app import db
from datetime import datetime

class Kochi_omiyage(db.Model):
    __tablename__ = "kochi_omiyage"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255)) # product's name
    kinds = db.Column(db.String(255)) # kinds of product, sake or otsumami
    # kinds = db.Column(db.Boolean) # kinds of product, 0:sake, 1:otsumami
    price = db.Column(db.Integer) # price of product