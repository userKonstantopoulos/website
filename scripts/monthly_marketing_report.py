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
baseline_file = Path("marketing-measurement/monthly-counts.json")
baseline = json.loads(baseline_file.read_text(encoding="utf-8")).get(period, {}) if baseline_file.exists() else {}
values = {}
for key, label in (("MONTHLY_CALLS", "Τηλεφωνικές επικοινωνίες"),
                   ("MONTHLY_APPOINTMENTS", "Ραντεβού αξιολόγησης"),
                   ("MONTHLY_NEW_PATIENTS", "Νέα περιστατικά")):
    raw = os.environ.get(key, "").strip()
    if raw:
        if not raw.isdecimal():
            raise ValueError(f"{key} must be a non-negative integer or empty")
        values[key] = int(raw)
    if key not in values and key in baseline:
        values[key] = baseline[key]
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
        import requests
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            reason = f"HTTP {exc.response.status_code}"
        else:
            reason = type(exc).__name__
        lines += [f"Η ανάκτηση δεδομένων GSC απέτυχε: {reason}. Ελέγξτε δικαιώματα ιδιοκτησίας και API.", ""]
# GA4 Data API: aggregate events only, never patient information.
lines += ["## Google Analytics 4 — ενέργειες επικοινωνίας", ""]
ga4_property = os.environ.get("GA4_PROPERTY_ID", "").strip()
ga4_secret = os.environ.get("GA4_SERVICE_ACCOUNT_JSON", "").strip() or secret
if not ga4_property or not ga4_secret:
    lines += ["Δεν έχει συνδεθεί το GA4 Data API (GA4_PROPERTY_ID και διαπιστευτήρια ανάγνωσης).", ""]
elif not ga4_property.isdecimal():
    lines += ["Μη έγκυρο GA4_PROPERTY_ID: απαιτείται αριθμητικό property ID, όχι Measurement ID G-...", ""]
else:
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        try:
            credential_info = json.loads(ga4_secret)
        except json.JSONDecodeError:
            raise ValueError("GA4 secret is not valid JSON; check the full file was pasted into the GitHub secret") from None
        if credential_info.get("type") != "service_account" or not credential_info.get("private_key"):
            raise ValueError("GA4 secret is not a complete Google service-account JSON key")
        credentials = service_account.Credentials.from_service_account_info(
            credential_info,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"])
        session = AuthorizedSession(credentials)
        response = session.post(
            "https://analyticsdata.googleapis.com/v1beta/properties/" + ga4_property + ":runReport",
            json={
                "dateRanges": [{"startDate": first.isoformat(), "endDate": last.isoformat()}],
                "dimensions": [{"name": "eventName"}, {"name": "customEvent:contact_channel"}],
                "metrics": [{"name": "eventCount"}],
                "dimensionFilter": {"filter": {"fieldName": "eventName", "inListFilter": {
                    "values": ["contact_click", "contact_page_click", "contact_form_success"]}}},
                "limit": 100
            }, timeout=30)
        # If custom dimension is not registered in GA4, retry with event name alone.
        if response.status_code == 400:
            response = session.post(
                "https://analyticsdata.googleapis.com/v1beta/properties/" + ga4_property + ":runReport",
                json={
                    "dateRanges": [{"startDate": first.isoformat(), "endDate": last.isoformat()}],
                    "dimensions": [{"name": "eventName"}],
                    "metrics": [{"name": "eventCount"}],
                    "dimensionFilter": {"filter": {"fieldName": "eventName", "inListFilter": {
                        "values": ["contact_click", "contact_page_click", "contact_form_success"]}}},
                    "limit": 100
                }, timeout=30)
        response.raise_for_status()
        rows = response.json().get("rows", [])
        counts = {}
        for row in rows:
            dims = [v.get("value", "") for v in row.get("dimensionValues", [])]
            name = dims[0] if dims else ""
            channel = dims[1] if len(dims) > 1 else "χωρίς ανάλυση καναλιού"
            count = int(row["metricValues"][0]["value"])
            counts[(name, channel)] = counts.get((name, channel), 0) + count
        if counts:
            lines += ["| Συμβάν | Κανάλι | Πλήθος |", "|---|---|---:|"]
            for (name, channel), count in sorted(counts.items()):
                lines.append(f"| {name} | {channel} | {count} |")
            lines.append("")
        else:
            lines += ["Δεν καταγράφηκαν αντίστοιχα συμβάντα στην περίοδο ή δεν είναι ακόμη διαθέσιμα.", ""]
    except Exception as exc:
        import requests
        if isinstance(exc, ValueError):
            reason = str(exc) if type(exc) is ValueError else type(exc).__name__
        elif isinstance(exc, requests.HTTPError):
            reason = f"HTTP {exc.response.status_code} from GA4 API"
        else:
            reason = type(exc).__name__
        lines += [f"Αποτυχία ανάκτησης GA4: {reason}. Δεν καταγράφονται μυστικά διαπιστευτήρια.", ""]
lines += ["Τα συμβάντα GA4 μετρούν ενέργειες επισκεπτών που αποδέχθηκαν τα cookies, όχι επιβεβαιωμένες κλήσεις ή νέους ασθενείς.", ""]

n = values.get("MONTHLY_NEW_PATIENTS")
lines += ["## Αξιολόγηση στόχου", "",
          ("Στόχος επιτεύχθηκε." if n >= 4 else "Κάτω από τον στόχο: χρειάζεται διερεύνηση.") if n is not None else "Δεν μπορεί να αξιολογηθεί χωρίς πλήθος νέων περιστατικών.",
          "", "Σημείωση: Τα clicks δεν ταυτίζονται με τηλεφωνήματα ή νέα περιστατικά. Δεν υπάρχει αυτόματη καταγραφή κλήσεων ή ραντεβού.", ""]
Path("marketing-report.md").write_text("\n".join(lines), encoding="utf-8")
print("Report created for", period, "(aggregate data only)")
