#!/usr/bin/env python3
"""Generate an UNPUBLISHED Greek-language article draft via the OpenAI API."""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

topic = os.environ.get("ARTICLE_TOPIC", "").strip()
key = os.environ.get("OPENAI_API_KEY", "")
model = os.environ.get("ARTICLE_MODEL", "gpt-4.1-mini")
if not topic or not key:
    sys.exit("ARTICLE_TOPIC and OPENAI_API_KEY are required")
if len(topic) > 180:
    sys.exit("Topic too long")

instructions = """Είσαι βοηθός σύνταξης προσχεδίων για επιστημονικά υπεύθυνο λογοθεραπευτή.
Γράψε στα ελληνικά ένα κατανοητό, προσεκτικό άρθρο για το memoryandspeech.com.
Απευθύνεται σε ανθρώπους που αναζητούν πληροφορίες για υπηρεσίες λογοθεραπείας.
Μη δίνεις διάγνωση, εξατομικευμένη ιατρική συμβουλή ή εγγυήσεις αποτελέσματος.
Μην επινοείς μελέτες, DOI, συγγραφείς ή παραπομπές. Αν δεν μπορείς να επαληθεύσεις
πηγή, πρόσθεσε την ένδειξη [ΑΠΑΙΤΕΙΤΑΙ ΕΠΑΛΗΘΕΥΣΗ ΠΗΓΗΣ] αντί βιβλιογραφίας.
Μην ισχυρίζεσαι ότι έγινε έρευνα σε πραγματικό χρόνο.
Δώσε Markdown με: τίτλο, προτεινόμενο SEO title, meta description (έως 155 χαρακτήρες),
κύριο άρθρο με σαφείς ενότητες, ενότητα 'Επιστημονικός έλεγχος πριν τη δημοσίευση',
και ουδέτερη προτροπή επικοινωνίας με το κέντρο.
Να αποφεύγεις την υπερβολική επανάληψη της περιοχής Νέα Μάκρη και τη διαφημιστική υπερβολή.
ΠΡΟΣΧΕΔΙΟ — ΟΧΙ ΓΙΑ ΔΗΜΟΣΙΕΥΣΗ."""

payload = {
    "model": model,
    "instructions": instructions,
    "input": "Θέμα άρθρου: " + topic,
    "max_output_tokens": 2200,
}
request = urllib.request.Request(
    "https://api.openai.com/v1/responses",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=90) as response:
        result = json.load(response)
except urllib.error.HTTPError as exc:
    sys.exit(f"OpenAI API HTTP {exc.code}: check key, credits, and model access")

parts = []
for item in result.get("output", []):
    if item.get("type") == "message":
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(content.get("text", ""))
article = "\n".join(parts).strip()
if not article:
    sys.exit("No article text returned; nothing written")

slug = re.sub(r"[^a-z0-9-]+", "-", topic.lower()).strip("-")[:48]
if not slug:
    slug = "greek-article"
stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
path = Path("article-drafts") / f"{stamp}-{slug}.md"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
    "> **ΠΡΟΣΧΕΔΙΟ — ΑΠΑΙΤΕΙΤΑΙ ΕΠΙΣΤΗΜΟΝΙΚΗ ΕΓΚΡΙΣΗ. ΔΕΝ ΕΧΟΥΝ ΕΠΑΛΗΘΕΥΤΕΙ ΠΗΓΕΣ.**\n\n"
    + article + "\n", encoding="utf-8"
)
print(path)
with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
    out.write(f"draft_path={path}\n")
