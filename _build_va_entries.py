import json

# All V&A entries collected from Notion fetches
entries = [
    {"objekt_id": "O133081", "vam_url": "https://collections.vam.ac.uk/item/O133081/", "title": "Chair One"},
    {"objekt_id": "O121083", "vam_url": "https://collections.vam.ac.uk/item/O121083/", "title": "Selene Chair"},
    {"objekt_id": "O1227489", "vam_url": "https://collections.vam.ac.uk/item/O1227489/", "title": "Cabbage Chair"},
    {"objekt_id": "O115748", "vam_url": "https://collections.vam.ac.uk/item/O115748/", "title": "Knotted Chair"},
    {"objekt_id": "O122530", "vam_url": "https://collections.vam.ac.uk/item/O122530/", "title": "Crosby chair"},
    {"objekt_id": "O372071", "vam_url": "https://collections.vam.ac.uk/item/O372071/", "title": "Bofinger chair"},
    {"objekt_id": "O168294", "vam_url": "https://collections.vam.ac.uk/item/O168294/", "title": "Womb Chair"},
    {"objekt_id": "O121005", "vam_url": "https://collections.vam.ac.uk/item/O121005/", "title": "LCM Chair"},
    {"objekt_id": "O121019", "vam_url": "https://collections.vam.ac.uk/item/O121019/", "title": "Diamond Chair"},
    {"objekt_id": "O63050", "vam_url": "https://collections.vam.ac.uk/item/O63050/", "title": "S Chair"},
    {"objekt_id": "O1153451", "vam_url": "https://collections.vam.ac.uk/item/O1153451/", "title": "Berlage chair"},
    {"objekt_id": "O1224753", "vam_url": "https://collections.vam.ac.uk/item/O1224753/", "title": "Palace chair"},
]

# Save
with open("va_entries.json", "w", encoding="utf-8") as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)
print(f"Wrote {len(entries)} entries to va_entries.json")
