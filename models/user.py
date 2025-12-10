
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    Klasse für Benutzer/IT-Mitarbeiter.
    Verwaltet Login-Daten und Mitarbeiter-Informationen.
    """
    __tablename__ = 'users'
    
    # Primärschlüssel
    id = db.Column(db.Integer, primary_key=True)
    
    # Login-Daten
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    # Mitarbeiter-Informationen
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))
    
    def __repr__(self):
        """String-Repräsentation des Benutzers"""
        return f'<User {self.username}>'
    
    def set_password(self, password):
        """
        Verschlüsselt und speichert das Passwort.
        
        Args:
            password: Klartext-Passwort
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Prüft ob das eingegebene Passwort korrekt ist.
        
        Args:
            password: Eingegebenes Klartext-Passwort
        
        Returns:
            bool: True wenn korrekt, False wenn falsch
        """
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """
        Gibt den vollen Namen zurück.
        
        Returns:
            str: Vorname + Nachname oder Username falls leer
        """
        if self.firstname and self.lastname:
            return f'{self.firstname} {self.lastname}'
        return self.username