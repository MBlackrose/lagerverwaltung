
import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, g

# Extensions & Models
from extensions import db
from models import Item, User, Movement

# Services
from services import CartService, ItemService, PDFService


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


# -------- App erstellen --------
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'change-me-in-.env'
    
    basedir = os.path.abspath(os.path.dirname(__file__))
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


# ======== ROUTES ========

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


@app.route('/api/subcategories/<category>')
def get_subcategories(category):
    from flask import jsonify
    subcategories = KATEGORIEN.get(category, [])
    return jsonify(subcategories)


# -------- AUTH ROUTES --------
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
        except Exception:
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


# -------- ITEMS ROUTES (mit ItemService) --------
@app.route('/items')
@login_required
def items_list():
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    items = ItemService.get_all(category_filter=category_filter, search_query=search_query)
    
    return render_template('items_list.html', items=items, search_query=search_query,
                          kategorien=KATEGORIEN, selected_category=category_filter)


@app.route('/items/new', methods=['GET', 'POST'])
@login_required
def items_new():
    if request.method == 'POST':
        success, message = ItemService.create(
            name=request.form.get('name', '').strip(),
            sku=request.form.get('sku', '').strip(),
            barcode=(request.form.get('barcode') or '').strip() or None,
            qty=int(request.form.get('qty', 0) or 0),
            min_qty=int(request.form.get('min_qty', 0) or 0),
            category=request.form.get('category', 'Sonstige'),
            subcategory=request.form.get('subcategory', ''),
            inventory_number=request.form.get('inventory_number', '').strip(),
            serial_number=request.form.get('serial_number', '').strip()
        )
        
        flash(message, 'success' if success else 'error')
        if success:
            return redirect(url_for('items_list'))
        return redirect(url_for('items_new'))

    return render_template('items_new.html', kategorien=KATEGORIEN)


@app.route('/items/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def items_edit(item_id):
    item = ItemService.get_by_id(item_id)
    if not item:
        flash('Artikel nicht gefunden.', 'error')
        return redirect(url_for('items_list'))
    
    if request.method == 'POST':
        success, message = ItemService.update(
            item_id=item_id,
            name=request.form.get('name', '').strip(),
            sku=request.form.get('sku', '').strip(),
            barcode=(request.form.get('barcode') or '').strip() or None,
            qty=int(request.form.get('qty', 0) or 0),
            min_qty=int(request.form.get('min_qty', 0) or 0),
            category=request.form.get('category', 'Sonstige'),
            subcategory=request.form.get('subcategory', ''),
            inventory_number=request.form.get('inventory_number', '').strip(),
            serial_number=request.form.get('serial_number', '').strip()
        )
        
        flash(message, 'success' if success else 'error')
        if success:
            return redirect(url_for('items_list'))
        return redirect(url_for('items_edit', item_id=item_id))
    
    return render_template('items_edit.html', item=item, kategorien=KATEGORIEN)


@app.route('/items/<int:item_id>/delete', methods=['POST'])
@login_required
def items_delete(item_id):
    success, message = ItemService.delete(item_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('items_list'))


# -------- DASHBOARD --------
@app.route('/dashboard')
@login_required
def dashboard():
    total_items = ItemService.count_all()
    low_stock_count = ItemService.count_low_stock()
    recently_added = Item.query.order_by(Item.created_at.desc()).limit(5).all()
    low_stock = ItemService.get_low_stock()[:5]

    return render_template(
        'dashboard.html',
        total_items=total_items,
        low_stock_count=low_stock_count,
        recently_added=recently_added,
        low_stock=low_stock
    )


# -------- SCANNER & WARENKORB (mit CartService) --------
@app.route('/scanner', methods=['GET', 'POST'])
@login_required
def scanner():
    cart_service = CartService()
    
    if request.method == 'POST':
        barcode = (request.form.get('barcode') or '').strip()
        quantity = int(request.form.get('quantity') or 1)
        
        success, message = cart_service.add_item(barcode, quantity)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('scanner'))
    
    return render_template('scanner.html', 
                          cart_items=cart_service.get_items(), 
                          cart_count=cart_service.get_count())


@app.route('/cart/clear')
@login_required
def cart_clear():
    cart_service = CartService()
    cart_service.clear()
    flash('Warenkorb geleert', 'success')
    return redirect(url_for('scanner'))


@app.route('/cart/remove/<int:item_id>')
@login_required
def cart_remove(item_id):
    cart_service = CartService()
    cart_service.remove_item(item_id)
    flash('Artikel entfernt', 'success')
    return redirect(url_for('scanner'))


@app.route('/checkout/<action>')
@login_required
def checkout(action):
    cart_service = CartService()
    
    if cart_service.is_empty():
        flash('Warenkorb ist leer', 'error')
        return redirect(url_for('scanner'))
    
    if action == 'rueckgabe':
        for cart_item in cart_service.get_raw():
            item = ItemService.get_by_id(cart_item['item_id'])
            if item:
                m = Movement(
                    item_id=item.id,
                    change=cart_item['quantity'],
                    reason='Rückgabe',
                    ausgabe_typ='rueckgabe',
                    issuer_firstname=g.user.firstname if g.user else '',
                    issuer_lastname=g.user.lastname if g.user else ''
                )
                item.qty += cart_item['quantity']
                db.session.add(m)
        
        db.session.commit()
        cart_service.clear()
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


# -------- MOVEMENTS ROUTES --------
@app.route('/movements/new', methods=['GET', 'POST'])
@login_required
def movement_new():
    cart_service = CartService()
    cart = cart_service.get_raw()
    ausgabe_typ = session.get('ausgabe_typ', '')
    
    if request.method == 'POST':
        recipient_firstname = request.form.get('recipient_firstname', '').strip()
        recipient_lastname = request.form.get('recipient_lastname', '').strip()
        recipient_department = request.form.get('recipient_department', '').strip()
        recipient_email = request.form.get('recipient_email', '').strip()
        inventory_number = request.form.get('inventory_number', '').strip()
        serial_number = request.form.get('serial_number', '').strip()
        has_keyboard = request.form.get('has_keyboard') == 'true'
        has_damage = request.form.get('has_damage') == 'true'
        damage_description = request.form.get('damage_description', '').strip()
        signature = request.form.get('signature', '')
        
        for cart_item in cart:
            item = ItemService.get_by_id(cart_item['item_id'])
            if item:
                change = -cart_item['quantity']
                
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
                    inventory_number=inventory_number,
                    serial_number=serial_number,
                    has_keyboard=has_keyboard,
                    has_damage=has_damage,
                    damage_description=damage_description,
                    signature=signature
                )
                item.qty += change
                db.session.add(m)
        
        db.session.commit()
        
        # PDF generieren für die letzte Bewegung
        if cart and len(cart) > 0:
            last_item = ItemService.get_by_id(cart[0]['item_id'])
            last_movement = Movement.query.order_by(Movement.id.desc()).first()
            if last_movement and last_item:
                pdf_path = PDFService.create_receipt(last_movement, last_item)
                last_movement.pdf_file = pdf_path
                db.session.commit()
        
        cart_service.clear()
        session['ausgabe_typ'] = ''
        session.modified = True
        
        flash('Bewegung gespeichert & PDF erstellt!', 'success')
        return redirect(url_for('movements_list'))
    
    return render_template('movements_new.html', 
                          cart_items=cart_service.get_items(), 
                          ausgabe_typ=ausgabe_typ)


@app.route('/movements')
@login_required
def movements_list():
    moves = Movement.query.order_by(Movement.created_at.desc()).limit(100).all()
    return render_template('movements_list.html', moves=moves)


# -------- START --------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)