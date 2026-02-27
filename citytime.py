#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from difflib import SequenceMatcher
from zoneinfo import ZoneInfo, available_timezones
# Configuration
HOME = Path.home()
ALIAS_FILE = HOME / ".citytime_aliases"
# Initialize files
ALIAS_FILE.touch(exist_ok=True)
# Default US city aliases
DEFAULT_ALIASES = {
    "newyork": "America/New_York",
    "nyc": "America/New_York",
    "chicago": "America/Chicago",
    "denver": "America/Denver",
    "losangeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "seattle": "America/Los_Angeles",
    "portland": "America/Los_Angeles",
    "sanfrancisco": "America/Los_Angeles",
    "sf": "America/Los_Angeles",
    "sacramento": "America/Los_Angeles",
    "sandiego": "America/Los_Angeles",
    "sanjose": "America/Los_Angeles",
    "lasvegas": "America/Los_Angeles",
    "phoenix": "America/Phoenix",
    "dallas": "America/Chicago",
    "houston": "America/Chicago",
    "atlanta": "America/New_York",
    "miami": "America/New_York",
    "boston": "America/New_York",
    "philadelphia": "America/New_York",
    "detroit": "America/Detroit",
    "minneapolis": "America/Chicago",
    "anchorage": "America/Anchorage",
    "honolulu": "Pacific/Honolulu",
}
# Comprehensive city database
CITY_DATABASE = {
    "birmingham": "America/Chicago", "montgomery": "America/Chicago", "mobile": "America/Chicago",
    "juneau": "America/Anchorage", "fairbanks": "America/Anchorage",
    "tucson": "America/Phoenix", "mesa": "America/Phoenix", "chandler": "America/Phoenix", "scottsdale": "America/Phoenix",
    "littlerock": "America/Chicago", "fayetteville": "America/Chicago",
    "fresno": "America/Los_Angeles", "oakland": "America/Los_Angeles", "bakersfield": "America/Los_Angeles",
    "anaheim": "America/Los_Angeles", "santaana": "America/Los_Angeles", "riverside": "America/Los_Angeles",
    "stockton": "America/Los_Angeles", "irvine": "America/Los_Angeles", "fremont": "America/Los_Angeles",
    "modesto": "America/Los_Angeles", "sanbernadino": "America/Los_Angeles", "oxnard": "America/Los_Angeles",
    "fontana": "America/Los_Angeles", "morenovalley": "America/Los_Angeles", "glendale": "America/Los_Angeles",
    "huntingtonbeach": "America/Los_Angeles", "santaclarita": "America/Los_Angeles", "gardengrove": "America/Los_Angeles",
    "oceanside": "America/Los_Angeles", "ranchocucamonga": "America/Los_Angeles", "santarosa": "America/Los_Angeles",
    "ontario": "America/Los_Angeles", "elkgrove": "America/Los_Angeles", "corona": "America/Los_Angeles",
    "palmdale": "America/Los_Angeles", "salinas": "America/Los_Angeles", "hayward": "America/Los_Angeles",
    "sunnyvale": "America/Los_Angeles", "pasadena": "America/Los_Angeles", "torrance": "America/Los_Angeles",
    "escondido": "America/Los_Angeles", "lakewood": "America/Los_Angeles", "fullerton": "America/Los_Angeles",
    "coloradosprings": "America/Denver", "aurora": "America/Denver", "fortcollins": "America/Denver",
    "thornton": "America/Denver", "arvada": "America/Denver", "westminster": "America/Denver",
    "pueblo": "America/Denver", "boulder": "America/Denver",
    "bridgeport": "America/New_York", "newhaven": "America/New_York", "stamford": "America/New_York",
    "hartford": "America/New_York", "waterbury": "America/New_York",
    "wilmington": "America/New_York", "dover": "America/New_York",
    "jacksonville": "America/New_York", "tampa": "America/New_York", "orlando": "America/New_York",
    "stpetersburg": "America/New_York", "hialeah": "America/New_York", "tallahassee": "America/New_York",
    "fortlauderdale": "America/New_York", "capecoral": "America/New_York", "pembrokepines": "America/New_York",
    "hollywood": "America/New_York", "miramar": "America/New_York", "gainesville": "America/New_York",
    "coralsprings": "America/New_York", "clearwater": "America/New_York", "westpalmbeach": "America/New_York",
    "columbus": "America/New_York", "augusta": "America/New_York", "macon": "America/New_York",
    "savannah": "America/New_York", "sandysprings": "America/New_York", "roswell": "America/New_York",
    "pearlcity": "Pacific/Honolulu", "hilo": "Pacific/Honolulu", "kailua": "Pacific/Honolulu",
    "boise": "America/Boise", "meridian": "America/Boise", "nampa": "America/Boise",
    "idahofalls": "America/Boise", "pocatello": "America/Boise",
    "rockford": "America/Chicago", "joliet": "America/Chicago", "naperville": "America/Chicago",
    "springfield": "America/Chicago", "peoria": "America/Chicago", "elgin": "America/Chicago", "waukegan": "America/Chicago",
    "indianapolis": "America/Indiana/Indianapolis", "fortwayne": "America/Indiana/Indianapolis",
    "evansville": "America/Indiana/Indianapolis", "southbend": "America/Indiana/Indianapolis", "carmel": "America/Indiana/Indianapolis",
    "desmoines": "America/Chicago", "cedarrapids": "America/Chicago", "davenport": "America/Chicago", "siouxcity": "America/Chicago",
    "wichita": "America/Chicago", "overlandpark": "America/Chicago", "kansascity": "America/Chicago",
    "olathe": "America/Chicago", "topeka": "America/Chicago",
    "louisville": "America/Kentucky/Louisville", "lexington": "America/Kentucky/Louisville", "bowlinggreen": "America/Chicago",
    "neworleans": "America/Chicago", "batonrouge": "America/Chicago", "shreveport": "America/Chicago", "lafayette": "America/Chicago",
    "lewiston": "America/New_York", "bangor": "America/New_York",
    "baltimore": "America/New_York", "frederick": "America/New_York", "rockville": "America/New_York",
    "gaithersburg": "America/New_York", "bowie": "America/New_York",
    "worcester": "America/New_York", "lowell": "America/New_York", "cambridge": "America/New_York",
    "newbedford": "America/New_York", "brockton": "America/New_York", "quincy": "America/New_York",
    "grandrapids": "America/Detroit", "warren": "America/Detroit", "sterlingheights": "America/Detroit",
    "annarbor": "America/Detroit", "lansing": "America/Detroit", "flint": "America/Detroit",
    "dearborn": "America/Detroit", "livonia": "America/Detroit", "westland": "America/Detroit",
    "troy": "America/Detroit", "farmingtonhills": "America/Detroit", "kalamazoo": "America/Detroit",
    "wyoming": "America/Detroit", "southfield": "America/Detroit", "rochesterhills": "America/Detroit",
    "taylor": "America/Detroit", "pontiac": "America/Detroit", "stclairshores": "America/Detroit",
    "royaloak": "America/Detroit", "novi": "America/Detroit", "dearbornheights": "America/Detroit",
    "stpaul": "America/Chicago", "duluth": "America/Chicago", "bloomington": "America/Chicago",
    "jackson": "America/Chicago", "gulfport": "America/Chicago", "southaven": "America/Chicago",
    "stlouis": "America/Chicago", "independence": "America/Chicago", "columbia": "America/Chicago",
    "billings": "America/Denver", "missoula": "America/Denver", "greatfalls": "America/Denver",
    "omaha": "America/Chicago", "lincoln": "America/Chicago", "bellevue": "America/Chicago",
    "henderson": "America/Los_Angeles", "reno": "America/Los_Angeles", "northlasvegas": "America/Los_Angeles", "sparks": "America/Los_Angeles",
    "manchester": "America/New_York", "nashua": "America/New_York", "concord": "America/New_York",
    "newark": "America/New_York", "jerseycity": "America/New_York", "paterson": "America/New_York",
    "elizabeth": "America/New_York", "edison": "America/New_York", "woodbridge": "America/New_York",
    "tomsriver": "America/New_York", "hamilton": "America/New_York", "trenton": "America/New_York",
    "albuquerque": "America/Denver", "lascruces": "America/Denver", "riorancho": "America/Denver", "santafe": "America/Denver",
    "buffalo": "America/New_York", "yonkers": "America/New_York", "syracuse": "America/New_York",
    "albany": "America/New_York", "newrochelle": "America/New_York", "mountvernon": "America/New_York",
    "schenectady": "America/New_York", "utica": "America/New_York",
    "charlotte": "America/New_York", "raleigh": "America/New_York", "greensboro": "America/New_York",
    "durham": "America/New_York", "winstonsalem": "America/New_York", "cary": "America/New_York", "highpoint": "America/New_York",
    "fargo": "America/Chicago", "bismarck": "America/Chicago", "grandforks": "America/Chicago",
    "cleveland": "America/New_York", "cincinnati": "America/New_York", "toledo": "America/New_York",
    "akron": "America/New_York", "dayton": "America/New_York", "parma": "America/New_York",
    "canton": "America/New_York", "youngstown": "America/New_York",
    "oklahomacity": "America/Chicago", "tulsa": "America/Chicago", "norman": "America/Chicago", "brokenarrow": "America/Chicago",
    "salem": "America/Los_Angeles", "eugene": "America/Los_Angeles", "gresham": "America/Los_Angeles",
    "hillsboro": "America/Los_Angeles", "beaverton": "America/Los_Angeles",
    "pittsburgh": "America/New_York", "allentown": "America/New_York", "erie": "America/New_York",
    "reading": "America/New_York", "scranton": "America/New_York", "bethlehem": "America/New_York",
    "providence": "America/New_York", "warwick": "America/New_York", "cranston": "America/New_York",
    "charleston": "America/New_York", "northcharleston": "America/New_York",
    "siouxfalls": "America/Chicago", "rapidcity": "America/Denver",
    "memphis": "America/Chicago", "nashville": "America/Chicago", "knoxville": "America/New_York",
    "chattanooga": "America/New_York", "clarksville": "America/Chicago",
    "sanantonio": "America/Chicago", "austin": "America/Chicago", "fortworth": "America/Chicago",
    "elpaso": "America/Denver", "arlington": "America/Chicago", "corpuschristi": "America/Chicago",
    "plano": "America/Chicago", "laredo": "America/Chicago", "lubbock": "America/Chicago",
    "garland": "America/Chicago", "irving": "America/Chicago", "amarillo": "America/Chicago",
    "grandprairie": "America/Chicago", "brownsville": "America/Chicago", "mckinney": "America/Chicago",
    "mesquite": "America/Chicago", "killeen": "America/Chicago", "frisco": "America/Chicago",
    "waco": "America/Chicago", "carrollton": "America/Chicago",
    "saltlakecity": "America/Denver", "westvalleycity": "America/Denver", "provo": "America/Denver",
    "westjordan": "America/Denver", "orem": "America/Denver",
    "burlington": "America/New_York", "essexjunction": "America/New_York",
    "virginiabeach": "America/New_York", "norfolk": "America/New_York", "chesapeake": "America/New_York",
    "richmond": "America/New_York", "newportnews": "America/New_York", "alexandria": "America/New_York",
    "hampton": "America/New_York", "roanoke": "America/New_York", "portsmouth": "America/New_York",
    "spokane": "America/Los_Angeles", "tacoma": "America/Los_Angeles", "bellevue": "America/Los_Angeles",
    "kent": "America/Los_Angeles", "everett": "America/Los_Angeles", "renton": "America/Los_Angeles", "spokanevalley": "America/Los_Angeles",
    "huntington": "America/New_York",
    "milwaukee": "America/Chicago", "madison": "America/Chicago", "greenbay": "America/Chicago",
    "kenosha": "America/Chicago", "racine": "America/Chicago",
    "cheyenne": "America/Denver", "casper": "America/Denver",
    "london": "Europe/London", "paris": "Europe/Paris", "berlin": "Europe/Berlin", "madrid": "Europe/Madrid",
    "rome": "Europe/Rome", "amsterdam": "Europe/Amsterdam", "brussels": "Europe/Brussels", "vienna": "Europe/Vienna",
    "prague": "Europe/Prague", "budapest": "Europe/Budapest", "warsaw": "Europe/Warsaw", "stockholm": "Europe/Stockholm",
    "oslo": "Europe/Oslo", "copenhagen": "Europe/Copenhagen", "helsinki": "Europe/Helsinki", "dublin": "Europe/Dublin",
    "lisbon": "Europe/Lisbon", "moscow": "Europe/Moscow", "istanbul": "Europe/Istanbul",
    "tokyo": "Asia/Tokyo", "beijing": "Asia/Shanghai", "shanghai": "Asia/Shanghai", "hongkong": "Asia/Hong_Kong",
    "singapore": "Asia/Singapore", "seoul": "Asia/Seoul", "bangkok": "Asia/Bangkok", "jakarta": "Asia/Jakarta",
    "manila": "Asia/Manila", "mumbai": "Asia/Kolkata", "delhi": "Asia/Kolkata", "bangalore": "Asia/Kolkata",
    "karachi": "Asia/Karachi", "dubai": "Asia/Dubai", "telaviv": "Asia/Jerusalem", "riyadh": "Asia/Riyadh",
    "sydney": "Australia/Sydney", "melbourne": "Australia/Melbourne", "brisbane": "Australia/Brisbane",
    "perth": "Australia/Perth", "adelaide": "Australia/Adelaide", "auckland": "Pacific/Auckland", "wellington": "Pacific/Auckland",
    "toronto": "America/Toronto", "montreal": "America/Montreal", "calgary": "America/Edmonton", "ottawa": "America/Toronto",
    "mexicocity": "America/Mexico_City", "guadalajara": "America/Mexico_City", "monterrey": "America/Monterrey",
    "buenosaires": "America/Argentina/Buenos_Aires", "saopaulo": "America/Sao_Paulo", "riodejaneiro": "America/Sao_Paulo",
    "lima": "America/Lima", "bogota": "America/Bogota", "santiago": "America/Santiago", "caracas": "America/Caracas",
    "cairo": "Africa/Cairo", "johannesburg": "Africa/Johannesburg", "lagos": "Africa/Lagos",
    "nairobi": "Africa/Nairobi", "casablanca": "Africa/Casablanca",
}
# Country to timezone mapping (for countries whose name doesn't appear in IANA timezone IDs)
COUNTRY_TIMEZONES = {
    "italy": ["Europe/Rome"],
    "france": ["Europe/Paris"],
    "germany": ["Europe/Berlin"],
    "spain": ["Europe/Madrid"],
    "uk": ["Europe/London"], "unitedkingdom": ["Europe/London"], "england": ["Europe/London"],
    "netherlands": ["Europe/Amsterdam"], "holland": ["Europe/Amsterdam"],
    "belgium": ["Europe/Brussels"],
    "austria": ["Europe/Vienna"],
    "switzerland": ["Europe/Zurich"],
    "sweden": ["Europe/Stockholm"],
    "norway": ["Europe/Oslo"],
    "denmark": ["Europe/Copenhagen"],
    "finland": ["Europe/Helsinki"],
    "portugal": ["Europe/Lisbon"],
    "greece": ["Europe/Athens"],
    "poland": ["Europe/Warsaw"],
    "czechrepublic": ["Europe/Prague"], "czechia": ["Europe/Prague"],
    "hungary": ["Europe/Budapest"],
    "romania": ["Europe/Bucharest"],
    "ukraine": ["Europe/Kyiv"],
    "turkey": ["Europe/Istanbul"],
    "israel": ["Asia/Jerusalem"],
    "saudiarabia": ["Asia/Riyadh"],
    "uae": ["Asia/Dubai"], "unitedarabemirates": ["Asia/Dubai"],
    "india": ["Asia/Kolkata"],
    "china": ["Asia/Shanghai"],
    "japan": ["Asia/Tokyo"],
    "southkorea": ["Asia/Seoul"], "korea": ["Asia/Seoul"],
    "thailand": ["Asia/Bangkok"],
    "indonesia": ["Asia/Jakarta", "Asia/Makassar", "Asia/Jayapura"],
    "philippines": ["Asia/Manila"],
    "pakistan": ["Asia/Karachi"],
    "bangladesh": ["Asia/Dhaka"],
    "egypt": ["Africa/Cairo"],
    "southafrica": ["Africa/Johannesburg"],
    "nigeria": ["Africa/Lagos"],
    "kenya": ["Africa/Nairobi"],
    "morocco": ["Africa/Casablanca"],
    "newzealand": ["Pacific/Auckland"],
    "canada": ["America/Toronto", "America/Vancouver", "America/Edmonton", "America/Winnipeg", "America/Halifax"],
    "brazil": ["America/Sao_Paulo", "America/Manaus", "America/Belem"],
    "argentina": ["America/Argentina/Buenos_Aires"],
    "chile": ["America/Santiago"],
    "colombia": ["America/Bogota"],
    "peru": ["America/Lima"],
    "venezuela": ["America/Caracas"],
}
# US State to timezone mapping
STATE_TIMEZONES = {
    "alabama": ["America/Chicago"], "alaska": ["America/Anchorage"], "arizona": ["America/Phoenix"],
    "arkansas": ["America/Chicago"], "california": ["America/Los_Angeles"], "colorado": ["America/Denver"],
    "connecticut": ["America/New_York"], "delaware": ["America/New_York"],
    "florida": ["America/New_York", "America/Chicago"], "georgia": ["America/New_York"],
    "hawaii": ["Pacific/Honolulu"], "idaho": ["America/Boise", "America/Denver"],
    "illinois": ["America/Chicago"], "indiana": ["America/Indiana/Indianapolis", "America/Chicago"],
    "iowa": ["America/Chicago"], "kansas": ["America/Chicago", "America/Denver"],
    "kentucky": ["America/Kentucky/Louisville", "America/Chicago"], "louisiana": ["America/Chicago"],
    "maine": ["America/New_York"], "maryland": ["America/New_York"], "massachusetts": ["America/New_York"],
    "michigan": ["America/Detroit"], "minnesota": ["America/Chicago"], "mississippi": ["America/Chicago"],
    "missouri": ["America/Chicago"], "montana": ["America/Denver"],
    "nebraska": ["America/Chicago", "America/Denver"], "nevada": ["America/Los_Angeles"],
    "newhampshire": ["America/New_York"], "newjersey": ["America/New_York"], "newmexico": ["America/Denver"],
    "newyork": ["America/New_York"], "northcarolina": ["America/New_York"], "northdakota": ["America/Chicago"],
    "ohio": ["America/New_York"], "oklahoma": ["America/Chicago"], "oregon": ["America/Los_Angeles"],
    "pennsylvania": ["America/New_York"], "rhodeisland": ["America/New_York"], "southcarolina": ["America/New_York"],
    "southdakota": ["America/Chicago", "America/Denver"], "tennessee": ["America/Chicago", "America/New_York"],
    "texas": ["America/Chicago", "America/Denver"], "utah": ["America/Denver"], "vermont": ["America/New_York"],
    "virginia": ["America/New_York"], "washington": ["America/Los_Angeles"], "westvirginia": ["America/New_York"],
    "wisconsin": ["America/Chicago"], "wyoming": ["America/Denver"],
    "al": ["America/Chicago"], "ak": ["America/Anchorage"], "az": ["America/Phoenix"], "ar": ["America/Chicago"],
    "ca": ["America/Los_Angeles"], "co": ["America/Denver"], "ct": ["America/New_York"], "de": ["America/New_York"],
    "fl": ["America/New_York"], "ga": ["America/New_York"], "hi": ["Pacific/Honolulu"], "id": ["America/Boise"],
    "il": ["America/Chicago"], "in": ["America/Indiana/Indianapolis"], "ia": ["America/Chicago"], "ks": ["America/Chicago"],
    "ky": ["America/Kentucky/Louisville"], "la": ["America/Chicago"], "me": ["America/New_York"], "md": ["America/New_York"],
    "ma": ["America/New_York"], "mi": ["America/Detroit"], "mn": ["America/Chicago"], "ms": ["America/Chicago"],
    "mo": ["America/Chicago"], "mt": ["America/Denver"], "ne": ["America/Chicago"], "nv": ["America/Los_Angeles"],
    "nh": ["America/New_York"], "nj": ["America/New_York"], "nm": ["America/Denver"], "ny": ["America/New_York"],
    "nc": ["America/New_York"], "nd": ["America/Chicago"], "oh": ["America/New_York"], "ok": ["America/Chicago"],
    "or": ["America/Los_Angeles"], "pa": ["America/New_York"], "ri": ["America/New_York"], "sc": ["America/New_York"],
    "sd": ["America/Chicago"], "tn": ["America/Chicago"], "tx": ["America/Chicago"], "ut": ["America/Denver"],
    "vt": ["America/New_York"], "va": ["America/New_York"], "wa": ["America/Los_Angeles"], "wv": ["America/New_York"],
    "wi": ["America/Chicago"], "wy": ["America/Denver"],
}
def load_aliases() -> Dict[str, str]:
    """Load aliases from file and merge with defaults and city database."""
    aliases = CITY_DATABASE.copy()
    aliases.update(DEFAULT_ALIASES)
    if ALIAS_FILE.exists():
        with open(ALIAS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key and value:
                        aliases[key] = value
    return aliases
def save_alias(city: str, tz: str) -> None:
    """Save a single alias to file."""
    city = city.lower()
    lines = []
    if ALIAS_FILE.exists():
        with open(ALIAS_FILE, 'r') as f:
            lines = [line for line in f if not line.startswith(f"{city}=")]
    lines.append(f"{city}={tz}\n")
    temp_file = ALIAS_FILE.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        f.writelines(lines)
    temp_file.replace(ALIAS_FILE)
def get_timezones_by_country(country: str, all_timezones: List[str]) -> List[str]:
    """Get timezones for a country, using COUNTRY_TIMEZONES mapping then falling back to string search."""
    country_normalized = country.lower().replace(' ', '').replace('.', '').replace('-', '')
    if country_normalized in COUNTRY_TIMEZONES:
        return COUNTRY_TIMEZONES[country_normalized]
    return [tz for tz in all_timezones if country.lower() in tz.lower()]
def fetch_valid_timezones(debug: bool = False) -> Optional[List[str]]:
    """Get valid timezones from the system's zoneinfo database."""
    timezones = sorted(available_timezones())
    if debug:
        print(f"✅ Loaded {len(timezones)} timezones from system zoneinfo", file=sys.stderr)
    return timezones
def get_timezone_by_state(state: str) -> Optional[str]:
    """Get timezone for a US state."""
    state_normalized = state.lower().replace(' ', '').replace('.', '')
    timezones = STATE_TIMEZONES.get(state_normalized, [])
    if not timezones:
        return None
    if len(timezones) > 1:
        print(f"📍 {state.title()} has multiple timezones:")
        for i, tz in enumerate(timezones, 1):
            tz_display = tz.split('/')[-1].replace('_', ' ')
            print(f"  {i}) {tz} ({tz_display})")
        choice = input(f"Select timezone [1-{len(timezones)}]: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(timezones):
                return timezones[idx]
        except ValueError:
            pass
        print(f"Using default: {timezones[0]}")
        return timezones[0]
    return timezones[0]
def similarity_score(city: str, timezone: str) -> float:
    """Calculate similarity score between city name and timezone."""
    city_lower = city.lower().replace('-', '').replace('_', '').replace(' ', '').replace('.', '')
    tz_city = os.path.basename(timezone).lower().replace('-', '').replace('_', '')
    return SequenceMatcher(None, city_lower, tz_city).ratio()
def find_timezone_matches(city: str, debug: bool = False) -> List[Tuple[str, float]]:
    """Find timezone matches for a city name with similarity scores."""
    city_normalized = city.lower().replace('-', '').replace('_', '').replace(' ', '').replace('.', '')
    if city_normalized in CITY_DATABASE:
        return [(CITY_DATABASE[city_normalized], 1.0)]
    db_matches = []
    for db_city, tz in CITY_DATABASE.items():
        db_city_norm = db_city.lower().replace('-', '').replace('_', '').replace(' ', '').replace('.', '')
        if city_normalized in db_city_norm or db_city_norm in city_normalized:
            score = similarity_score(city, db_city)
            db_matches.append((tz, score))
    if db_matches:
        unique_matches = {}
        for tz, score in db_matches:
            if tz not in unique_matches or unique_matches[tz] < score:
                unique_matches[tz] = score
        return sorted(unique_matches.items(), key=lambda x: x[1], reverse=True)
    timezones = fetch_valid_timezones(debug=debug)
    if not timezones:
        return []
    matches = []
    for tz in timezones:
        tz_city = os.path.basename(tz).lower().replace('-', '').replace('_', '')
        if city_normalized == tz_city:
            matches.append((tz, 1.0))
        elif city_normalized in tz_city or tz_city in city_normalized:
            score = similarity_score(city, tz)
            matches.append((tz, score))
        else:
            score = similarity_score(city, tz)
            if score >= 0.7:
                matches.append((tz, score))
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches
def auto_match_timezone_with_context(city: str, debug: bool = False) -> Optional[str]:
    """Helper function to match timezone when automatic matching fails or is rejected."""
    print()
    print("Let's find the right timezone:")
    print("  1) Specify US state")
    print("  2) Specify country")
    print("  3) Enter timezone manually")
    print("  4) Skip")
    choice = input("Choose option [1-4]: ").strip()
    if choice == "1":
        state = input("Enter state name or abbreviation: ").strip()
        tz = get_timezone_by_state(state)
        if tz:
            print(f"✅ Using {tz} for {state}")
            return tz
        else:
            print(f"❌ State '{state}' not recognized")
    elif choice == "2":
        country = input("Enter country name: ").strip()
        timezones = fetch_valid_timezones(debug=debug)
        if timezones:
            country_matches = get_timezones_by_country(country, timezones)
            if country_matches:
                if len(country_matches) == 1:
                    return country_matches[0]
                else:
                    print(f"🔍 Found {len(country_matches)} timezones:")
                    for i, tz in enumerate(country_matches[:15], 1):
                        print(f"  {i}) {tz}")
                    selection = input(f"Select [1-{min(15, len(country_matches))}]: ").strip()
                    try:
                        idx = int(selection) - 1
                        if 0 <= idx < len(country_matches):
                            return country_matches[idx]
                    except ValueError:
                        pass
            else:
                print(f"❌ No timezones found for country: {country}")
    elif choice == "3":
        manual_tz = input("Enter timezone: ").strip()
        if manual_tz and is_valid_timezone(manual_tz):
            return manual_tz
        elif manual_tz:
            print(f"❌ Invalid timezone: {manual_tz}")
    return None
def auto_match_timezone(city: str, debug: bool = False) -> Optional[str]:
    """Automatically match a city to its timezone with user confirmation."""
    matches = find_timezone_matches(city, debug=debug)
    if not matches:
        print(f"🌍 No automatic match found for '{city}'")
        print()
        print("Options:")
        print("  1) Specify US state (e.g., Michigan, MI)")
        print("  2) Specify country (e.g., France, Japan)")
        print("  3) Enter timezone manually (e.g., America/Detroit)")
        print("  4) Skip")
        choice = input("Choose option [1-4]: ").strip()
        if choice == "1":
            state = input("Enter state name or abbreviation: ").strip()
            tz = get_timezone_by_state(state)
            if tz:
                print(f"✅ Matched to {tz} based on state: {state}")
                response = input(f"Use this timezone for '{city}'? [Y/n]: ").strip().lower()
                if response in ['', 'y', 'yes']:
                    return tz
            else:
                print(f"❌ State '{state}' not recognized")
        elif choice == "2":
            country = input("Enter country name: ").strip()
            timezones = fetch_valid_timezones(debug=debug)
            if timezones:
                country_matches = get_timezones_by_country(country, timezones)
                if country_matches:
                    if len(country_matches) == 1:
                        tz = country_matches[0]
                        print(f"✅ Found timezone: {tz}")
                        response = input(f"Use this timezone for '{city}'? [Y/n]: ").strip().lower()
                        if response in ['', 'y', 'yes']:
                            return tz
                    else:
                        print(f"🔍 Found {len(country_matches)} timezones:")
                        for i, tz in enumerate(country_matches[:15], 1):
                            print(f"  {i}) {tz}")
                        selection = input(f"Select timezone [1-{min(15, len(country_matches))}]: ").strip()
                        try:
                            idx = int(selection) - 1
                            if 0 <= idx < len(country_matches):
                                return country_matches[idx]
                        except ValueError:
                            pass
                else:
                    print(f"❌ No timezones found for country: {country}")
        elif choice == "3":
            manual_tz = input("Enter timezone (e.g., America/Detroit): ").strip()
            if manual_tz and is_valid_timezone(manual_tz):
                return manual_tz
            elif manual_tz:
                print(f"❌ Invalid timezone: {manual_tz}")
        return None
    if matches[0][1] == 1.0:
        best_match = matches[0][0]
        print(f"✨ Auto-matched '{city}' → {best_match}")
        response = input(f"Use this timezone? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            return best_match
        else:
            return auto_match_timezone_with_context(city, debug)
    if len(matches) > 1:
        print(f"🔍 Found multiple timezone matches for '{city}':")
        top_matches = matches[:10]
        for i, (tz, score) in enumerate(top_matches, 1):
            confidence = "★★★" if score >= 0.95 else "★★" if score >= 0.85 else "★"
            print(f"  {i}) {tz} {confidence}")
        print(f"  0) None of these")
        choice = input(f"Select timezone [1-{len(top_matches)}, 0 for more options]: ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(top_matches):
                return top_matches[idx - 1][0]
            elif idx == 0:
                return auto_match_timezone_with_context(city, debug)
        except ValueError:
            pass
    elif matches:
        best_match = matches[0][0]
        confidence_pct = int(matches[0][1] * 100)
        print(f"🔍 Best match for '{city}': {best_match} ({confidence_pct}% confidence)")
        response = input(f"Use this timezone? [Y/n]: ").strip().lower()
        if response in ['', 'y', 'yes']:
            return best_match
        else:
            return auto_match_timezone_with_context(city, debug)
    return None
def is_valid_timezone(tz: str) -> bool:
    """Validate timezone format and existence."""
    if '/' not in tz:
        return False
    return tz in available_timezones()
def add_alias(city: str, tz: str, auto_match: bool = False, debug: bool = False) -> bool:
    """Add a new alias with optional auto-matching."""
    city = city.lower()
    if not city:
        print("❌ Invalid city name", file=sys.stderr)
        return False
    if not tz and auto_match:
        tz = auto_match_timezone(city, debug=debug)
        if not tz:
            print("⏭️ Skipping alias addition.", file=sys.stderr)
            return False
    if not tz:
        print("❌ Invalid alias format. Usage: city timezone", file=sys.stderr)
        return False
    if not is_valid_timezone(tz):
        print(f"❌ Invalid timezone: {tz}", file=sys.stderr)
        return False
    save_alias(city, tz)
    print(f"✅ Alias added: {city} → {tz}")
    return True
def list_aliases() -> None:
    """List all configured aliases."""
    aliases = load_aliases()
    if not aliases:
        print("📜 No aliases configured.")
        return
    print("📜 Current aliases:")
    for city in sorted(aliases.keys()):
        print(f"  {city} → {aliases[city]}")
def update_aliases_from_api(debug: bool = False) -> None:
    """Update aliases from API timezone list."""
    print("🔄 Updating aliases from API...")
    
    if debug:
        print("🐛 DEBUG MODE ENABLED", file=sys.stderr)
        print("🐛 Starting timezone fetch...", file=sys.stderr)
    
    timezones = fetch_valid_timezones(debug=debug)
    
    if not timezones:
        print("❌ Failed to fetch timezones", file=sys.stderr)
        return
    
    if debug:
        print(f"🐛 Successfully fetched {len(timezones)} timezones", file=sys.stderr)
        print(f"🐛 Sample timezones: {timezones[:5]}", file=sys.stderr)
    
    aliases = load_aliases()
    if debug:
        print(f"🐛 Current aliases count: {len(aliases)}", file=sys.stderr)
    
    count = 0
    skipped = 0
    
    for tz in timezones:
        city = os.path.basename(tz).lower().replace('_', '-')
        
        if city in aliases:
            skipped += 1
            if debug and skipped <= 5:
                print(f"🐛 Skipping existing: {city} → {aliases[city]}", file=sys.stderr)
            continue
        
        save_alias(city, tz)
        count += 1
        
        if debug and count <= 10:
            print(f"🐛 Added: {city} → {tz}", file=sys.stderr)
        elif count % 50 == 0:
            print(f"  ... processed {count} aliases")
            if debug:
                print(f"🐛 Progress: {count} added, {skipped} skipped", file=sys.stderr)
    
    print(f"✅ Aliases updated: {count} new entries")
    if debug:
        print(f"🐛 Final stats: {count} added, {skipped} skipped, {count + skipped} total processed", file=sys.stderr)
def get_time(raw: str, debug: bool = False) -> bool:
    """Get time for a city or timezone."""
    aliases = load_aliases()
    city = raw.lower()
    tz = aliases.get(city, city)
    if not is_valid_timezone(tz):
        matched_tz = auto_match_timezone(city, debug=debug)
        if matched_tz and is_valid_timezone(matched_tz):
            tz = matched_tz
            response = input(f"Save '{city}' → {tz} as an alias? [Y/n]: ").strip().lower()
            if response in ['', 'y', 'yes']:
                save_alias(city, tz)
        else:
            print(f"❓ City '{city}' not found.", file=sys.stderr)
            return False
    try:
        tz_info = ZoneInfo(tz)
        now = datetime.now(tz_info)
        time_str = now.isoformat()
        if debug:
            print(f"🐛 Resolved {tz} via system zoneinfo", file=sys.stderr)
        print(f"🕒 {city} → {tz} → {time_str}")
        return True
    except Exception as e:
        if debug:
            print(f"❌ Error resolving timezone {tz}: {e}", file=sys.stderr)
        print(f"❌ Failed to get time for {tz}", file=sys.stderr)
        return False
def batch_add(file_path: str) -> None:
    """Batch add aliases from file."""
    try:
        with open(file_path, 'r') as f:
            count = 0
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(None, 1)
                if len(parts) != 2:
                    print(f"⚠️ Skipping invalid line: '{line}'", file=sys.stderr)
                    continue
                city, tz = parts
                if add_alias(city, tz):
                    count += 1
            print(f"✅ Batch add complete: {count} aliases added")
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}", file=sys.stderr)
def edit_aliases() -> None:
    """Interactive alias editor."""
    aliases = load_aliases()
    print("🧠 Interactive Alias Editor")
    print("Type the number to edit, or press Enter to skip.")
    sorted_cities = sorted(aliases.keys())
    for i, city in enumerate(sorted_cities, 1):
        print(f"{i}) {city} → {aliases[city]}")
    choice = input("Select alias number to edit: ").strip()
    if not choice:
        return
    try:
        idx = int(choice) - 1
        selected = sorted_cities[idx]
        new_tz = input(f"Edit timezone for '{selected}' (current: {aliases[selected]}): ").strip()
        if new_tz:
            add_alias(selected, new_tz)
        else:
            print("⏭️ Skipped")
    except (ValueError, IndexError):
        print("❌ Invalid selection")
def interactive_mode() -> None:
    """Interactive menu-driven interface."""
    os.system('clear' if os.name == 'posix' else 'cls')
    print("🧑‍💻 Interactive Mode")
    options = ["Show Options", "Add Alias (Auto-Match)", "Add Alias (Manual)", "Remove Alias", "List Aliases",
               "Lookup Time", "Lookup Time (Debug Mode)", "Batch Time Lookup", "Update Aliases from Timezone DB",
               "Update Aliases from Timezone DB (Debug Mode)", "Exit"]
    while True:
        print()
        for i, option in enumerate(options):
            print(f"{i}) {option}")
        print()
        choice = input(f"Choose an option [0-{len(options)-1}]: ").strip()
        if choice == "0":
            continue
        elif choice == "1":
            city = input("City: ").strip()
            if city:
                add_alias(city, "", auto_match=True)
        elif choice == "2":
            city = input("City: ").strip()
            tz = input("Timezone: ").strip()
            add_alias(city, tz)
        elif choice == "3":
            city = input("City to remove: ").strip().lower()
            aliases = load_aliases()
            if city in aliases:
                lines = []
                with open(ALIAS_FILE, 'r') as f:
                    lines = [line for line in f if not line.startswith(f"{city}=")]
                with open(ALIAS_FILE, 'w') as f:
                    f.writelines(lines)
                print(f"❌ Removed {city}")
            else:
                print(f"❓ Alias '{city}' not found")
        elif choice == "4":
            list_aliases()
        elif choice == "5":
            city = input("City or alias: ").strip()
            get_time(city)
        elif choice == "6":
            city = input("City or alias: ").strip()
            get_time(city, debug=True)
        elif choice == "7":
            file_path = input("File path: ").strip()
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            get_time(line)
            except FileNotFoundError:
                print(f"❌ File not found: {file_path}", file=sys.stderr)
        elif choice == "8":
            update_aliases_from_api()
        elif choice == "9":
            update_aliases_from_api(debug=True)
        elif choice == "10":
            break
        else:
            print("❌ Invalid choice")
def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("🛠️ Usage:")
        print(f"  {sys.argv[0]} --list")
        print(f"  {sys.argv[0]} --add city [timezone]")
        print(f"  {sys.argv[0]} --time city_or_alias [--debug]")
        print(f"  {sys.argv[0]} --batch-add aliases.txt")
        print(f"  {sys.argv[0]} --edit-aliases")
        print(f"  {sys.argv[0]} --update-aliases [--debug]")
        print(f"  {sys.argv[0]} --interactive")
        return
    cmd = sys.argv[1]
    if cmd == "--add":
        if len(sys.argv) >= 3:
            city = sys.argv[2]
            tz = sys.argv[3] if len(sys.argv) >= 4 else ""
            add_alias(city, tz, auto_match=(not tz))
        else:
            print("Usage: --add city [timezone]", file=sys.stderr)
    elif cmd == "--list":
        list_aliases()
    elif cmd == "--time":
        if len(sys.argv) >= 3:
            debug = len(sys.argv) >= 4 and sys.argv[3] == "--debug"
            get_time(sys.argv[2], debug)
        else:
            print("Usage: --time city_or_alias [--debug]", file=sys.stderr)
    elif cmd == "--batch-add":
        if len(sys.argv) >= 3:
            batch_add(sys.argv[2])
        else:
            print("Usage: --batch-add file", file=sys.stderr)
    elif cmd == "--edit-aliases":
        edit_aliases()
    elif cmd == "--update-aliases":
        debug = len(sys.argv) >= 3 and sys.argv[2] == "--debug"
        update_aliases_from_api(debug)
    elif cmd == "--interactive":
        interactive_mode()
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)
if __name__ == "__main__":
    main()
