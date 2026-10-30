"""Aggregate-only monthly report; no patient data and no invented zeroes."""
import calendar
import datetime as dt
import json
import os
from pathlib import Path

today = dt.date.today()
last = today.replace(day=1) - dt.timedelta(days=1)
first = last.replace(day=1)
period = first.strftime("%Y-%m")
lines = [f"# Μηνιαία αναφορά marketing — {period}", "",
         "Στόχος: τουλάχιστον 4 νέα περιστατικά τον μήνα.", "",
         "## Πραγματικές επικοινωνίες και περιστατικά", "",
         "| Δείκτης | Τιμή |", "|---|---:|"]
values = {}
for key, label in (("MONTHLY_CALLS", "Τηλεφωνικές επικοινωνίες"),
                   ("MONTHLY_APPOINTMENTS", "Ραντεβού αξιολόγησης"),
                   ("MONTHLY_NEW_PATIENTS", "Νέα περιστατικά")):
    raw = os.environ.get(key, "").strip()
    if raw:
        if not raw.isdecimal():
            raise ValueError(f"{key} must be a non-negative integer or empty")
        values[key] = int(raw)
    lines.append(f"| {label} | {values.get(key, 'Δεν καταχωρίστηκε')} |")
lines += ["", "Οι μετρήσεις επικοινωνιών καταχωρίζονται χειροκίνητα ως συνολικά πλήθη, όχι ως προσωπικά δεδομένα.", "",
          "## Google Search Console — οργανική αναζήτηση", ""]
secret = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
site = os.environ.get("GSC_SITE_URL", "").strip()
if not secret or not site:
    lines += ["Δεν έχει συνδεθεί το Google Search Console. Απαιτούνται το secret GSC_SERVICE_ACCOUNT_JSON και η μεταβλητή GSC_SITE_URL.", ""]
else:
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        info = json.loads(secret)
        creds = service_account.Credentials.from_service_account_info(
            info, scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
        session = AuthorizedSession(creds)
        url = "https://www.googleapis.com/webmasters/v3/sites/" + __import__("urllib.parse", fromlist=["quote"]).quote(site, safe="") + "/searchAnalytics/query"
        response = session.post(url, json={"startDate": first.isoformat(), "endDate": last.isoformat(), "rowLimit": 1}, timeout=30)
        response.raise_for_status()
        data = response.json()
        rows = data.get("rows", [])
        if rows:
            r = rows[0]
            lines += [f"- Κλικ από οργανική αναζήτηση: **{r.get('clicks', 'Μ/Δ')}**",
                      f"- Εμφανίσεις: **{r.get('impressions', 'Μ/Δ')}**",
                      f"- CTR: **{100*r.get('ctr', 0):.2f}%**",
                      f"- Μέση θέση: **{r.get('position', 'Μ/Δ')}**", ""]
        else:
            lines += ["Δεν επιστράφηκαν δεδομένα για την περίοδο (δεν σημαίνει απαραίτητα μηδενική επισκεψιμότητα).", ""]
    except Exception as exc:
        lines += [f"Η ανάκτηση δεδομένων GSC απέτυχε: {type(exc).__name__}. Ελέγξτε εξουσιοδότηση, site URL και το Actions log.", ""]
n = values.get("MONTHLY_NEW_PATIENTS")
lines += ["## Αξιολόγηση στόχου", "",
          ("Στόχος επιτεύχθηκε." if n >= 4 else "Κάτω από τον στόχο: χρειάζεται διερεύνηση.") if n is not None else "Δεν μπορεί να αξιολογηθεί χωρίς πλήθος νέων περιστατικών.",
          "", "Σημείωση: Τα clicks δεν ταυτίζονται με τηλεφωνήματα ή νέα περιστατικά. Δεν υπάρχει αυτόματη καταγραφή κλήσεων ή ραντεβού.", ""]
Path("marketing-report.md").write_text("\n".join(lines), encoding="utf-8")
print("Report created for", period, "(aggregate data only)")
