#!/usr/bin/env python3
"""Surveille le stock iPhone Duo (retrait en Apple Store, Île-de-France)
et envoie une notification push (ntfy.sh) dès qu'un magasin l'a en stock.

Usage :
  python3 check_stock.py                    # une vérification
  python3 check_stock.py --watch 180        # re-vérifie toutes les 180 s
  python3 check_stock.py --watch 180 --duration 20700   # boucle ~5h45 puis s'arrête

Aucune dépendance : bibliothèque standard uniquement.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request

# Références France (apple.com/fr) surveillées : "REF=Libellé"
DEFAULT_PARTS = "MK2D4F/A=Blanc stellaire 256 Go,MK2E4F/A=Ciel nocturne 256 Go"
PARTS = dict(
    p.split("=", 1) if "=" in p else (p, p)
    for p in os.environ.get("APPLE_PARTS", DEFAULT_PARTS).split(",") if p.strip()
)
# 75001 renvoie les 9 Apple Store d'Île-de-France ; 77127 / 78000 en secours
LOCATIONS = os.environ.get("APPLE_LOCATIONS", "75001,77127,78000").split(",")
IDF_PREFIXES = ("75", "77", "78", "91", "92", "93", "94", "95")
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
STATE_FILE = os.environ.get("STATE_FILE", ".duo-state.json")
BUY_URL = "https://www.apple.com/fr/shop/buy-iphone/iphone-duo"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def fetch(location):
    q = [("pl", "true")] + [(f"parts.{i}", p) for i, p in enumerate(PARTS)] + [("location", location)]
    url = "https://www.apple.com/fr/shop/retail/pickup-message?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def parse(data):
    """-> {(storeNumber, part): (storeName, available, quote)}"""
    out = {}
    for s in data.get("body", {}).get("stores", []):
        zipcode = str(s.get("address", {}).get("postalCode", ""))
        if zipcode and not zipcode.startswith(IDF_PREFIXES):
            continue
        for part in PARTS:
            info = s.get("partsAvailability", {}).get(part, {})
            display = info.get("pickupDisplay", "")
            quote = info.get("pickupSearchQuote") or info.get("storePickupQuote") or display or "?"
            out[(s["storeNumber"], part)] = (s["storeName"], display == "available", quote)
    return out


def check():
    results = {}
    for loc in LOCATIONS:
        try:
            results.update(parse(fetch(loc)))
        except Exception as e:
            print(f"[warn] {loc}: {e}", file=sys.stderr)
        if len({k[0] for k in results}) >= 9:
            break
    return results


def notify(title, body):
    if not NTFY_TOPIC:
        return
    headers = {"Title": title.encode("utf-8"), "Priority": "5",
               "Tags": "iphone,white_check_mark", "Click": BUY_URL}
    req = urllib.request.Request("https://ntfy.sh/" + NTFY_TOPIC, data=body.encode(), headers=headers)
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"[warn] ntfy: {e}", file=sys.stderr)


def load_state():
    try:
        with open(STATE_FILE) as f:
            return {tuple(x) for x in json.load(f) if isinstance(x, list)}
    except Exception:
        return set()


def save_state(available):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(list(k) for k in available), f)


def run_once():
    results = check()
    stamp = time.strftime("%H:%M:%S", time.gmtime())
    if not results:
        print(f"[{stamp} UTC] Aucune réponse d'apple.com (bloqué ou endpoint changé).")
        return 2
    available = {k for k, (_, ok, _) in results.items() if ok}
    new = available - load_state()
    print(f"[{stamp} UTC] {len({k[0] for k in results})} magasins vérifiés")
    for part, label in PARTS.items():
        print(f"  {label} ({part})")
        rows = sorted((v for k, v in results.items() if k[1] == part), key=lambda v: v[0])
        for name, ok, quote in rows:
            print(f"    {'✅' if ok else '—'} {name:<26} {quote}")
    for part, label in PARTS.items():
        stores = sorted(results[k][0] for k in new if k[1] == part)
        if stores:
            notify(f"iPhone Duo {label} disponible !", "En stock : " + ", ".join(stores))
            print(f"  🔔 Notification : {label} → {', '.join(stores)}")
    save_state(available)
    return 0 if available else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", type=int, metavar="SECONDES", help="re-vérifie en boucle")
    ap.add_argument("--duration", type=int, metavar="SECONDES", help="durée max de la boucle")
    a = ap.parse_args()
    if not a.watch:
        sys.exit(run_once())
    end = time.time() + a.duration if a.duration else None
    while True:
        run_once()
        sys.stdout.flush()
        if end and time.time() + a.watch > end:
            break
        time.sleep(max(60, a.watch))
