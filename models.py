from datetime import datetime
from database import db


class Species(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f"<Species {self.name}>"


class Variation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)

    species = db.relationship('Species', backref=db.backref('variations', lazy=True))

    def __repr__(self):
        return f"<Variation {self.name} ({self.species.name})>"


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variation_id = db.Column(db.Integer, db.ForeignKey('variation.id'), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    cost_per_kg = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    variation = db.relationship('Variation')

    def __repr__(self):
        return f"<Inventory {self.variation.name} {self.weight_kg}kg>"


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False)
    purchase_variation_id = db.Column(db.Integer, db.ForeignKey('variation.id'), nullable=False)
    sold_variation_id = db.Column(db.Integer, db.ForeignKey('variation.id'), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    sale_price_per_kg = db.Column(db.Float, nullable=False)
    cost_per_kg = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    species = db.relationship('Species')
    purchase_variation = db.relationship('Variation', foreign_keys=[purchase_variation_id])
    sold_variation = db.relationship('Variation', foreign_keys=[sold_variation_id])

    @property
    def revenue(self):
        return self.sale_price_per_kg * self.weight_kg

    @property
    def cost(self):
        return self.cost_per_kg * self.weight_kg

    @property
    def profit(self):
        return self.revenue - self.cost

    def __repr__(self):
        return (f"<Sale {self.purchase_variation.name} as {self.sold_variation.name} "
                f"{self.weight_kg}kg>")
