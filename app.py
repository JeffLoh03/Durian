import os
from flask import Flask, render_template, request, redirect, url_for, flash
from database import db
from models import Species, Variation, Inventory, Sale

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///durian.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
def dashboard():
    sales = Sale.query.all()
    total_profit = sum(s.profit for s in sales)
    mapping_totals = {}
    for s in sales:
        key = (s.species.name, s.purchase_variation.name, s.sold_variation.name)
        data = mapping_totals.setdefault(key, {'weight': 0, 'revenue': 0, 'profit': 0})
        data['weight'] += s.weight_kg
        data['revenue'] += s.revenue
        data['profit'] += s.profit
    return render_template('dashboard.html', total_profit=total_profit, mapping_totals=mapping_totals)


@app.route('/species', methods=['GET', 'POST'])
def add_species():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            db.session.add(Species(name=name))
            db.session.commit()
            flash('Species added')
        return redirect(url_for('add_species'))
    species = Species.query.all()
    return render_template('species.html', species=species)


@app.route('/variation', methods=['GET', 'POST'])
def add_variation():
    species = Species.query.all()
    if request.method == 'POST':
        species_id = request.form.get('species_id')
        name = request.form.get('name')
        if species_id and name:
            variation = Variation(species_id=species_id, name=name)
            db.session.add(variation)
            db.session.commit()
            flash('Variation added')
        return redirect(url_for('add_variation'))
    variations = Variation.query.all()
    return render_template('variation.html', species=species, variations=variations)


@app.route('/inventory', methods=['GET', 'POST'])
def add_inventory():
    variations = Variation.query.all()
    if request.method == 'POST':
        variation_id = request.form.get('variation_id')
        weight = request.form.get('weight')
        cost = request.form.get('cost')
        if variation_id and weight and cost:
            inv = Inventory(variation_id=variation_id, weight_kg=float(weight), cost_per_kg=float(cost))
            db.session.add(inv)
            db.session.commit()
            flash('Inventory recorded')
        return redirect(url_for('add_inventory'))
    inventory = Inventory.query.all()
    return render_template('inventory.html', variations=variations, inventory=inventory)


@app.route('/sale', methods=['GET', 'POST'])
def add_sale():
    variations = Variation.query.all()
    if request.method == 'POST':
        purchase_variation_id = request.form.get('purchase_variation_id')
        sold_variation_id = request.form.get('sold_variation_id')
        weight = request.form.get('weight')
        price = request.form.get('price')
        if purchase_variation_id and sold_variation_id and weight and price:
            cost_per_kg = consume_inventory_cost(int(purchase_variation_id), float(weight))
            if cost_per_kg is None:
                flash('Insufficient inventory')
            else:
                purchase_variation = Variation.query.get(purchase_variation_id)
                sale = Sale(
                    species_id=purchase_variation.species_id,
                    purchase_variation_id=purchase_variation_id,
                    sold_variation_id=sold_variation_id,
                    weight_kg=float(weight),
                    sale_price_per_kg=float(price),
                    cost_per_kg=cost_per_kg,
                )
                db.session.add(sale)
                db.session.commit()
                generate_receipt(sale)
                sync_sale_to_google_sheets(sale)
                flash('Sale recorded')
        return redirect(url_for('add_sale'))
    sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    return render_template('sale.html', variations=variations, sales=sales)


def consume_inventory_cost(variation_id: int, weight_needed: float):
    inventory_items = (
        Inventory.query.filter_by(variation_id=variation_id)
        .order_by(Inventory.id)
        .all()
    )
    total_available = sum(item.weight_kg for item in inventory_items)
    if total_available < weight_needed:
        return None
    remaining = weight_needed
    total_cost = 0.0
    for item in inventory_items:
        if remaining <= 0:
            break
        used = min(item.weight_kg, remaining)
        total_cost += used * item.cost_per_kg
        item.weight_kg -= used
        remaining -= used
        if item.weight_kg == 0:
            db.session.delete(item)
    return total_cost / weight_needed


def generate_receipt(sale: Sale):
    os.makedirs('receipts', exist_ok=True)
    path = os.path.join('receipts', f'sale_{sale.id}.txt')
    with open(path, 'w') as f:
        f.write(f'Species: {sale.species.name}\n')
        f.write(f'Purchased as: {sale.purchase_variation.name}\n')
        f.write(f'Sold as: {sale.sold_variation.name}\n')
        f.write(f'Weight (kg): {sale.weight_kg}\n')
        f.write(f'Cost per kg: {sale.cost_per_kg}\n')
        f.write(f'Sale price per kg: {sale.sale_price_per_kg}\n')
        f.write(f'Total cost: {sale.cost}\n')
        f.write(f'Total revenue: {sale.revenue}\n')
        f.write(f'Profit: {sale.profit}\n')


def sync_sale_to_google_sheets(sale: Sale):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scopes)
        client = gspread.authorize(creds)
        sheet = client.open('DurianSales').sheet1
        sheet.append_row([
            sale.timestamp.isoformat(),
            sale.species.name,
            sale.purchase_variation.name,
            sale.sold_variation.name,
            sale.weight_kg,
            sale.cost_per_kg,
            sale.sale_price_per_kg,
            sale.revenue,
            sale.profit,
        ])
    except Exception as e:
        app.logger.warning(f'Google Sheets sync failed: {e}')


if __name__ == '__main__':
    app.run(debug=True)
