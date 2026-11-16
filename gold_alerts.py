"""Alertes Telegram : annonces USD à fort impact (qui font bouger l'or).

Modes :
  alert -> prévient 30 à 45 min avant chaque annonce (lancé toutes les 15 min)
  daily -> résumé des annonces du jour
  test  -> message de test
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send(text):
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data
    )
    urllib.request.urlopen(req, timeout=20).read()


def load_events():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = json.load(r)
    events = []
    for e in raw:
        if e.get("country") != "USD" or e.get("impact") != "High":
            continue
        try:
            t = datetime.fromisoformat(e["date"]).astimezone(timezone.utc)
        except Exception:
            continue
        events.append((t, e))
    return sorted(events, key=lambda x: x[0])


def fmt(t, e):
    return (
        f"{t:%H:%M} UTC | {e.get('title', '?')}\n"
        f"   Prévu: {e.get('forecast') or '-'} | Précédent: {e.get('previous') or '-'}"
    )


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "alert"

    if not TOKEN or not CHAT_ID:
        print("TELEGRAM_TOKEN ou TELEGRAM_CHAT_ID manquant")
        sys.exit(1)

    if mode == "test":
        send("✅ Test OK : ton bot d'alertes Gold fonctionne.")
        return

    try:
        events = load_events()
    except Exception as ex:
        print(f"Erreur de récupération du calendrier : {ex}")
        return

    now = datetime.now(timezone.utc)

    if mode == "daily":
        today = [(t, e) for t, e in events if t.date() == now.date()]
        if not today:
            send("📅 Aucune annonce USD à fort impact aujourd'hui.")
        else:
            lines = "\n".join(fmt(t, e) for t, e in today)
            send(f"📅 Annonces USD à fort impact aujourd'hui (XAUUSD) :\n\n{lines}")
        return

    for t, e in events:
        mins = (t - now).total_seconds() / 60
        if 30 < mins <= 45:
            send(f"⚠️ Annonce USD dans ~{int(mins)} min (impact élevé)\n\n{fmt(t, e)}")


if __name__ == "__main__":
    main()
