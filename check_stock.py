#!/usr/bin/env python3
"""Surveille le stock iPhone Duo (retrait en Apple Store, Île-de-France)
et envoie une notification push (ntfy.sh) dès qu'un magasin l'a en stock.

Usage :
  python3 check_stock.py                 # une vérification
  python3 check_stock.py --watch 120     # re-vérifie toutes les 120 s
  NTFY_TOPIC=mon-topic python3 check_stock.py --watch 120

Aucune dépendance : bibliothèque standard uniquement.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request

# iPhone Duo, Blanc stellaire, 256 Go — référence France (apple.com/fr)
PART = os.environ.get("APPLE_PART", "MK2D4F/A")
# 75001 renvoie les 9 Apple Store d'Île-de-France ; 77127 / 78000 en secours
LOCATIONS = os.environ.get("APPLE_LOCATIONS", "75001,77127,78000").split(",")
IDF_PREFIXES = ("75", "77", "78", "91", "92", "93", "94", "95")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")  # ex. "duo-philippe-8f3a"
STATE_FILE = os.environ.get("STATE_FILE", ".duo-state.json")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def fetch(location):
    url = ("https://www.apple.com/fr/shop/retail/pickup-message?pl=true&parts.0="
           + urllib.parse.quote(PART, safe="") + "&location=" + urllib.parse.quote(location))
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def parse(data):
    """-> {storeNumber: (storeName, available: bool, quote)}"""
    out = {}
    for s in data.get("body", {}).get("stores", []):
        zipcode = str(s.get("address", {}).get("postalCode", ""))
        if zipcode and not zipcode.startswith(IDF_PREFIXES):
            continue
        part = s.get("partsAvailability", {}).get(PART, {})
        display = part.get("pickupDisplay", "")
        quote = part.get("pickupSearchQuote") or part.get("storePickupQuote") or display
        out[s["storeNumber"]] = (s["storeName"], display == "available", quote)
    return out


def check():
    stores = {}
    for loc in LOCATIONS:
        try:
            stores.update(parse(fetch(loc)))
        except Exception as e:
            print(f"[warn] {loc}: {e}", file=sys.stderr)
        if len(stores) >= 9:
            break
    return stores


def notify(title, body, url=None):
    if not NTFY_TOPIC:
        return
    headers = {"Title": title.encode("latin-1", "ignore"), "Priority": "5", "Tags": "iphone,white_check_mark"}
    if url:
        headers["Click"] = url
    req = urllib.request.Request("https://ntfy.sh/" + NTFY_TOPIC, data=body.encode(), headers=headers)
    urllib.request.urlopen(req, timeout=15)


def load_state():
    try:
        with open(STATE_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_state(available):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(available), f)


def run_once():
    stores = check()
    if not stores:
        print("Aucune réponse d'apple.com (bloqué ou endpoint changé).")
        return 2
    available = {n for n, (_, ok, _) in stores.items() if ok}
    previously = load_state()
    new = available - previously
    for n, (name, ok, quote) in sorted(stores.items(), key=lambda kv: kv[1][0]):
        print(f"{'✅' if ok else '—'} {name:<28} {quote}")
    if new:
        names = ", ".join(stores[n][0] for n in sorted(new))
        notify("iPhone Duo Blanc 256 Go disponible !", f"En stock : {names}",
               "https://www.apple.com/fr/shop/buy-iphone/iphone-duo")
        print(f"\n🔔 Notification envoyée : {names}")
    save_state(available)
    return 0 if available else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", type=int, metavar="SECONDES", help="re-vérifie en boucle")
    a = ap.parse_args()
    if not a.watch:
        sys.exit(run_once())
    while True:
        run_once()
        time.sleep(max(60, a.watch))
