from app.blueprints.main.routes import main_bp
from app.blueprints.main import account  # noqa: F401  (registreert routes op main_bp)

__all__ = ["main_bp"]
