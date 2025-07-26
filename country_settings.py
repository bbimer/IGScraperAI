# Country-specific settings
COUNTRY_SETTINGS = {
    "UK": {
        "name_patterns": ["uk", "brit", "eng", "london", "gb", "england", "british"],
        "bio_keywords": ["uk", "british", "england", "london", "manchester", "ukrainian"],
        "age_regex": r'(\d{2})\s?(?:yo|yrs|years|year|age)',
        "location_priority": ["london", "manchester", "birmingham", "uk", "england"],
        "filter_prompt": "Is this a male from UK? Check name, username, bio. Filter out women, non-traditional orientations."
    },
    "DE": {
        "name_patterns": [
            "de", "ger", "deutsch", "german", "deutsche",
            "berlin", "munich", "münchen", "hamburg", "frankfurt", "stuttgart",
            "cologne", "köln", "düsseldorf", "bremen", "hannover", "leipzig",
            "dortmund", "essen", "dresden", "nürnberg", "bochum", "wuppertal"
        ],
        "bio_keywords": [
            "germany", "deutschland", "deutsch", "german", "berlin", "münchen", "munich",
            "hamburg", "frankfurt", "stuttgart", "cologne", "köln", "düsseldorf",
            "bremen", "hannover", "leipzig", "dortmund", "essen", "dresden",
            "nürnberg", "bochum", "wuppertal", "bavaria", "bayern", "rheinland", "sachsen"
        ],
        "age_regex": r'(\d{2})\s?(?:jahr|jahre|j|yrs|years|jahrig|alt|age)',
        "location_priority": [
            "berlin", "munich", "münchen", "hamburg", "frankfurt", "stuttgart",
            "cologne", "köln", "düsseldorf", "bremen", "hannover", "leipzig",
            "dortmund", "essen", "dresden", "nürnberg", "bochum", "wuppertal",
            "germany", "deutschland", "bayern", "bavaria", "rheinland", "sachsen"
        ],
        "filter_prompt": (
            "Strictly analyze this Instagram profile for MALE from Germany.\n"
            "CRITERIA (all must be satisfied):\n"
            "1. If the NAME or USERNAME is a typical MALE German name (e.g. Lukas, Leon, Tim, Jonas, Jan, Paul), "
            "and the bio is empty, minimal, or contains only neutral info (city, sport, emoji, etc.), "
            "then this is OK and can be accepted.\n"
            "2. If the bio contains anything female (female names, -a/-ia endings, pronouns like she/her, words like miss, lady), "
            "LGBT/rainbow/pride, marriage/family (wife, frau, verheiratet, kinder, family, married, family, kids, mutter, mama), "
            "beauty, fashion, makeup, cosmetics, nails, spa, or ads/business, migrants (Arabic, African, Asian names), or unclear gender — REJECT.\n"
            "3. If the profile is unclear or suspicious, REJECT.\n"
            "4. If the profile has more than 2500 followers (followers > 2500) — REJECT.\n"
            "Location (Germany/cities) is only a plus, but not required if the rest is OK.\n"
            "If in doubt — REJECT.\n"
            "Answer ONLY 'Yes' or 'No', and briefly explain (max 5 words)."
        )
    },
    "FR": {
        "name_patterns": ["fr", "paris", "france", "français", "francais", "lyon"],
        "bio_keywords": ["france", "paris", "lyon", "marseille", "français", "francais"],
        "age_regex": r'(\d{2})\s?(?:ans|age)',
        "location_priority": ["paris", "lyon", "marseille", "france"],
        "filter_prompt": "Est-ce un homme de France? Vérifiez le nom, le pseudo, la bio. Filtrez les femmes, les orientations non traditionnelles."
    },
    "CH": {  # Швейцария
        "name_patterns": ["ch", "suisse", "schweiz", "svizzera", "zürich", "geneva", "bern", "swiss"],
        "bio_keywords": ["switzerland", "suisse", "schweiz", "svizzera", "zürich", "geneva", "basel", "bern"],
        "age_regex": r'(\d{2})\s?(?:jahr|jahre|ans|years|alt|age)',
        "location_priority": ["zürich", "geneva", "basel", "bern", "lausanne", "switzerland"],
        "filter_prompt": "Ist das ein Mann aus der Schweiz? Prüfe Name, Benutzername, Bio. Filtere Frauen, nicht-traditionelle Orientierungen."
    },
    "PL": {  # Польша
        "name_patterns": ["pl", "pol", "warsaw", "warszawa", "krakow", "polish", "polski"],
        "bio_keywords": ["poland", "polska", "warsaw", "warszawa", "krakow", "gdansk", "polish"],
        "age_regex": r'(\d{2})\s?(?:lat|rok|roku|years|wiek)',
        "location_priority": ["warsaw", "warszawa", "krakow", "gdansk", "poland", "polska"],
        "filter_prompt": "Czy to mężczyzna z Polski? Sprawdź imię, nazwę użytkownika, bio. Odfiltruj kobiety, nietradycyjne orientacje."
    },
    "NL": {  # Нидерланды
        "name_patterns": ["nl", "nederland", "holland", "amsterdam", "rotterdam", "dutch"],
        "bio_keywords": ["netherlands", "nederland", "holland", "amsterdam", "rotterdam", "utrecht", "dutch"],
        "age_regex": r'(\d{2})\s?(?:jaar|years|oud|age)',
        "location_priority": ["amsterdam", "rotterdam", "utrecht", "hague", "netherlands", "nederland"],
        "filter_prompt": "Is dit een man uit Nederland? Controleer naam, gebruikersnaam, bio. Filter vrouwen, niet-traditionele oriëntaties."
    },
    "UA": {  # Украина
        "name_patterns": ["ua", "ukr", "kyiv", "kiev", "lviv", "odesa", "ukrainian", "україна"],
        "bio_keywords": ["ukraine", "ukrainian", "kyiv", "kiev", "lviv", "odesa", "kharkiv", "україна"],
        "age_regex": r'(\d{2})\s?(?:років|роки|рік|years|вік)',
        "location_priority": ["kyiv", "kiev", "lviv", "odesa", "kharkiv", "ukraine", "україна"],
        "filter_prompt": "Це чоловік з України? Перевірте ім'я, нікнейм, біо. Відфільтруйте жінок, нетрадиційні орієнтації."
    },
    "IT & ES": {
        "name_patterns": [
            # Italian
            "it", "ita", "italy", "roma", "milano", "napoli",
            # Spanish
            "es", "esp", "spain", "españa", "madrid", "barcelona", "sevilla", "valencia"
        ],
        "bio_keywords": [
            # Italian
            "italy", "italiano", "roma", "milano", "napoli", "torino", "sicilia", "calcio",
            "italian", "firenze", "venezia", "bologna", "padova", "bergamo",
            # Spanish
            "spain", "español", "españa", "madrid", "barcelona", "valencia", "sevilla", "granada",
            "málaga", "zaragoza", "bilbao", "mallorca", "sevillista", "barça", "real madrid", "espanol"
        ],
        "age_regex": r'(\d{2})\s?(?:anni|años|ano|yo|yrs|years|year|age)',
        "location_priority": [
            # Italy
            "rome", "milan", "naples", "turin", "palermo", "genoa", "bologna", "florence",
            "venice", "bari", "italy", "sicily", "sardinia",
            # Spain
            "madrid", "barcelona", "valencia", "seville", "granada", "malaga", "zaragoza",
            "bilbao", "alicante", "cordoba", "spain", "españa", "canary islands", "mallorca"
        ],
        "filter_prompt": (
            "Strictly analyze this Instagram profile for MALE from Italy or Spain.\n"
            "CRITERIA (all must be satisfied):\n"
            "1. If the NAME or USERNAME is a typical MALE Italian or Spanish name (e.g. Marco, Luca, Juan, Miguel), "
            "and the bio is empty, minimal, or contains only neutral info (city, sport, emoji, etc.), "
            "then this is OK and can be accepted.\n"
            "2. If the bio contains anything female (female names, -a/-ia endings, pronouns like she/her, words like miss, lady), "
            "LGBT/rainbow/pride, marriage/family (wife, esposa, moglie, mujer, family, married, esposo, esposa, figli, hijos, kids), "
            "beauty, fashion, makeup, cosmetics, nails, spa, or ads/business, migrants (Arabic, African, Asian names), or unclear gender — REJECT.\n"
            "3. If the profile is unclear or suspicious, REJECT.\n"
            "4. If the profile has more than 2500 followers (followers > 2500) — REJECT.\n"
            "Location (Italy/Spain) is only a plus, but not required if the rest is OK.\n"
            "If in doubt — REJECT.\n"
            "Answer ONLY 'Yes' or 'No', and briefly explain (max 5 words)."
        )
    }
}