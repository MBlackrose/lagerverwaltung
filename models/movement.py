
from datetime import datetime
from extensions import db


class Movement(db.Model):
    """
    Klasse für Lagerbewegungen.
    Dokumentiert alle Ein- und Ausgänge mit Empfänger und Signatur.
    """
    __tablename__ = 'movements'
    
    # Primärschlüssel
    id = db.Column(db.Integer, primary_key=True)
    
    # Verknüpfung zum Artikel
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    
    # Bewegungsdaten
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100))
    ausgabe_typ = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Empfänger-Daten
    recipient_firstname = db.Column(db.String(100))
    recipient_lastname = db.Column(db.String(100))
    recipient_department = db.Column(db.String(100))
    recipient_email = db.Column(db.String(120))
    
    # IT-Mitarbeiter (der ausgibt)
    issuer_firstname = db.Column(db.String(100))
    issuer_lastname = db.Column(db.String(100))
    
    # Geräte-Details
    inventory_number = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    
    # Zusatzinfo
    has_keyboard = db.Column(db.Boolean, default=False)
    has_damage = db.Column(db.Boolean, default=False)
    damage_description = db.Column(db.Text)
    
    # Signatur & PDF
    signature = db.Column(db.Text)
    pdf_file = db.Column(db.String(200))
    
    # Beziehung zum Artikel
    item = db.relationship('Item', backref=db.backref('movements', lazy=True))
    
    def __repr__(self):
        """String-Repräsentation der Bewegung"""
        return f'<Movement {self.id}: {self.change}>'
    
    def is_incoming(self):
        """Prüft ob es ein Eingang ist"""
        return self.change > 0
    
    def is_outgoing(self):
        """Prüft ob es ein Ausgang ist"""
        return self.change < 0
    
    def get_recipient_name(self):
        """Gibt den vollen Empfänger-Namen zurück"""
        if self.recipient_firstname and self.recipient_lastname:
            return f'{self.recipient_firstname} {self.recipient_lastname}'
        return '—'
    
    def get_issuer_name(self):
        """Gibt den vollen IT-Mitarbeiter-Namen zurück"""
        if self.issuer_firstname and self.issuer_lastname:
            return f'{self.issuer_firstname} {self.issuer_lastname}'
        return '—'