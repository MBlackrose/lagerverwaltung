
import unittest
from app import app
from extensions import db
from models.item import Item


class TestLagerverwaltung(unittest.TestCase):
    """Meine Tests für die Lagerverwaltung"""
    
    def setUp(self):
        # Test-Datenbank im Speicher erstellen
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        # Nach dem Test aufräumen
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_artikel_anlegen(self):
        # Teste ob ich einen Artikel anlegen kann
        with app.app_context():
            artikel = Item(
                name='Dell Monitor',
                sku='MON-001',
                qty=5,
                min_qty=2
            )
            db.session.add(artikel)
            db.session.commit()
            
            # Artikel wieder suchen
            gefunden = Item.query.filter_by(sku='MON-001').first()
            
            # Prüfen ob er existiert
            self.assertIsNotNone(gefunden)
            self.assertEqual(gefunden.name, 'Dell Monitor')
    
    def test_bestand_aendert_sich(self):
        # Teste ob der Bestand sich ändert
        with app.app_context():
            artikel = Item(name='Maus', sku='MAUS-001', qty=10)
            db.session.add(artikel)
            db.session.commit()
            
            # Bestand reduzieren (Ausgabe)
            artikel.qty = artikel.qty - 1
            db.session.commit()
            
            # Prüfen
            self.assertEqual(artikel.qty, 9)
    
    def test_login_seite_geht(self):
        # Teste ob die Login-Seite funktioniert
        antwort = self.client.get('/login')
        self.assertEqual(antwort.status_code, 200)
    
    def test_niedriger_bestand(self):
        # Teste ob niedriger Bestand erkannt wird
        with app.app_context():
            artikel = Item(name='Kabel', sku='KAB-001', qty=1, min_qty=5)
            db.session.add(artikel)
            db.session.commit()
            
            # Ist Bestand unter Minimum?
            ist_niedrig = artikel.qty < artikel.min_qty
            self.assertTrue(ist_niedrig)


if __name__ == '__main__':
    print("Starte Tests...")
    unittest.main()