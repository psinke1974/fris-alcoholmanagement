"""Inhoud per fase bij stoppen met alcohol — tips, positieve en negatieve bijwerkingen."""

PHASE_ORDER = [
    "voorbereiding",
    "dag_1_3",
    "week_1",
    "week_2_4",
    "maand_1_3",
    "langdurig",
]

PHASE_CONTENT = {
    "voorbereiding": {
        "label": "Voorbereiding",
        "description": "Je overweegt te stoppen of bent net begonnen. Goede voorbereiding vergroot je kans op succes.",
        "day_range": None,
        "tips": [
            {
                "title": "Kies een startdatum",
                "text": "Plan je stopdag concreet. Vertel het aan iemand die je steunt — sociale steun maakt een groot verschil.",
                "category": "strategie",
            },
            {
                "title": "Verwijder verleiding",
                "text": "Haal alcohol uit huis vóór je startdag. Vul de koelkast met alcoholvrije alternatieven die je lekker vindt.",
                "category": "strategie",
            },
            {
                "title": "Ken je triggers",
                "text": "Noteer wanneer je normaal drinkt: na werk, bij stress, sociale gelegenheden. Bedenk per trigger een alternatief.",
                "category": "strategie",
            },
        ],
        "positive_effects": [
            "Meer controle over je keuzes",
            "Duidelijk doel om naartoe te werken",
            "Mogelijkheid om patronen te herkennen vóór je stopt",
        ],
        "negative_effects": [
            "Onzekerheid over wat je te wachten staat",
            "Angst om sociale situaties te missen",
            "Twijfel of je het volhoudt",
        ],
    },
    "dag_1_3": {
        "label": "Eerste 72 uur",
        "description": "De acute fase. Je lichaam past zich aan aan het ontbreken van alcohol.",
        "day_range": (1, 3),
        "tips": [
            {
                "title": "Drink veel water",
                "text": "Alcohol ontwaterd. Drink minstens 2 liter water per dag en eet regelmatig — dat vermindert ongemak.",
                "category": "strategie",
            },
            {
                "title": "Rust en slaap",
                "text": "Slaap kan in het begin verstoord zijn. Ga op vaste tijden naar bed en vermijd schermen voor het slapen.",
                "category": "strategie",
            },
            {
                "title": "Bij ernstige klachten",
                "text": "Trillen, hartkloppingen of verwardheid? Neem direct contact op met je huisarts. Stoppen kan medische begeleiding vereisen.",
                "category": "waarschuwing",
            },
        ],
        "positive_effects": [
            "Je lichaam begint direct met ontgifting",
            "Lever start herstel binnen 24–48 uur",
            "Eerste trots op je beslissing",
        ],
        "negative_effects": [
            "Onrust, zenuwachtigheid of prikkelbaarheid",
            "Slechte slaap of levendige dromen",
            "Hoofdpijn, transpireren of misselijkheid",
            "Sterk verlangen naar alcohol",
        ],
    },
    "week_1": {
        "label": "Eerste week",
        "description": "De eerste volle week zonder alcohol. Lichamelijke klachten nemen meestal af.",
        "day_range": (4, 7),
        "tips": [
            {
                "title": "Vier kleine successen",
                "text": "Elke alcoholvrije dag is een overwinning. Beloon jezelf met iets niet-alcoholisch: een goede film, een wandeling, een lekker etentje.",
                "category": "motivatie",
            },
            {
                "title": "Vermijd triggers",
                "text": "In week 1 is je wilskracht nog kwetsbaar. Vermijd de kroeg of feestjes als dat te zwaar is — dat is geen falen.",
                "category": "strategie",
            },
            {
                "title": "Schrijf je gevoelens op",
                "text": "Gebruik je dagboek om stemming en verlangen bij te houden. Patronen worden zichtbaar na een paar dagen.",
                "category": "strategie",
            },
        ],
        "positive_effects": [
            "Betere hydratatie en minder opgezwollen gevoel",
            "Huid kan al helderder worden",
            "Meer energie overdag (ondanks slaapproblemen)",
            "Duidelijkere ochtenden zonder kater",
        ],
        "negative_effects": [
            "Verlangen kan pieken rond vaste drinkmomenten",
            "Stemmingsschommelingen (euforie én somberheid)",
            "Vermoeidheid door verstoorde slaap",
            "Moeite met concentratie",
        ],
    },
    "week_2_4": {
        "label": "Week 2–4",
        "description": "Gewoontes veranderen. Lichamelijk herstel wordt merkbaarder.",
        "day_range": (8, 30),
        "tips": [
            {
                "title": "Nieuwe routines",
                "text": "Vervang je drinkritueel: thee na het werk, een avondwandeling, of een hobby op het moment dat je normaal een glas pakte.",
                "category": "strategie",
            },
            {
                "title": "Sociale situaties",
                "text": "Oefen met 'nee' zeggen. Een kort 'ik drink even niet' is genoeg — je hoeft je niet te verantwoorden.",
                "category": "strategie",
            },
            {
                "title": "Let op valse troost",
                "text": "Sommige mensen eten meer suiker of snacken meer in deze fase. Dat is normaal — wees mild voor jezelf.",
                "category": "info",
            },
        ],
        "positive_effects": [
            "Slaap verbetert merkbaar",
            "Beter concentratievermogen",
            "Lagere bloeddruk en rustiger hartslag",
            "Gewichtsverlies bij sommige mensen",
            "Meer zelfvertrouwen",
        ],
        "negative_effects": [
            "Af en toe sterke cravings, vooral bij stress",
            "Verveling — alcohol vulde vaak leegtes",
            "Emotionele ups en downs (verdriet, boosheid)",
            "Soms dromen over drinken",
        ],
    },
    "maand_1_3": {
        "label": "Maand 1–3",
        "description": "Je bouwt een nieuw leven zonder alcohol. Lichamelijk herstel gaat door.",
        "day_range": (31, 90),
        "tips": [
            {
                "title": "Herken de gevarenzone",
                "text": "Na de eerste euforie kan een dip komen. Veel terugval gebeurt rond maand 2–3. Blijf alert en zoek steun.",
                "category": "waarschuwing",
            },
            {
                "title": "Investeer in relaties",
                "text": "Versterk connecties die niet draaien om drinken. Nieuwe vriendschappen of hobby's geven voldoening.",
                "category": "motivatie",
            },
            {
                "title": "Vier je mijlpalen",
                "text": "30, 60, 90 dagen zijn belangrijke momenten. Kijk terug in je dagboek — je bent ver gekomen.",
                "category": "motivatie",
            },
        ],
        "positive_effects": [
            "Lever herstelt grotendeels (vetafbraak verbetert)",
            "Huid ziet er gezonder uit",
            "Immuunsysteem wordt sterker",
            "Stabielere stemming",
            "Betere sportprestaties en uithoudingsvermogen",
            "Besparing op geld wordt zichtbaar",
        ],
        "negative_effects": [
            "Emotionele problemen kunnen naar boven komen",
            "Soms een gevoel van leegte of 'wie ben ik zonder alcohol?'",
            "Incidentele cravings bij feesten of stress",
            "Sociale druk van mensen die niet stoppen",
        ],
    },
    "langdurig": {
        "label": "Langdurig herstel",
        "description": "Meer dan 3 maanden alcoholvrij. Je hebt een solide basis — blijf bewust.",
        "day_range": (91, None),
        "tips": [
            {
                "title": "Complacentie is een valkuil",
                "text": "'Eén glas kan geen kwaad' is een gevaarlijke gedachte. Herinner jezelf waarom je gestopt bent.",
                "category": "waarschuwing",
            },
            {
                "title": "Blijf je dagboek bijhouden",
                "text": "Schrijven helpt om terugval te voorkomen. Noteer wat goed gaat én wat lastig is.",
                "category": "strategie",
            },
            {
                "title": "Help anderen",
                "text": "Overweeg steungroepen of online communities. Je ervaring kan anderen inspireren.",
                "category": "motivatie",
            },
        ],
        "positive_effects": [
            "Aanzienlijk lager risico op lever-, hart- en kankerziekten",
            "Diepe, herstellende slaap",
            "Helder denken en beter geheugen",
            "Sterk gevoel van eigenwaarde",
            "Financiële en relationele winst",
            "Voorbeeld voor anderen",
        ],
        "negative_effects": [
            "Incidentele nostalgie naar drinken",
            "Soms moeilijk in omgevingen waar alcohol centraal staat",
            "Risico op terugval bij grote levensgebeurtenissen",
        ],
    },
}

REDUCTION_PHASE_CONTENT = {
    "label": "Minder drinken",
    "description": "Je werkt aan minder alcohol per week. Geleidelijk verminderen is een bewezen strategie.",
    "tips": [
        {
            "title": "Plan je glazen",
            "text": "Kies vooraf hoeveel glazen je deze week drinkt en wanneer. Spontaan drinken leidt vaker tot overschrijding.",
            "category": "strategie",
        },
        {
            "title": "Wissel af met water",
            "text": "Drink een glas water tussen elk alcoholisch glas. Je drinkt langzamer en minder.",
            "category": "strategie",
        },
        {
            "title": "Alcoholvrije dagen plannen",
            "text": "Plan minstens 2–3 alcoholvrije dagen vast in je agenda. Maak er geen uitzonderingen van.",
            "category": "strategie",
        },
    ],
    "positive_effects": [
        "Betere slaap op alcoholvrije dagen",
        "Meer energie en helderheid",
        "Lagere weekkosten",
        "Meer controle over je gedrag",
    ],
    "negative_effects": [
        "Verlangen op dagen dat je normaal drinkt",
        "Sociale druk om 'mee te doen'",
        "Frustratie als je je doel net mist",
    ],
}
