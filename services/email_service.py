
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os


class EmailService:
    """Service für E-Mail-Versand von Empfangsbestätigungen"""
    
    # TEST-KONFIGURATION (später anpassen)
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USER = ''  # Deine Test-E-Mail
    SMTP_PASSWORD = ''  # App-Passwort von Gmail
    
    @classmethod
    def send_receipt(cls, recipient_email, recipient_name, pdf_path):
        """
        Sendet die Empfangsbestätigung per E-Mail.
        
        Args:
            recipient_email: E-Mail des Empfängers
            recipient_name: Name des Empfängers
            pdf_path: Pfad zur PDF-Datei
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Prüfen ob Konfiguration vorhanden
        if not cls.SMTP_USER or not cls.SMTP_PASSWORD:
            return False, 'E-Mail nicht konfiguriert (Test-Modus)'
        
        if not recipient_email:
            return False, 'Keine Empfänger-E-Mail angegeben'
        
        if not os.path.exists(pdf_path):
            return False, 'PDF-Datei nicht gefunden'
        
        try:
            # E-Mail erstellen
            msg = MIMEMultipart()
            msg['From'] = cls.SMTP_USER
            msg['To'] = recipient_email
            msg['Subject'] = 'Ihre Empfangsbestätigung - IT-Lagerverwaltung'
            
            # E-Mail Text
            body = f"""
Guten Tag {recipient_name},

anbei erhalten Sie Ihre Empfangsbestätigung für die erhaltenen IT-Geräte.

Bitte bewahren Sie dieses Dokument für Ihre Unterlagen auf.

Mit freundlichen Grüßen
IT-Abteilung
Landratsamt Lörrach
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # PDF anhängen
            with open(pdf_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename=Empfangsbestaetigung.pdf'
                )
                msg.attach(part)
            
            # E-Mail senden
            server = smtplib.SMTP(cls.SMTP_SERVER, cls.SMTP_PORT)
            server.starttls()
            server.login(cls.SMTP_USER, cls.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True, f'E-Mail gesendet an {recipient_email}'
        
        except Exception as e:
            return False, f'E-Mail-Fehler: {str(e)}'