
from flask import session
from models.item import Item


class CartService:
    """
    Service-Klasse für den Warenkorb.
    Verwaltet alle Warenkorb-Operationen.
    """
    
    def __init__(self):
        """Initialisiert den Warenkorb aus der Session"""
        if 'cart' not in session:
            session['cart'] = []
    
    def get_items(self):
        """
        Gibt alle Artikel im Warenkorb zurück.
        
        Returns:
            list: Liste mit Artikel-Objekten und Mengen
        """
        cart_items = []
        for cart_item in session.get('cart', []):
            item = Item.query.get(cart_item['item_id'])
            if item:
                cart_items.append({
                    'item': item,
                    'quantity': cart_item['quantity']
                })
        return cart_items
    
    def add_item(self, barcode, quantity=1, check_stock=True):
        """
        Fügt einen Artikel zum Warenkorb hinzu.
        
        Args:
            barcode: Barcode oder SKU des Artikels
            quantity: Menge (Standard: 1)
            check_stock: Bestand prüfen? (False bei Rückgabe)
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not barcode:
            return False, 'Barcode ist leer'
        
        # Artikel suchen
        item = Item.query.filter(
            (Item.barcode == barcode) | (Item.sku == barcode)
        ).first()
        
        if not item:
            return False, f'Artikel mit Barcode/SKU "{barcode}" nicht gefunden'
        
        # Prüfen ob genug Bestand (nur bei Ausgabe, nicht bei Rückgabe)
        if check_stock and item.qty < quantity:
            return False, f'Nicht genug Bestand! Verfügbar: {item.qty}'
        
        # Zum Warenkorb hinzufügen
        cart = session.get('cart', [])
        
        # Prüfen ob Artikel schon im Warenkorb
        found = False
        for cart_item in cart:
            if cart_item['item_id'] == item.id:
                cart_item['quantity'] += quantity
                found = True
                break
        
        if not found:
            cart.append({
                'item_id': item.id,
                'item_name': item.name,
                'quantity': quantity
            })
        
        session['cart'] = cart
        session.modified = True
        
        return True, f'{quantity}x {item.name} zum Warenkorb hinzugefügt'
    
    def remove_item(self, item_id):
        """
        Entfernt einen Artikel aus dem Warenkorb.
        
        Args:
            item_id: ID des zu entfernenden Artikels
        """
        if 'cart' in session:
            session['cart'] = [c for c in session['cart'] if c['item_id'] != item_id]
            session.modified = True
    
    def clear(self):
        """Leert den kompletten Warenkorb"""
        session['cart'] = []
        session.modified = True
    
    def get_count(self):
        """
        Gibt die Anzahl der Artikel im Warenkorb zurück.
        
        Returns:
            int: Anzahl der verschiedenen Artikel
        """
        return len(session.get('cart', []))
    
    def is_empty(self):
        """
        Prüft ob der Warenkorb leer ist.
        
        Returns:
            bool: True wenn leer
        """
        return len(session.get('cart', [])) == 0
    
    def get_raw(self):
        """
        Gibt die rohen Warenkorb-Daten zurück.
        
        Returns:
            list: Rohe Session-Daten
        """
        return session.get('cart', [])