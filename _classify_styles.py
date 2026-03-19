#!/usr/bin/env python3
"""
Classify museum chair entries into style periods based on dating, designer, origin, materials.
Reads _gap_analysis.json, outputs _style_enrichment.json.
"""
import json
import re
import sys

# ── Known designer → style mappings ──────────────────────────────────
# Maps designer name fragments (lowercased) to style period
DESIGNER_STYLES = {
    # Scandinavian Modernism (~1930-1970)
    'hans wegner': 'Skandinavisk modernisme',
    'wegner, hans': 'Skandinavisk modernisme',
    'finn juhl': 'Skandinavisk modernisme',
    'juhl, finn': 'Skandinavisk modernisme',
    'arne jacobsen': 'Skandinavisk modernisme',
    'jacobsen, arne': 'Skandinavisk modernisme',
    'alvar aalto': 'Skandinavisk modernisme',
    'aalto, alvar': 'Skandinavisk modernisme',
    'bruno mathsson': 'Skandinavisk modernisme',
    'mathsson, bruno': 'Skandinavisk modernisme',
    'kaare klint': 'Skandinavisk modernisme',
    'klint, kaare': 'Skandinavisk modernisme',
    'poul kjaerholm': 'Skandinavisk modernisme',
    'kjaerholm, poul': 'Skandinavisk modernisme',
    'kjærholm, poul': 'Skandinavisk modernisme',
    'borge mogensen': 'Skandinavisk modernisme',
    'mogensen, borge': 'Skandinavisk modernisme',
    'mogensen, børge': 'Skandinavisk modernisme',
    'poul henningsen': 'Skandinavisk modernisme',
    'henningsen, poul': 'Skandinavisk modernisme',
    'nanna ditzel': 'Skandinavisk modernisme',
    'ditzel, nanna': 'Skandinavisk modernisme',
    'verner panton': 'Skandinavisk modernisme',
    'panton, verner': 'Skandinavisk modernisme',
    'ilmari tapiovaara': 'Skandinavisk modernisme',
    'tapiovaara, ilmari': 'Skandinavisk modernisme',
    'carl-johan boman': 'Skandinavisk modernisme',
    'boman, carl-johan': 'Skandinavisk modernisme',
    'peter opsvik': 'Skandinavisk modernisme',
    'opsvik, peter': 'Skandinavisk modernisme',
    'ingmar relling': 'Skandinavisk modernisme',
    'relling, ingmar': 'Skandinavisk modernisme',
    'sigurd resell': 'Skandinavisk modernisme',
    'resell, sigurd': 'Skandinavisk modernisme',
    'sven ivar dysthe': 'Skandinavisk modernisme',
    'dysthe, sven ivar': 'Skandinavisk modernisme',
    'torstein nilsen': 'Skandinavisk modernisme',
    'nilsen, torstein': 'Skandinavisk modernisme',
    'fredrik kayser': 'Skandinavisk modernisme',
    'kayser, fredrik': 'Skandinavisk modernisme',
    'eero saarinen': 'Skandinavisk modernisme',

    # Functionalism / Bauhaus (~1920-1940)
    'breuer, marcel': 'Funksjonalisme',
    'marcel breuer': 'Funksjonalisme',
    'mies van der rohe': 'Funksjonalisme',
    'le corbusier': 'Funksjonalisme',
    'charlotte perriand': 'Funksjonalisme',
    'perriand, charlotte': 'Funksjonalisme',
    'mart stam': 'Funksjonalisme',
    'stam, mart': 'Funksjonalisme',
    'gerrit rietveld': 'Funksjonalisme',
    'rietveld, gerrit': 'Funksjonalisme',
    'pel limited': 'Funksjonalisme',
    'pel ': 'Funksjonalisme',

    # Post-war Modernism / Mid-century Modern (~1945-1970)
    'eames, charles': 'Etterkrigsmodernisme',
    'eames, ray': 'Etterkrigsmodernisme',
    'charles eames': 'Etterkrigsmodernisme',
    'ray eames': 'Etterkrigsmodernisme',
    'race, ernest': 'Etterkrigsmodernisme',
    'ernest race': 'Etterkrigsmodernisme',
    'robin day': 'Etterkrigsmodernisme',
    'day, robin': 'Etterkrigsmodernisme',
    'harry bertoia': 'Etterkrigsmodernisme',
    'bertoia, harry': 'Etterkrigsmodernisme',
    'george nelson': 'Etterkrigsmodernisme',
    'nelson, george': 'Etterkrigsmodernisme',
    'magistretti, vico': 'Etterkrigsmodernisme',
    'vico magistretti': 'Etterkrigsmodernisme',
    'carter, ronald': 'Etterkrigsmodernisme',
    'ronald carter': 'Etterkrigsmodernisme',
    'lucian ercolani': 'Etterkrigsmodernisme',
    'ercolani, lucian': 'Etterkrigsmodernisme',
    'ercol': 'Etterkrigsmodernisme',
    'rodney kinsman': 'Etterkrigsmodernisme',
    'kinsman, rodney': 'Etterkrigsmodernisme',
    'peter murdoch': 'Etterkrigsmodernisme',
    'murdoch, peter': 'Etterkrigsmodernisme',
    'decurso, giorgio': 'Etterkrigsmodernisme',

    # Pop Art (~1960-1975)
    'aarnio, eero': 'Pop Art',
    'eero aarnio': 'Pop Art',

    # Art Nouveau / Jugend (~1890-1910)
    'charles rennie mackintosh': 'Jugend',
    'mackintosh, charles rennie': 'Jugend',
    'riemerschmid, richard': 'Jugend',
    'richard riemerschmid': 'Jugend',
    'walton, george': 'Jugend',
    'george walton': 'Jugend',
    'henry van de velde': 'Jugend',
    'van de velde, henry': 'Jugend',
    'liberty & co': 'Jugend',
    'koloman moser': 'Jugend',
    'moser, koloman': 'Jugend',
    'josef hoffmann': 'Jugend',
    'hoffmann, josef': 'Jugend',

    # Arts and Crafts (~1880-1920)
    'gimson, ernest': 'Arts and Crafts',
    'ernest gimson': 'Arts and Crafts',
    'morris & co': 'Arts and Crafts',
    'william morris': 'Arts and Crafts',
    'fry, roger': 'Arts and Crafts',
    'roger fry': 'Arts and Crafts',
    'ambrose heal': 'Arts and Crafts',
    'heal, ambrose': 'Arts and Crafts',
    'gordon russell': 'Arts and Crafts',
    'russell, gordon': 'Arts and Crafts',
    'philip webb': 'Arts and Crafts',
    'webb, philip': 'Arts and Crafts',
    'lutyens, edwin': 'Arts and Crafts',
    'edwin lutyens': 'Arts and Crafts',
    'c.f.a. voysey': 'Arts and Crafts',
    'voysey': 'Arts and Crafts',
    'ravilious, eric': 'Arts and Crafts',
    'eric ravilious': 'Arts and Crafts',

    # Aesthetic Movement / Historicism
    'godwin, edward': 'Historisme',
    'edward william godwin': 'Historisme',
    'christopher dresser': 'Historisme',
    'dresser, christopher': 'Historisme',
    'a.w. pugin': 'Historisme',
    'pugin, a.w.': 'Historisme',
    'augustus pugin': 'Historisme',

    # Postmodernism (~1975-2000)
    'starck, philippe': 'Postmodernisme',
    'philippe starck': 'Postmodernisme',
    'sottsass, ettore': 'Postmodernisme',
    'ettore sottsass': 'Postmodernisme',
    'baresel-bofinger': 'Postmodernisme',

    # Contemporary design (2000+)
    'morrison, jasper': 'Samtidsdesign',
    'jasper morrison': 'Samtidsdesign',
    'severen, maarten van': 'Samtidsdesign',
    'maarten van severen': 'Samtidsdesign',

    # Frank Lloyd Wright - spans multiple periods, use dating to disambiguate
    'wright, frank lloyd': None,  # Will use dating
    'frank lloyd wright': None,

    # Chippendale (Rococo era, ~1750-1780)
    'thomas chippendale': 'Rokokko',
    'chippendale': 'Rokokko',

    # Georgian/Neoclassical designers
    'james stuart': 'Nyklassisisme',
    'stuart, james': 'Nyklassisisme',
    'robert adam': 'Nyklassisisme',
    'adam, robert': 'Nyklassisisme',
    'linnell, john': 'Nyklassisisme',
    'john linnell': 'Nyklassisisme',

    # Regency / Empire
    'jacob-desmalter': 'Empire',

    # Roberts family (18th century British)
    'roberts family': None,  # Use dating
    'roberts, thomas': None,  # Use dating

    # Thonet (spans multiple eras)
    'thonet': None,  # Use dating

    # Wells Coates - British modernist
    'wells coates': 'Funksjonalisme',
    'coates, wells': 'Funksjonalisme',

    # Utility furniture (WWII British)
    'utility': 'Funksjonalisme',

    # Goldfinger
    'goldfinger': 'Etterkrigsmodernisme',

    # Bath Cabinet Makers
    'bath cabinet makers': None,  # Use dating
}


def parse_year_range(dating):
    """
    Parse a dating string and return (year_from, year_to).
    Returns (None, None) if unparseable.
    """
    dating = dating.strip()

    # Handle empty
    if not dating:
        return None, None

    # "1952" - single year
    m = re.match(r'^(\d{4})$', dating)
    if m:
        y = int(m.group(1))
        return y, y

    # "ca. 1732" or "c. 1790" or "circa 1800"
    m = re.match(r'^(?:ca\.?|c\.?|circa)\s*(\d{4})$', dating, re.IGNORECASE)
    if m:
        y = int(m.group(1))
        return y, y

    # "1750-1775" or "1750 - 1775"
    m = re.match(r'^(\d{4})\s*[-–]\s*(\d{4})$', dating)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "ca. 1725-1730"
    m = re.match(r'^(?:ca\.?|c\.?|circa)\s*(\d{4})\s*[-–]\s*(\d{4})$', dating, re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "ca. 1780-1800" or "ca. 1755-1770"
    m = re.match(r'^(?:ca\.?|c\.?|circa)\s*(\d{4})\s*[-–]\s*(\d{4})$', dating, re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "about 1800-1830"
    m = re.match(r'^about\s*(\d{4})\s*[-–]\s*(\d{4})$', dating, re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "Mellom 1735 og 1745"
    m = re.match(r'^[Mm]ellom\s*(\d{4})\s*og\s*(\d{4})$', dating)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "Mellom 1980 og 2013"
    m = re.match(r'^[Mm]ellom\s*(\d{4})\s*og\s*(\d{4})$', dating)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "1936-1937"
    m = re.match(r'^(\d{4})\s*[-–]\s*(\d{4})$', dating)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "1820-tallet" (the 1820s)
    m = re.match(r'^(\d{4})-tallet$', dating)
    if m:
        y = int(m.group(1))
        return y, y + 9

    # "1800-tallet" (the 1800s / 19th century)
    m = re.match(r'^(\d{3})0-tallet$', dating)
    if m:
        y = int(m.group(1)) * 10
        return y, y + 99

    # "1986 (design) / 1991 (dette eksemplar)"
    m = re.match(r'^(\d{4})\s*\(design\)', dating)
    if m:
        y = int(m.group(1))
        return y, y

    # Norwegian: "Midten av 1600-tallet" (middle of 1600s)
    m = re.match(r'^[Mm]idten\s+av\s+(\d{4})-tallet$', dating)
    if m:
        base = int(m.group(1))
        if base % 100 == 0:  # Century (1600-tallet = 1600s century)
            return base + 40, base + 60
        else:  # Decade (1930-tallet = 1930s)
            return base + 4, base + 6

    # Norwegian: "Siste halvdel av 1800-tallet" (second half of 1800s)
    m = re.match(r'^[Ss]iste\s+halvdel\s+av\s+(\d{4})-tallet$', dating)
    if m:
        base = int(m.group(1))
        if base % 100 == 0:
            return base + 50, base + 99
        else:
            return base + 5, base + 9

    # Norwegian: "Begynnelsen av 1800-tallet" (beginning of 1800s)
    m = re.match(r'^[Bb]egynnelsen\s+av\s+(\d{4})-tallet$', dating)
    if m:
        base = int(m.group(1))
        if base % 100 == 0:
            return base, base + 20
        else:
            return base, base + 3

    # Norwegian: "Slutten av 1930-tallet" (end of 1930s)
    m = re.match(r'^[Ss]lutten\s+av\s+(\d{4})-tallet$', dating)
    if m:
        base = int(m.group(1))
        if base % 100 == 0:
            return base + 80, base + 99
        else:
            return base + 7, base + 9

    # Norwegian: "F*rste halvdel av 1970-tallet" (first half of 1970s)
    m = re.match(r'^[Ff].rste\s+halvdel\s+av\s+(\d{4})-tallet$', dating)
    if m:
        base = int(m.group(1))
        if base % 100 == 0:
            return base, base + 49
        else:
            return base, base + 4

    # Norwegian: "1980- eller 1990-tallet" (1980s or 1990s)
    m = re.match(r'^(\d{4})-?\s*eller\s+(\d{4})-tallet$', dating)
    if m:
        return int(m.group(1)), int(m.group(2)) + 9

    # "late 19th century" / "early 18th century"
    m = re.match(r'^(early|late|mid)\s+(\d{1,2})(?:th|st|nd|rd)\s+century', dating, re.IGNORECASE)
    if m:
        period = m.group(1).lower()
        cent = int(m.group(2))
        base = (cent - 1) * 100
        if period == 'early':
            return base, base + 30
        elif period == 'mid':
            return base + 30, base + 70
        else:  # late
            return base + 70, base + 99

    # "late 17th century or early 18th century"
    m = re.match(r'^late\s+(\d{1,2})(?:th|st|nd|rd)\s+century\s+or\s+early\s+(\d{1,2})(?:th|st|nd|rd)\s+century', dating, re.IGNORECASE)
    if m:
        cent1 = int(m.group(1))
        cent2 = int(m.group(2))
        return (cent1 - 1) * 100 + 70, (cent2 - 1) * 100 + 30

    # "1941-48" or "1930-60" (two-digit end year)
    m = re.match(r'^(\d{4})\s*[-–]\s*(\d{2})$', dating)
    if m:
        y1 = int(m.group(1))
        y2_short = int(m.group(2))
        century = y1 // 100
        y2 = century * 100 + y2_short
        # Handle century rollover: "1990-10" means 2010
        if y2 < y1:
            y2 += 100
        return y1, y2

    # "ca. 1780- ca. 1830" (two ca. markers)
    m = re.match(r'^(?:ca\.?|c\.?)\s*(\d{4})\s*[-–]\s*(?:ca\.?|c\.?)\s*(\d{4})$', dating, re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "ca.1930-1970" (no space after ca.)
    m = re.match(r'^(?:ca\.?|c\.?)\s*(\d{4})\s*[-–]\s*(\d{4})$', dating, re.IGNORECASE)
    if m:
        return int(m.group(1)), int(m.group(2))

    # "1550 - 1590; 1830 - 1840" (multiple periods - use the later one as the relevant date)
    if ';' in dating:
        parts = dating.split(';')
        # Use the last part (most recent period)
        last_part = parts[-1].strip()
        m = re.match(r'^(\d{4})\s*[-–]\s*(\d{4})$', last_part)
        if m:
            return int(m.group(1)), int(m.group(2))

    # "designed 1950, made 1960" patterns - generic fallback
    m = re.search(r'(\d{4})', dating)
    if m:
        y = int(m.group(1))
        # Try to find a second year
        all_years = re.findall(r'(\d{4})', dating)
        if len(all_years) >= 2:
            years = [int(y) for y in all_years]
            return min(years), max(years)
        return y, y

    return None, None


def classify_by_dating_and_origin(year_from, year_to, origin, is_british, is_scandinavian,
                                   is_french, designer_lower, materials, dating_str):
    """
    Classify a chair into a style period based on dating range, origin, and context.
    Returns (style, confidence) where confidence is 0-100.
    """
    if year_from is None:
        return None, 0

    mid_year = (year_from + year_to) / 2
    span = year_to - year_from

    # Very wide date ranges (>100 years) are too ambiguous
    if span > 100:
        return None, 0

    # Very wide date ranges (80-100 years) need special handling
    if span >= 80:
        # "1500-1600" -> Renaissance
        if 1400 <= year_from <= 1530 and 1580 <= year_to <= 1620:
            return 'Renessanse', 55
        # "1550-1650" -> spans Renaissance to early Baroque
        if 1540 <= year_from <= 1570 and 1630 <= year_to <= 1660:
            return 'Renessanse', 55
        # "1600-1700" -> Baroque (for non-European handled in 60-span too)
        if 1590 <= year_from <= 1620 and 1690 <= year_to <= 1710:
            return 'Barokk', 55
        # "1700-1800" or "ca. 1700-1780" -> Rococo
        if 1690 <= year_from <= 1710 and 1770 <= year_to <= 1810:
            return 'Rokokko', 55
        # "1800-1900" or "1800-1899" -> Historisme is dominant for the 19th century
        if 1800 <= year_from <= 1810 and 1890 <= year_to <= 1910:
            return 'Historisme', 55
        # "ca. 1850-1930" -> Historisme (dominant period)
        if 1840 <= year_from <= 1860 and 1920 <= year_to <= 1940:
            return 'Historisme', 55
        # "1830-1900" -> Historisme
        if 1825 <= year_from <= 1840 and 1890 <= year_to <= 1910:
            return 'Historisme', 55
        # "1900-1950" or "1900-1962" -> hard to pin down
        if 1900 <= year_from <= 1910 and 1950 <= year_to <= 1970:
            return 'Etterkrigsmodernisme', 55
        # Otherwise too ambiguous
        return None, 0

    # Wide spans (60-80 years) - handle carefully
    if span >= 60:
        # "1500-1560" or "1500-1600" -> Renaissance
        if 1450 <= year_from <= 1560 and 1550 <= year_to <= 1620:
            return 'Renessanse', 55
        # "1550-1650" spans Renaissance to early Baroque
        if 1540 <= year_from <= 1570 and 1630 <= year_to <= 1660:
            return 'Renessanse', 55
        # "1600-1700" full century -> Baroque
        if 1590 <= year_from <= 1620 and 1690 <= year_to <= 1720:
            return 'Barokk', 55
        # "1660-1720" -> Baroque
        if 1650 <= year_from <= 1670 and 1710 <= year_to <= 1730:
            return 'Barokk', 55
        # "1700-1800" or "1700-1780" full century -> Rococo dominated
        if 1690 <= year_from <= 1710 and 1770 <= year_to <= 1810:
            return 'Rokokko', 55
        # "1730-1800" -> Rococo
        if 1720 <= year_from <= 1740 and 1790 <= year_to <= 1810:
            return 'Rokokko', 55
        # "1830-1900" -> Historisme
        if 1820 <= year_from <= 1850 and 1890 <= year_to <= 1910:
            return 'Historisme', 55
        # "1850-1920/1930" spans Historisme through Jugend - pick Historisme as dominant
        if 1840 <= year_from <= 1860 and 1910 <= year_to <= 1940:
            return 'Historisme', 55
        # "1900-1950" or "1900-1962" -> Functionalism/Modernism
        if 1895 <= year_from <= 1910 and 1940 <= year_to <= 1970:
            return 'Funksjonalisme', 55
        # "ca.1930-1970" or "1935-55" -> post-war modernism
        if 1925 <= year_from <= 1940 and 1955 <= year_to <= 1980:
            return 'Etterkrigsmodernisme', 55
        return None, 0

    # ── Renaissance (~1400-1600) ──
    if mid_year < 1610 and year_to <= 1660 and year_from >= 1350:
        return 'Renessanse', 70 if span > 50 else 80

    # ── Régence / Early Rococo transition (~1700-1730) ──
    # Régence is already used in the DB - check before Baroque
    if 1710 <= mid_year <= 1730 and is_french:
        return 'Régence', 70

    # ── Baroque (~1600-1720) ──
    if 1600 <= mid_year < 1720 and year_from >= 1580:
        if year_to <= 1740:
            return 'Barokk', 75
        return 'Barokk', 60

    # ── Rococo (~1720-1775) ──
    if 1720 <= mid_year < 1770 and year_from >= 1700:
        if is_british:
            # In Britain this overlaps with Chippendale
            if 'chippendale' in designer_lower:
                return 'Rokokko', 85
            return 'Rokokko', 70
        if year_to <= 1790:
            return 'Rokokko', 75
        return 'Rokokko', 60

    # ── Neoclassicism (~1770-1830) ──
    if 1770 <= mid_year < 1810 and year_from >= 1745:
        if is_french and mid_year < 1800:
            # Could be Louis XVI
            return 'Nyklassisisme', 70
        if is_british:
            if mid_year >= 1800:
                return 'Empire', 65  # Regency/Empire in Britain
            return 'Nyklassisisme', 70
        return 'Nyklassisisme', 70

    # ── Empire (~1800-1830) ──
    if 1800 <= mid_year < 1835 and year_from >= 1790:
        if is_french:
            return 'Empire', 80
        if is_british:
            # British Regency overlaps with Empire
            return 'Empire', 70
        if is_scandinavian:
            return 'Empire', 70
        return 'Empire', 65

    # ── Biedermeier (~1815-1848) ──
    # Mainly German/Austrian/Scandinavian
    if 1815 <= mid_year < 1850 and year_from >= 1810:
        if origin and any(x in origin.lower() for x in ['german', 'austria', 'vienna', 'munich']):
            return 'Biedermeier', 80
        if is_scandinavian:
            return 'Biedermeier', 65
        # Overlap zone - could be Empire or Historisme too
        if mid_year >= 1840:
            return 'Historisme', 60
        return 'Empire', 55

    # ── Historicism (~1840-1900) ──
    if 1840 <= mid_year < 1890 and year_from >= 1830:
        if is_british:
            return 'Historisme', 75
        return 'Historisme', 70

    # ── Art Nouveau / Jugend (~1890-1910) ──
    if 1890 <= mid_year < 1915 and year_from >= 1880:
        # This period is tricky - could be Arts & Crafts, Jugend, or late Historicism
        if is_british:
            # In Britain, Arts & Crafts is more dominant
            return 'Arts and Crafts', 55  # Lower confidence - ambiguous
        return 'Jugend', 55

    # ── Interwar period (~1920-1940) ──
    if 1920 <= mid_year < 1940 and year_from >= 1895:
        if is_scandinavian:
            if mid_year >= 1930:
                return 'Skandinavisk modernisme', 70
            return 'Funksjonalisme', 65
        return 'Funksjonalisme', 65

    # ── Wartime / transitional (~1940-1945) ──
    if 1940 <= mid_year <= 1945:
        return 'Funksjonalisme', 60

    # ── Post-war / Mid-century (~1945-1970) ──
    if 1945 < mid_year < 1970 and year_from >= 1925:
        if is_scandinavian:
            return 'Skandinavisk modernisme', 80
        return 'Etterkrigsmodernisme', 75

    # ── 1970s-1990s ──
    if 1970 <= mid_year < 2000 and year_from >= 1955:
        if mid_year < 1975:
            return 'Etterkrigsmodernisme', 60
        return 'Postmodernisme', 65

    # ── Contemporary (2000+) ──
    if mid_year >= 2000:
        return 'Samtidsdesign', 80

    return None, 0


def classify_entry(entry_id, entry):
    """
    Classify a single entry. Returns (style, confidence) or (None, 0) if skipped.
    """
    dating = entry.get('dating', '')
    designer = entry.get('designer', '')
    origin = entry.get('origin', '')
    materials = entry.get('materials', [])
    century = entry.get('century', '')
    url = entry.get('url', '')
    name = entry.get('name', '')
    keywords = entry.get('keywords', [])

    designer_lower = designer.lower() if designer else ''
    origin_lower = origin.lower() if origin else ''

    is_british = any(x in origin_lower for x in ['england', 'london', 'great britain',
                                                    'britain', 'united kingdom', 'british',
                                                    'glasgow', 'edinburgh', 'birmingham',
                                                    'manchester', 'bath'])
    is_va = 'vam.ac.uk' in url
    if is_va and not is_british and not origin:
        is_british = True  # V&A items without origin are likely British

    is_scandinavian = any(x in origin_lower for x in ['norge', 'norway', 'oslo', 'bergen',
                                                       'denmark', 'danmark', 'copenhagen',
                                                       'sweden', 'sverige', 'stockholm',
                                                       'finland', 'helsinki'])
    is_french = any(x in origin_lower for x in ['france', 'paris', 'french', 'lyon'])

    year_from, year_to = parse_year_range(dating)

    # ── Step 1: Try designer-based classification ──
    if designer_lower and designer_lower not in ('ukjent', 'unknown', 'ukjent / unknown', ''):
        for pattern, style in DESIGNER_STYLES.items():
            if pattern in designer_lower:
                if style is not None:
                    # Validate style against dating if we have years
                    return style, 90
                else:
                    # Designer known but spans multiple periods - fall through to dating
                    break

    # ── Step 2: Handle specific well-known designers that need dating context ──
    if 'wright, frank lloyd' in designer_lower or 'frank lloyd wright' in designer_lower:
        if year_from:
            if year_from < 1920:
                return 'Arts and Crafts', 80
            elif year_from < 1945:
                return 'Funksjonalisme', 80
            else:
                return 'Etterkrigsmodernisme', 75

    if 'thonet' in designer_lower:
        if year_from:
            if year_from < 1890:
                return 'Historisme', 75
            elif year_from < 1920:
                return 'Jugend', 70
            elif year_from < 1945:
                return 'Funksjonalisme', 75
            else:
                return 'Etterkrigsmodernisme', 70

    if 'roberts' in designer_lower:
        if year_from:
            if year_from < 1720:
                return 'Barokk', 75
            elif year_from < 1775:
                return 'Rokokko', 75
            else:
                return 'Nyklassisisme', 70

    # ── Step 3: Special handling for specific dating strings ──
    dating_lower = dating.lower()

    # "1900-tallet" (20th century) - too broad, skip
    if dating_lower in ('1900-tallet', '1800-tallet', '1700-tallet', '1600-tallet'):
        # Century-level dating is too broad unless we have other context
        if designer_lower and designer_lower not in ('ukjent', 'unknown', ''):
            pass  # Already tried above
        return None, 0

    # ── Step 4: Date-based classification ──
    if year_from is not None:
        style, confidence = classify_by_dating_and_origin(
            year_from, year_to, origin, is_british, is_scandinavian,
            is_french, designer_lower, materials, dating
        )
        if style and confidence >= 55:
            return style, confidence

    return None, 0


def refine_art_nouveau_arts_crafts(entry_id, entry, initial_style):
    """
    Refine ambiguous Art Nouveau / Arts and Crafts classifications.
    """
    designer = entry.get('designer', '').lower()
    origin = entry.get('origin', '').lower()
    materials = entry.get('materials', [])
    mat_lower = [m.lower() for m in materials]

    # Arts and Crafts indicators
    ac_indicators = ['oak', 'eik', 'rush', 'leather', 'elm']
    ac_designers = ['gimson', 'morris', 'heal', 'russell', 'voysey', 'webb',
                    'lutyens', 'fry', 'ravilious', 'barnsley', 'lethaby']

    # Jugend/Art Nouveau indicators
    jugend_designers = ['mackintosh', 'riemerschmid', 'walton', 'van de velde',
                        'hoffmann', 'moser', 'liberty', 'guimard', 'majorelle']

    for d in ac_designers:
        if d in designer:
            return 'Arts and Crafts'
    for d in jugend_designers:
        if d in designer:
            return 'Jugend'

    # British Arts & Crafts was more dominant in Britain
    if any(x in origin for x in ['england', 'london', 'britain', 'united kingdom']):
        if any(m in mat_lower for m in ac_indicators):
            return 'Arts and Crafts'

    return initial_style


def main():
    with open('_gap_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    missing = {k: v for k, v in data.items()
               if (not v.get('style')) and v.get('dating')}

    results = {}
    skipped = 0
    classified = 0
    style_counts = {}

    for entry_id, entry in missing.items():
        style, confidence = classify_entry(entry_id, entry)

        if style and confidence >= 55:
            # Additional refinement for ambiguous periods
            if style in ('Arts and Crafts', 'Jugend'):
                style = refine_art_nouveau_arts_crafts(entry_id, entry, style)

            results[entry_id] = style
            classified += 1
            style_counts[style] = style_counts.get(style, 0) + 1
        else:
            skipped += 1

    # Write results
    with open('_style_enrichment.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Total missing style with dating: {len(missing)}")
    print(f"Classified: {classified}")
    print(f"Skipped (low confidence): {skipped}")
    print(f"\nStyle distribution:")
    for s, c in sorted(style_counts.items(), key=lambda x: -x[1]):
        print(f"  {c:4d}  {s}")


if __name__ == '__main__':
    main()
