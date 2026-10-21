"""Vaste waarden voor formulieren en validatie."""

# Standaardglazen op basis van RIVM-omrekening (10 g alcohol per glas).
# units = volume_ml × (abv% / 100) × 0,789 / 10
DRINK_OPTIONS = [
    {
        "id": "bier",
        "label": "Standaard bier",
        "icon": "🍺",
        "units": 1.0,
        "hint": "250 ml · 5%",
        "color": "#e8a838",
    },
    {
        "id": "radler",
        "label": "Radler",
        "icon": "🍋",
        "units": 0.5,
        "hint": "250 ml · 2,5%",
        "color": "#f5d76e",
    },
    {
        "id": "blond",
        "label": "Blond",
        "icon": "🌾",
        "units": 1.2,
        "hint": "250 ml · 6%",
        "color": "#f0c040",
    },
    {
        "id": "dubbel",
        "label": "Dubbel",
        "icon": "🟤",
        "units": 1.4,
        "hint": "250 ml · 7%",
        "color": "#8b5a2b",
    },
    {
        "id": "tripel",
        "label": "Tripel",
        "icon": "🍻",
        "units": 1.6,
        "hint": "250 ml · 8%",
        "color": "#d4a017",
    },
    {
        "id": "quadrupel",
        "label": "Quadrupel",
        "icon": "🖤",
        "units": 2.0,
        "hint": "250 ml · 10%",
        "color": "#4a3728",
    },
    {
        "id": "wijn",
        "label": "Wijnglas",
        "icon": "🍷",
        "units": 1.0,
        "hint": "100 ml · 12%",
        "color": "#9b2335",
    },
    {
        "id": "port",
        "label": "Portglas",
        "icon": "🍷",
        "units": 0.8,
        "hint": "50 ml · 20%",
        "color": "#6b1d3a",
    },
    {
        "id": "champagne",
        "label": "Champagne / prosecco",
        "icon": "🥂",
        "units": 1.2,
        "hint": "125 ml · 12%",
        "color": "#d4af37",
    },
    {
        "id": "sterk",
        "label": "Sterke drank",
        "icon": "🥃",
        "units": 1.0,
        "hint": "35 ml · 35% · whisky, rum, gin",
        "color": "#5c4033",
    },
    {
        "id": "cider",
        "label": "Cider",
        "icon": "🍎",
        "units": 0.9,
        "hint": "250 ml · 4,5%",
        "color": "#c45c26",
    },
    {
        "id": "cocktail",
        "label": "Cocktail / mix",
        "icon": "🍸",
        "units": 1.1,
        "hint": "250 ml · 5,5%",
        "color": "#e87a90",
    },
]

DRINK_OPTIONS_BY_ID = {d["id"]: d for d in DRINK_OPTIONS}

GENDERS = [
    ("", "— Kies —"),
    ("man", "Man"),
    ("vrouw", "Vrouw"),
    ("anders", "Anders / zeg ik liever niet"),
]

EDUCATION_LEVELS = [
    ("", "— Kies —"),
    ("basisonderwijs", "Basisonderwijs"),
    ("vmbo", "VMBO"),
    ("havo_vwo", "HAVO/VWO"),
    ("mbo", "MBO"),
    ("hbo", "HBO"),
    ("wo", "WO"),
    ("anders", "Anders"),
]

GOAL_TYPES = {
    "weekly_units": "Maximaal X glazen per week",
    "dry_days": "Minimaal X alcoholvrije dagen per week",
    "abstain": "Volledig stoppen met alcohol",
}

MIN_PASSWORD_LENGTH = 8
MIN_USERNAME_LENGTH = 3
MAX_UNITS_PER_DAY = 50
GAP_MIN_DAYS = 2
