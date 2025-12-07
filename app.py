from functools import wraps
from datetime import datetime
import os

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

# -------- Basis / DB --------
db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))


# -------- KATEGORIEN MIT UNTERKATEGORIEN --------
KATEGORIEN = {
    'Monitor': ['Dell', 'Asus', 'HP', 'Lenovo'],
    'Docking Station': ['Dell', 'Lenovo'],
    'Tastatur': ['Logitech', 'Cherry', 'Microsoft'],
    'Maus': ['Logitech', 'HP', 'Microsoft'],
    'Headsets': [
        'Binaurale Headsets Ständer',
        'Binaurale Headsets USB-A',
        'Binaurale Headsets',
        'Monaurale Headsets',
        'Netzteil 4,5W Ständer Mono Headset',
        'Headset Telefon-USB alt',
        'Telefon Headsets kabellos'
    ],
    'Kabel': [
        'USB-C Kabel',
        'Netzwerkkabel 20m',
        'Netzwerkkabel 15m',
        'Netzwerkkabel 10m',
        'Netzwerkkabel 5m',
        'Netzwerkkabel 3m',
        'Netzwerkkabel 2m',
        'Netzwerkkabel 1m',
        'Netzwerkkabel 0.5m',
        'Displayportkabel',
        'Kaltgerätestecker',
        'Mehrfachsteckdose 1-fach',
        'Mehrfachsteckdose 2-fach',
        'Eurostecker',
        'HDMI Kabel',
        'Netzteil Lenovo Docking 90W',
        'Netzteil Tischscanner',
        'USB-A auf USB-B Kabel Drucker'
    ]
}


# -------- Modelle --------
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=True)
    barcode = db.Column(db.String(64), unique=True, nullable=True)
    qty = db.Column(db.Integer, nullable=False, default=0)
    min_qty = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='Sonstige')
    subcategory = db.Column(db.String(100), default='')


class Movement(db.Model):
    __tablename__ = 'movements'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ausgabe-Typ
    ausgabe_typ = db.Column(db.String(50))
    
    # Empfänger-Daten
    recipient_firstname = db.Column(db.String(100))
    recipient_lastname = db.Column(db.String(100))
    recipient_department = db.Column(db.String(100))
    recipient_email = db.Column(db.String(120))
    
    # IT-Mitarbeiter
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
    
    item = db.relationship('Item', backref=db.backref('movements', lazy=True))


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    firstname = db.Column(db.String(100))
    lastname = db.Column(db.String(100))

    def set_password(self, pw: str):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw: str) -> bool:
        return check_password_hash(self.password_hash, pw)


# -------- App-Factory --------
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'change-me-in-.env'

    db_dir = os.path.join(basedir, "database")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "lager.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    return app


app = create_app()


# -------- Login-Hilfen --------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.before_request
def load_logged_in_user():
    g.user = None
    uid = session.get('user_id')
    if uid:
        g.user = User.query.get(uid)


# -------- ROUTES --------

@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/initdb')
def initdb():
    os.makedirs('database', exist_ok=True)
    db.create_all()
    return "DB initialisiert."


@app.route('/health')
def health():
    return 'OK'


# API für Unterkategorien (JavaScript)
@app.route('/api/subcategories/<category>')
def get_subcategories(category):
    subcategories = KATEGORIEN.get(category, [])
    return jsonify(subcategories)


# ---- AUTH ROUTES ----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            flash(f'Willkommen, {username}!', 'success')
            return redirect(request.args.get('next') or url_for('dashboard'))
        
        flash('Login fehlgeschlagen.', 'error')
        return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        firstname = (request.form.get('firstname') or '').strip()
        lastname = (request.form.get('lastname') or '').strip()
        password = request.form.get('password') or ''
        password_confirm = request.form.get('password_confirm') or ''

        if not username or not password:
            flash('Benutzername und Passwort sind Pflicht.', 'error')
            return redirect(url_for('register'))

        if len(username) < 3:
            flash('Benutzername muss mindestens 3 Zeichen lang sein.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Passwort muss mindestens 6 Zeichen lang sein.', 'error')
            return redirect(url_for('register'))

        if password != password_confirm:
            flash('Passwörter stimmen nicht überein.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Benutzer existiert bereits.', 'error')
            return redirect(url_for('register'))

        try:
            user = User(username=username, firstname=firstname, lastname=lastname)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Benutzer erfolgreich erstellt! Bitte melden Sie sich an.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Fehler beim Erstellen des Benutzers.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Abgemeldet.', 'success')
    return redirect(url_for('login'))


@app.route('/initadmin')
def initadmin():
    if User.query.filter_by(username='admin').first():
        return 'Admin existiert bereits.'
    u = User(username='admin', firstname='Admin', lastname='User')
    u.set_password('admin123')
    db.session.add(u)
    db.session.commit()
    return 'Admin angelegt: admin / admin123'


# ---- ITEMS ROUTES ----
@app.route('/items')
@login_required
def items_list():
    q = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    query = Item.query
    
    if q:
        query = query.filter(
            (Item.name.ilike(f'%{q}%')) |
            (Item.sku.ilike(f'%{q}%')) |
            (Item.barcode == q)
        )
    
    if category_filter:
        query = query.filter(Item.category == category_filter)
    
    items = query.order_by(Item.category.asc(), Item.subcategory.asc(), Item.name.asc()).all()
    
    return render_template('items_list.html', items=items, search_query=q, 
                          kategorien=KATEGORIEN, selected_category=category_filter)


@app.route('/items/new', methods=['GET', 'POST'])
@login_required
def items_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip()
        barcode = (request.form.get('barcode') or '').strip() or None
        qty = int(request.form.get('qty', 0) or 0)
        min_qty = int(request.form.get('min_qty', 0) or 0)
        category = request.form.get('category', 'Sonstige')
        subcategory = request.form.get('subcategory', '')

        if not name or not sku:
            flash('Name und Artikelnummer (SKU) sind Pflicht.', 'error')
            return redirect(url_for('items_new'))

        try:
            item = Item(name=name, sku=sku, barcode=barcode, qty=qty, 
                       min_qty=min_qty, category=category, subcategory=subcategory)
            db.session.add(item)
            db.session.commit()
            flash('Artikel angelegt.', 'success')
            return redirect(url_for('items_list'))
        except IntegrityError:
            db.session.rollback()
            flash('SKU oder Barcode ist schon vergeben.', 'error')
            return redirect(url_for('items_new'))

    return render_template('items_new.html', kategorien=KATEGORIEN)


@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def items_edit(item_id):
    item = Item.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item.name = request.form.get('name', '').strip()
        item.sku = request.form.get('sku', '').strip()
        item.barcode = (request.form.get('barcode') or '').strip() or None
        item.qty = int(request.form.get('qty', 0) or 0)
        item.min_qty = int(request.form.get('min_qty', 0) or 0)
        item.category = request.form.get('category', 'Sonstige')
        item.subcategory = request.form.get('subcategory', '')
        
        if not item.name or not item.sku:
            flash('Name und Artikelnummer (SKU) sind Pflicht.', 'error')
            return redirect(url_for('items_edit', item_id=item_id))
        
        try:
            db.session.commit()
            flash('Artikel aktualisiert.', 'success')
            return redirect(url_for('items_list'))
        except IntegrityError:
            db.session.rollback()
            flash('SKU oder Barcode ist schon vergeben.', 'error')
            return redirect(url_for('items_edit', item_id=item_id))
    
    return render_template('items_edit.html', item=item, kategorien=KATEGORIEN)


@app.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def items_delete(item_id):
    item = Item.query.get_or_404(item_id)
    
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Artikel gelöscht.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Fehler beim Löschen.', 'error')
    
    return redirect(url_for('items_list'))


# ---- MOVEMENTS ROUTES ----
@app.route('/movements/new', methods=['GET', 'POST'])
@login_required
def movement_new():
    cart = session.get('cart', [])
    ausgabe_typ = session.get('ausgabe_typ', '')
    
    if request.method == 'POST':
        recipient_firstname = request.form.get('recipient_firstname', '').strip()
        recipient_lastname = request.form.get('recipient_lastname', '').strip()
        recipient_department = request.form.get('recipient_department', '').strip()
        recipient_email = request.form.get('recipient_email', '').strip()
        signature = request.form.get('signature', '')
        
        for cart_item in cart:
            item = Item.query.get(cart_item['item_id'])
            if item:
                change = -cart_item['quantity'] if ausgabe_typ != 'rueckgabe' else cart_item['quantity']
                
                m = Movement(
                    item_id=item.id,
                    change=change,
                    reason=ausgabe_typ,
                    ausgabe_typ=ausgabe_typ,
                    recipient_firstname=recipient_firstname,
                    recipient_lastname=recipient_lastname,
                    recipient_department=recipient_department,
                    recipient_email=recipient_email,
                    issuer_firstname=g.user.firstname if g.user else '',
                    issuer_lastname=g.user.lastname if g.user else '',
                    signature=signature
                )
                item.qty = item.qty + change
                db.session.add(m)
        
        db.session.commit()
        
        session['cart'] = []
        session['ausgabe_typ'] = ''
        session.modified = True
        
        flash('Bewegung gespeichert.', 'success')
        return redirect(url_for('items_list'))
    
    cart_items = []
    for cart_item in cart:
        item = Item.query.get(cart_item['item_id'])
        if item:
            cart_items.append({
                'item': item,
                'quantity': cart_item['quantity']
            })
    
    return render_template('movements_new.html', cart_items=cart_items, ausgabe_typ=ausgabe_typ)


@app.route('/movements')
@login_required
def movements_list():
    moves = Movement.query.order_by(Movement.created_at.desc()).limit(100).all()
    return render_template('movements_list.html', moves=moves)


# ---- DASHBOARD ROUTE ----
@app.route('/dashboard')
@login_required
def dashboard():
    total_items = db.session.query(func.count(Item.id)).scalar()
    low_stock_count = db.session.query(func.count(Item.id))\
                        .filter(Item.qty < Item.min_qty).scalar()

    recently_added = Item.query.order_by(Item.created_at.desc()).limit(5).all()
    low_stock = Item.query.filter(Item.qty < Item.min_qty)\
                 .order_by((Item.min_qty - Item.qty).desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_items=total_items,
        low_stock_count=low_stock_count,
        recently_added=recently_added,
        low_stock=low_stock
    )


# ---- SCANNER & WARENKORB ----
@app.route('/scanner', methods=['GET', 'POST'])
@login_required
def scanner():
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    if request.method == 'GET':
        cart_items = []
        for cart_item in cart:
            item = Item.query.get(cart_item['item_id'])
            if item:
                cart_items.append({
                    'item': item,
                    'quantity': cart_item['quantity']
                })
        
        return render_template('scanner.html', cart_items=cart_items, cart_count=len(cart))
    
    if request.is_json:
        data = request.get_json() or {}
    else:
        data = request.form or {}

    barcode = (data.get('barcode') or '').strip()
    quantity = int(data.get('quantity') or 1)

    if not barcode:
        msg = 'Barcode ist leer'
        if request.is_json:
            return {'success': False, 'message': msg}, 400
        flash(msg, 'error')
        return redirect(url_for('scanner'))

    item = Item.query.filter(
        (Item.barcode == barcode) | (Item.sku == barcode)
    ).first()

    if not item:
        msg = f'Artikel mit Barcode/SKU "{barcode}" nicht gefunden'
        if request.is_json:
            return {'success': False, 'message': msg}, 404
        flash(msg, 'error')
        return redirect(url_for('scanner'))

    if item.qty < quantity:
        msg = f'Nicht genug Bestand! Verfügbar: {item.qty}'
        if request.is_json:
            return {'success': False, 'message': msg}, 400
        flash(msg, 'error')
        return redirect(url_for('scanner'))

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

    msg = f'{quantity}x {item.name} zum Warenkorb hinzugefügt'
    if request.is_json:
        return {'success': True, 'message': msg, 'cart_count': len(cart)}, 200
    
    flash(msg, 'success')
    return redirect(url_for('scanner'))


@app.route('/cart/clear')
@login_required
def cart_clear():
    session['cart'] = []
    session.modified = True
    flash('Warenkorb geleert', 'success')
    return redirect(url_for('scanner'))


@app.route('/cart/remove/<int:item_id>')
@login_required
def cart_remove(item_id):
    if 'cart' in session:
        session['cart'] = [c for c in session['cart'] if c['item_id'] != item_id]
        session.modified = True
    flash('Artikel entfernt', 'success')
    return redirect(url_for('scanner'))


@app.route('/checkout/<action>')
@login_required
def checkout(action):
    if 'cart' not in session or len(session['cart']) == 0:
        flash('Warenkorb ist leer', 'error')
        return redirect(url_for('scanner'))
    
    if action == 'rueckgabe':
        for cart_item in session['cart']:
            item = Item.query.get(cart_item['item_id'])
            if item:
                m = Movement(
                    item_id=item.id,
                    change=cart_item['quantity'],
                    reason='Rückgabe',
                    ausgabe_typ='rueckgabe',
                    issuer_firstname=g.user.firstname if g.user else '',
                    issuer_lastname=g.user.lastname if g.user else ''
                )
                item.qty = item.qty + cart_item['quantity']
                db.session.add(m)
        
        db.session.commit()
        session['cart'] = []
        session.modified = True
        flash('Rückgabe erfolgreich! Bestand wurde erhöht.', 'success')
        return redirect(url_for('items_list'))
    
    elif action == 'ausgabe':
        return render_template('checkout.html')
    
    else:
        flash('Ungültige Aktion', 'error')
        return redirect(url_for('scanner'))


@app.route('/checkout/ausgabe-typ', methods=['POST'])
@login_required
def checkout_ausgabe_typ():
    ausgabe_typ = request.form.get('ausgabe_typ')
    
    if not ausgabe_typ:
        flash('Bitte Ausgabe-Typ wählen', 'error')
        return redirect(url_for('checkout', action='ausgabe'))
    
    session['ausgabe_typ'] = ausgabe_typ
    session.modified = True
    return redirect(url_for('movement_new'))


# -------- START --------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)