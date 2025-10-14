from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import os

db = SQLAlchemy()

# Projektbasis ermitteln (absoluter Pfad)
basedir = os.path.abspath(os.path.dirname(__file__))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'change-me-in-.env'

    # SQLite: absoluter Pfad + Ordner anlegen
    db_dir = os.path.join(basedir, "database")
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "lager.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # ---------------- Model ----------------
    class Item(db.Model):
        __tablename__ = 'items'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(120), nullable=False)
        sku = db.Column(db.String(64), unique=True, nullable=False)
        barcode = db.Column(db.String(64), unique=True, nullable=True)
        qty = db.Column(db.Integer, nullable=False, default=0)
        min_qty = db.Column(db.Integer, nullable=False, default=0)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---------------- Routen ----------------
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/initdb')
    def initdb():
        os.makedirs('database', exist_ok=True)
        db.create_all()
        return "DB initialisiert."

    @app.route('/items')
    def items_list():
        items = Item.query.order_by(Item.name.asc()).all()
        return render_template('items_list.html', items=items)

    @app.route('/items/new', methods=['GET', 'POST'])
    def items_new():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            sku = request.form.get('sku', '').strip()
            barcode = request.form.get('barcode', '').strip() or None
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

    return app


if __name__ == '__main__':
    app = create_app()
    # Tabellen sicherstellen
    with app.app_context():
        db.create_all()
    app.run(debug=True)
