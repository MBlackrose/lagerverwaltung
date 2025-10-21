from functools import wraps
from datetime import datetime
import os

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, g
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash

# -------- Basis / DB --------
db = SQLAlchemy()
basedir = os.path.abspath(os.path.dirname(__file__))


# -------- Modelle (außerhalb von create_app) --------
class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sku = db.Column(db.String(64), unique=True, nullable=True)
    barcode = db.Column(db.String(64), unique=True, nullable=True)
    qty = db.Column(db.Integer, nullable=False, default=0)
    min_qty = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Movement(db.Model):
    __tablename__ = 'movements'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    item = db.relationship('Item', backref=db.backref('movements', lazy=True))

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

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

# Startseite
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
        password = request.form.get('password') or ''
        password_confirm = request.form.get('password_confirm') or ''

        # Validierungen
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
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('✅ Benutzer erfolgreich erstellt! Bitte melden Sie sich an.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('❌ Fehler beim Erstellen des Benutzers.', 'error')
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
    u = User(username='admin')
    u.set_password('admin123')
    db.session.add(u)
    db.session.commit()
    return 'Admin angelegt: admin / admin123'


# ---- ITEMS ROUTES ----
@app.route('/items')
@login_required
def items_list():
    q = request.args.get('q', '').strip()
    if q:
        items = Item.query.filter(
            (Item.name.ilike(f'%{q}%')) |
            (Item.sku.ilike(f'%{q}%')) |
            (Item.barcode == q)
        ).order_by(Item.name.asc()).all()
    else:
        items = Item.query.order_by(Item.name.asc()).all()
    
    return render_template('items_list.html', items=items, search_query=q)


@app.route('/items/new', methods=['GET', 'POST'])
@login_required
def items_new():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        sku = request.form.get('sku', '').strip()
        barcode = (request.form.get('barcode') or '').strip() or None
        qty = int(request.form.get('qty', 0) or 0)
        min_qty = int(request.form.get('min_qty', 0) or 0)

        if not name or not sku:
            flash('Name und Artikelnummer (SKU) sind Pflicht.', 'error')
            return redirect(url_for('items_new'))

        try:
            item = Item(name=name, sku=sku, barcode=barcode, qty=qty, min_qty=min_qty)
            db.session.add(item)
            db.session.commit()
            flash('Artikel angelegt.', 'success')
            return redirect(url_for('items_list'))
        except IntegrityError:
            db.session.rollback()
            flash('SKU oder Barcode ist schon vergeben.', 'error')
            return redirect(url_for('items_new'))

    return render_template('items_new.html')


# ---- MOVEMENTS ROUTES ----
@app.route('/movements/new', methods=['GET', 'POST'])
@login_required
def movement_new():
    items = Item.query.order_by(Item.name).all()

    if request.method == 'POST':
        item_id = int(request.form['item_id'])
        change = int(request.form['change'])
        reason = request.form.get('reason', '')

        item = Item.query.get_or_404(item_id)
        if item.qty + change < 0:
            flash('Menge kann nicht negativ werden.', 'error')
            return redirect(url_for('movement_new'))

        m = Movement(item_id=item.id, change=change, reason=reason)
        item.qty = item.qty + change
        db.session.add(m)
        db.session.commit()
        flash('Bewegung gespeichert.', 'success')
        return redirect(url_for('items_list'))

    selected_id = request.args.get('item_id', type=int)
    return render_template('movements_new.html', items=items, selected_id=selected_id)


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


# -------- START --------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)