
from extensions import db
from models.item import Item
from sqlalchemy.exc import IntegrityError


class ItemService:
    """
    Service-Klasse für Artikel-Verwaltung.
    Enthält alle Business-Logik für Artikel.
    """
    
    @staticmethod
    def get_all(category_filter=None, search_query=None):
        """Gibt alle Artikel zurück, optional gefiltert."""
        query = Item.query
        
        if search_query:
            query = query.filter(
                (Item.name.ilike(f'%{search_query}%')) |
                (Item.sku.ilike(f'%{search_query}%')) |
                (Item.barcode == search_query)
            )
        
        if category_filter:
            query = query.filter(Item.category == category_filter)
        
        return query.order_by(Item.category.asc(), Item.subcategory.asc(), Item.name.asc()).all()
    
    @staticmethod
    def get_by_id(item_id):
        """Findet einen Artikel anhand seiner ID."""
        return Item.query.get(item_id)
    
    @staticmethod
    def get_by_barcode(barcode):
        """Findet einen Artikel anhand Barcode oder SKU."""
        return Item.query.filter(
            (Item.barcode == barcode) | (Item.sku == barcode)
        ).first()
    
    @staticmethod
    def create(name, sku, barcode=None, qty=0, min_qty=0, category='Sonstige', subcategory='', inventory_number=None, serial_number=None):
        """Erstellt einen neuen Artikel."""
        if not name or not sku:
            return False, 'Name und Artikelnummer (SKU) sind Pflicht.'
        
        try:
            item = Item(
                name=name,
                sku=sku,
                barcode=barcode or None,
                qty=qty,
                min_qty=min_qty,
                category=category,
                subcategory=subcategory,
                inventory_number=inventory_number or None,
                serial_number=serial_number or None
            )
            db.session.add(item)
            db.session.commit()
            return True, 'Artikel angelegt.'
        except IntegrityError:
            db.session.rollback()
            return False, 'SKU oder Barcode ist schon vergeben.'
    
    @staticmethod
    def update(item_id, name, sku, barcode=None, qty=0, min_qty=0, category='Sonstige', subcategory='', inventory_number=None, serial_number=None):
        """Aktualisiert einen bestehenden Artikel."""
        item = Item.query.get(item_id)
        if not item:
            return False, 'Artikel nicht gefunden.'
        
        if not name or not sku:
            return False, 'Name und Artikelnummer (SKU) sind Pflicht.'
        
        try:
            item.name = name
            item.sku = sku
            item.barcode = barcode or None
            item.qty = qty
            item.min_qty = min_qty
            item.category = category
            item.subcategory = subcategory
            item.inventory_number = inventory_number or None
            item.serial_number = serial_number or None
            db.session.commit()
            return True, 'Artikel aktualisiert.'
        except IntegrityError:
            db.session.rollback()
            return False, 'SKU oder Barcode ist schon vergeben.'
    
    @staticmethod
    def delete(item_id):
        """Löscht einen Artikel."""
        item = Item.query.get(item_id)
        if not item:
            return False, 'Artikel nicht gefunden.'
        
        try:
            db.session.delete(item)
            db.session.commit()
            return True, 'Artikel gelöscht.'
        except Exception:
            db.session.rollback()
            return False, 'Fehler beim Löschen.'
    
    @staticmethod
    def get_low_stock():
        """Gibt alle Artikel mit niedrigem Bestand zurück."""
        return Item.query.filter(Item.qty < Item.min_qty).all()
    
    @staticmethod
    def count_all():
        """Gibt die Gesamtanzahl der Artikel zurück"""
        from sqlalchemy import func
        return db.session.query(func.count(Item.id)).scalar()
    
    @staticmethod
    def count_low_stock():
        """Gibt die Anzahl der Artikel unter Mindestbestand zurück"""
        from sqlalchemy import func
        return db.session.query(func.count(Item.id)).filter(Item.qty < Item.min_qty).scalar()