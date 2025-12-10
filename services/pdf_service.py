
import os
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO


class PDFService:
    """Service für PDF-Generierung von Empfangsbestätigungen"""
    
    PDF_FOLDER = 'static/pdfs'
    
    @classmethod
    def create_receipt(cls, movement, item):
        """
        Erstellt eine PDF-Empfangsbestätigung.
        Gibt den Dateipfad zurück.
        """
        # Ordner erstellen falls nicht vorhanden
        os.makedirs(cls.PDF_FOLDER, exist_ok=True)
        
        # Dateiname generieren
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"empfangsbestaetigung_{movement.id}_{timestamp}.pdf"
        filepath = os.path.join(cls.PDF_FOLDER, filename)
        
        # PDF erstellen
        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # Header
        c.setFont("Helvetica-Bold", 20)
        c.drawString(2*cm, height - 2*cm, "Empfangsbestätigung")
        
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, height - 2.8*cm, f"IT-Lagerverwaltung | Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # Linie
        c.line(2*cm, height - 3.2*cm, width - 2*cm, height - 3.2*cm)
        
        # Artikel-Info
        y = height - 4.5*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Artikel-Informationen")
        
        c.setFont("Helvetica", 11)
        y -= 0.7*cm
        c.drawString(2*cm, y, f"Artikel: {item.name}")
        y -= 0.5*cm
        c.drawString(2*cm, y, f"SKU: {item.sku}")
        y -= 0.5*cm
        c.drawString(2*cm, y, f"Menge: {abs(movement.change)}")
        
        if movement.inventory_number:
            y -= 0.5*cm
            c.drawString(2*cm, y, f"Inventarnummer: {movement.inventory_number}")
        
        if movement.serial_number:
            y -= 0.5*cm
            c.drawString(2*cm, y, f"Seriennummer: {movement.serial_number}")
        
        # Empfänger
        y -= 1.2*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Empfänger")
        
        c.setFont("Helvetica", 11)
        y -= 0.7*cm
        c.drawString(2*cm, y, f"Name: {movement.get_recipient_name()}")
        y -= 0.5*cm
        c.drawString(2*cm, y, f"Abteilung: {movement.recipient_department or '—'}")
        y -= 0.5*cm
        c.drawString(2*cm, y, f"E-Mail: {movement.recipient_email or '—'}")
        
        # IT-Mitarbeiter
        y -= 1.2*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Ausgegeben von")
        
        c.setFont("Helvetica", 11)
        y -= 0.7*cm
        c.drawString(2*cm, y, f"IT-Mitarbeiter: {movement.get_issuer_name()}")
        
        # Zusatzinfos
        if movement.has_keyboard or movement.has_damage:
            y -= 1.2*cm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2*cm, y, "Zusatzinformationen")
            
            c.setFont("Helvetica", 11)
            y -= 0.7*cm
            c.drawString(2*cm, y, f"Tastatur vorhanden: {'Ja' if movement.has_keyboard else 'Nein'}")
            y -= 0.5*cm
            c.drawString(2*cm, y, f"Mängel: {'Ja' if movement.has_damage else 'Nein'}")
            
            if movement.damage_description:
                y -= 0.5*cm
                c.drawString(2*cm, y, f"Beschreibung: {movement.damage_description}")
        
        # Signatur
        y -= 1.5*cm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(2*cm, y, "Unterschrift Empfänger")
        
        y -= 0.5*cm
        c.line(2*cm, y, 8*cm, y)
        
        # Signatur-Bild einfügen falls vorhanden
        if movement.signature and movement.signature.startswith('data:image'):
            try:
                # Base64 zu Bild konvertieren
                sig_data = movement.signature.split(',')[1]
                sig_bytes = base64.b64decode(sig_data)
                sig_image = ImageReader(BytesIO(sig_bytes))
                
                # Signatur zeichnen
                c.drawImage(sig_image, 2*cm, y - 2.5*cm, width=6*cm, height=2*cm, preserveAspectRatio=True)
            except Exception as e:
                print(f"Signatur-Fehler: {e}")
        
        # Footer
        c.setFont("Helvetica", 8)
        c.drawString(2*cm, 1.5*cm, f"Dokument erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}")
        c.drawString(2*cm, 1*cm, "IT-Lagerverwaltung - Landratsamt Lörrach")
        
        # PDF speichern
        c.save()
        
        return filepath