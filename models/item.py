
from datetime import datetime
from extensions import db


class Item(db.Model):
    """
    Klasse für Artikel im Lager.
    Repräsentiert alle Hardware-Produkte mit Kategorie und Bestand.
    """
    __tablename__ = 'items'
    
    # Primärschlüssel
    id = db.Column(db.Integer, primary_key=True)
    
    # Artikel-Informationen
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=True)
    barcode = db.Column(db.String(64), unique=True, nullable=True)
    
    # Bestand
    qty = db.Column(db.Integer, nullable=False, default=0)
    min_qty = db.Column(db.Integer, nullable=False, default=0)
    
    # Kategorie & Unterkategorie
    category = db.Column(db.String(50), default='Sonstige')
    subcategory = db.Column(db.String(100), default='')
    
    # Zeitstempel
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        """String-Repräsentation des Artikels"""
        return f'<Item {self.name}>'
    
    def is_low_stock(self):
        """Prüft ob Bestand unter Minimum ist"""
        return self.qty < self.min_qty
    
    def update_stock(self, change):
        """
        Aktualisiert den Bestand.
        
        Args:
            change: Positive Zahl = Zugang, Negative Zahl = Abgang
        
        Returns:
            bool: True wenn erfolgreich, False wenn Bestand negativ würde
        """
        if self.qty + change < 0:
            return False
        self.qty += change
        return True