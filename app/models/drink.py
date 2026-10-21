from datetime import datetime

from app.extensions import db


class DrinkLog(db.Model):
    __tablename__ = "drink_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    log_date = db.Column(db.Date, nullable=False, index=True)
    units = db.Column(db.Float, nullable=False)
    drink_type = db.Column(db.String(255))
    drink_items = db.Column(db.Text)
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="drink_logs")
