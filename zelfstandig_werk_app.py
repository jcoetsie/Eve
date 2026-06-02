#!/usr/bin/env python3
"""
Eve's Zelfstandig Werk Generator - VBS Aaigem
Stap-voor-stap tool voor leerkrachten.

Bouw als Windows .exe:
  pip install pyinstaller
  pyinstaller --onefile --windowed --name "Eve's Zelfstandig Werk" zelfstandig_werk_app.py
"""

import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext, colorchooser
import json
import os
import sys
import threading
import webbrowser
from datetime import date
from urllib.request import urlopen, Request
from urllib.error import URLError

# ============================================================
# VERSIE
# ============================================================
VERSIE = "1.2.0"
GITHUB_REPO = "jcoetsie/Eve"

# ============================================================
# APP KLEUREN (UI van de app zelf - vast)
# ============================================================
GROEN = "#AACD55"
GROEN_DONKER = "#8AB535"
BLAUW = "#27A9E1"
BLAUW_DONKER = "#1E8CBF"
WIT = "#FFFFFF"
LICHTGRIJS = "#F5F5F5"
GRIJS = "#E0E0E0"
DONKERGRIJS = "#666666"
ZWART = "#333333"

# ============================================================
# STANDAARD SCHOOLKLEUREN (instelbaar door gebruiker)
# ============================================================
STANDAARD_INSTELLINGEN = {
    "schoolnaam": "VBS Aaigem",
    "hoofdkleur": "#AACD55",      # Groen - headers, knoppen
    "accentkleur": "#27A9E1",     # Blauw - titelbalk, namen, score
    "layout": "bovenaan",         # "bovenaan" = leerlingen als kolommen, "links" = als rijen
}

def _donkerder(hex_kleur, factor=0.8):
    """Maak een hex kleur donkerder."""
    hex_kleur = hex_kleur.lstrip("#")
    r, g, b = int(hex_kleur[0:2], 16), int(hex_kleur[2:4], 16), int(hex_kleur[4:6], 16)
    r, g, b = int(r * factor), int(g * factor), int(b * factor)
    return f"#{r:02x}{g:02x}{b:02x}"

def _lichter(hex_kleur, factor=0.3):
    """Maak een lichte tint van een kleur (mix met wit)."""
    hex_kleur = hex_kleur.lstrip("#")
    r, g, b = int(hex_kleur[0:2], 16), int(hex_kleur[2:4], 16), int(hex_kleur[4:6], 16)
    r = int(r + (255 - r) * (1 - factor))
    g = int(g + (255 - g) * (1 - factor))
    b = int(b + (255 - b) * (1 - factor))
    return f"#{r:02x}{g:02x}{b:02x}"

# Pad voor opgeslagen data (in de Documenten-map van de gebruiker)
def _data_map():
    thuis = os.path.expanduser("~")
    # Maak een nette map aan in Documenten
    documenten = os.path.join(thuis, "Documents", "Eve's Zelfstandig Werk")
    os.makedirs(documenten, exist_ok=True)
    return documenten

def _data_pad():
    return os.path.join(_data_map(), "klassen_en_leerlingen.json")


# ============================================================
# DATA OPSLAG + MIGRATIE
# ============================================================
DATA_SCHEMA_VERSIE = 2  # Verhoog bij schema-wijzigingen

def _migreer_data(data):
    """Migreer oude data-formaten naar het huidige schema."""
    schema = data.get("_schema", 0)

    if schema < 1:
        # v0 -> v1: oud formaat met "klassen"/{} en "opdrachten"/{} op toplevel
        if "klassen" in data and "schooljaren" not in data:
            oude_klassen = data.pop("klassen", {})
            oude_opdrachten = data.pop("opdrachten", {})
            data["schooljaren"] = {}
            if oude_klassen:
                # Zet alles onder een standaard schooljaar
                vandaag = date.today()
                start = vandaag.year if vandaag.month >= 9 else vandaag.year - 1
                jaar = f"{start}-{start + 1}"
                klassen_nieuw = {}
                for naam, leerlingen in oude_klassen.items():
                    klassen_nieuw[naam] = {
                        "leerlingen": leerlingen if isinstance(leerlingen, list) else [],
                        "opdrachten": oude_opdrachten.get(naam, []),
                    }
                data["schooljaren"][jaar] = {"klassen": klassen_nieuw}

    if schema < 2:
        # v1 -> v2: instellingen toevoegen
        if "instellingen" not in data:
            data["instellingen"] = dict(STANDAARD_INSTELLINGEN)
        # Zorg dat alle standaard-keys bestaan
        for key, val in STANDAARD_INSTELLINGEN.items():
            if key not in data["instellingen"]:
                data["instellingen"][key] = val

    # Zorg dat toplevel keys bestaan
    data.setdefault("schooljaren", {})
    data.setdefault("instellingen", dict(STANDAARD_INSTELLINGEN))
    data["_schema"] = DATA_SCHEMA_VERSIE
    return data


def laad_data():
    pad = _data_pad()
    if os.path.exists(pad):
        try:
            with open(pad, "r", encoding="utf-8") as f:
                data = json.load(f)
            data = _migreer_data(data)
            bewaar_data(data)  # Sla gemigreerde versie op
            return data
        except Exception:
            pass
    return _migreer_data({})


def bewaar_data(data):
    pad = _data_pad()
    data["_schema"] = DATA_SCHEMA_VERSIE
    with open(pad, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# HTML GENERATOR - Smartboard Touch (geen macro's nodig!)
# ============================================================
def genereer_smartboard(leerlingen, opdracht_naam, taken, bestandspad,
                         hoofdkleur="#AACD55", accentkleur="#27A9E1",
                         schoolnaam="VBS Aaigem", layout="bovenaan"):
    """Genereer een HTML-bestand voor het smartboard.

    Touch op een vakje = vinkje aan/uit. Werkt in elke browser.
    layout: "bovenaan" = leerlingen als kolommen (standaard), "links" = leerlingen als rijen
    """
    import html as html_mod

    n_taken = len(taken)
    n_ll = len(leerlingen)
    naam_esc = html_mod.escape(opdracht_naam)
    school_esc = html_mod.escape(schoolnaam)

    # Afgeleide kleuren
    hoofd_donker = _donkerder(hoofdkleur)
    accent_donker = _donkerder(accentkleur)
    hoofd_licht = _lichter(hoofdkleur, 0.25)
    hoofd_xlicht = _lichter(hoofdkleur, 0.15)
    hoofd_licht2 = _lichter(hoofdkleur, 0.35)
    hoofd_xlicht2 = _lichter(hoofdkleur, 0.20)
    accent_licht = _lichter(accentkleur, 0.20)
    hoofd_done = _lichter(hoofdkleur, 0.45)
    hoofd_done2 = _lichter(hoofdkleur, 0.50)

    # Bouw tabel HTML afhankelijk van layout
    if layout == "bovenaan":
        # Leerlingen als KOLOMMEN (bovenaan), taken als RIJEN (links)
        header_html = "      <th>Taak</th>\n"
        for i, naam in enumerate(leerlingen):
            even = "even" if i % 2 == 0 else "odd"
            header_html += f'      <th class="naam-kol {even}">{html_mod.escape(naam)}</th>\n'
        header_html += "      <th>Klaar</th>\n"

        rijen_html = ""
        for j, taak in enumerate(taken):
            cellen = ""
            for i in range(n_ll):
                even = "even" if i % 2 == 0 else "odd"
                cellen += f'      <td class="cel {even}" onclick="toggle(this)" id="c{i}_{j}"></td>\n'
            # "Klaar" kolom: hoeveel leerlingen hebben deze taak af
            rijen_html += f"""    <tr>
      <td class="taak-naam">{html_mod.escape(taak)}</td>
{cellen}      <td class="klaar" id="klaar{j}">0/{n_ll}</td>
    </tr>
"""
        # Score-rij onderaan: per leerling
        score_cellen = ""
        for i in range(n_ll):
            even = "even" if i % 2 == 0 else "odd"
            score_cellen += f'      <td class="score {even}" id="score{i}">0/{n_taken}</td>\n'
        rijen_html += f"""    <tr class="score-rij">
      <td class="score-label">Score</td>
{score_cellen}      <td></td>
    </tr>
"""
    else:
        # Leerlingen als RIJEN (links), taken als KOLOMMEN (bovenaan)
        header_html = "      <th>Leerling</th>\n"
        for taak in taken:
            header_html += f"      <th>{html_mod.escape(taak)}</th>\n"
        header_html += "      <th>Score</th>\n"

        rijen_html = ""
        for i, naam in enumerate(leerlingen):
            even = "even" if i % 2 == 0 else "odd"
            cellen = ""
            for j in range(n_taken):
                cellen += f'      <td class="cel {even}" onclick="toggle(this)" id="c{i}_{j}"></td>\n'
            rijen_html += f"""    <tr class="{even}">
      <td class="naam">{html_mod.escape(naam)}</td>
{cellen}      <td class="score" id="score{i}">0/{n_taken}</td>
    </tr>
"""

    pagina = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{naam_esc} - {school_esc}</title>
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Roboto', 'Segoe UI', sans-serif;
    background: #f8f8f8;
    -webkit-user-select: none;
    user-select: none;
    touch-action: manipulation;
  }}

  .header {{
    background: {accentkleur};
    color: white;
    text-align: center;
    padding: 18px 20px 10px;
  }}
  .header h1 {{ font-size: 28px; margin-bottom: 4px; }}
  .header p {{ font-size: 16px; opacity: 0.85; }}

  .subheader {{
    background: {hoofdkleur};
    color: white;
    text-align: center;
    padding: 8px;
    font-size: 15px;
    font-weight: bold;
  }}

  .instructie {{
    text-align: center;
    color: #888;
    font-style: italic;
    padding: 10px;
    font-size: 15px;
  }}

  .tabel-container {{
    overflow-x: auto;
    padding: 0 10px 20px;
  }}

  table {{
    border-collapse: collapse;
    width: 100%;
    min-width: 600px;
  }}

  th {{
    background: {hoofdkleur};
    color: white;
    font-weight: bold;
    font-size: 13px;
    padding: 12px 8px;
    border: 2px solid {hoofd_donker};
    text-align: center;
    min-width: 90px;
  }}
  th:first-child {{
    min-width: 160px;
    font-size: 15px;
    background: {hoofd_donker};
  }}
  th:last-child {{
    min-width: 70px;
    background: {accentkleur};
    border-color: {accent_donker};
  }}

  td {{
    border: 2px solid #ccc;
    text-align: center;
    vertical-align: middle;
  }}

  td.naam {{
    font-weight: bold;
    font-size: 16px;
    color: {accentkleur};
    text-align: left;
    padding: 0 12px;
    background: {hoofd_licht};
    white-space: nowrap;
  }}
  tr.odd td.naam {{ background: {hoofd_licht2}; }}

  td.cel {{
    width: 90px;
    height: 55px;
    cursor: pointer;
    font-size: 30px;
    transition: background 0.15s;
    background: {hoofd_xlicht};
  }}
  tr.odd td.cel {{ background: {hoofd_xlicht2}; }}

  td.cel:hover {{ background: {hoofd_licht2} !important; }}
  td.cel:active {{ background: {hoofd_licht} !important; }}

  td.cel.done {{
    color: {accentkleur};
    background: {hoofd_done} !important;
  }}
  tr.odd td.cel.done {{
    background: {hoofd_done2} !important;
  }}

  td.score, td.klaar {{
    font-weight: bold;
    font-size: 15px;
    padding: 0 8px;
    background: {accent_licht};
    color: {accentkleur};
    white-space: nowrap;
  }}

  /* Layout: leerlingen bovenaan */
  th.naam-kol {{
    writing-mode: vertical-rl;
    text-orientation: mixed;
    transform: rotate(180deg);
    padding: 12px 6px;
    font-size: 14px;
    color: {accentkleur};
    background: {hoofd_licht};
    min-width: 50px;
    height: 120px;
    vertical-align: bottom;
  }}
  th.naam-kol.odd {{ background: {hoofd_licht2}; }}

  td.taak-naam {{
    font-weight: bold;
    font-size: 14px;
    color: {accentkleur};
    text-align: left;
    padding: 8px 12px;
    background: {hoofd_licht};
    white-space: nowrap;
  }}

  .score-rij td {{
    background: {accent_licht};
    font-weight: bold;
    font-size: 14px;
    color: {accentkleur};
    padding: 8px;
  }}
  td.score-label {{
    font-weight: bold;
    font-size: 14px;
    color: {accentkleur};
    text-align: left;
    padding: 8px 12px;
    background: {accent_licht};
  }}

  .reset-container {{
    text-align: center;
    padding: 20px;
  }}
  .reset-btn {{
    background: #e0e0e0;
    border: none;
    padding: 12px 30px;
    font-size: 14px;
    border-radius: 8px;
    cursor: pointer;
    color: #666;
  }}
  .reset-btn:hover {{ background: #ccc; }}

  /* Viering animatie */
  .viering-overlay {{
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.5);
    z-index: 9999;
    display: flex; align-items: center; justify-content: center;
    animation: fadeIn 0.3s ease;
    cursor: pointer;
    overflow: hidden;
  }}
  .viering-box {{
    background: white; border-radius: 24px; padding: 40px 60px;
    text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    z-index: 10000;
  }}
  .viering-ster {{
    font-size: 80px;
    animation: spinStar 1s ease;
  }}
  .viering-tekst {{
    font-size: 36px; font-weight: bold; color: {accentkleur};
    margin: 10px 0 5px; font-family: 'Roboto', sans-serif;
  }}
  .viering-sub {{
    font-size: 18px; color: {hoofdkleur}; font-weight: bold;
    font-family: 'Roboto', sans-serif;
  }}
  .confetti {{
    position: fixed; top: -10px; width: 10px; height: 10px;
    border-radius: 2px; z-index: 10001;
    animation: confettiFall linear forwards;
  }}
  @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  @keyframes popIn {{ from {{ transform: scale(0.3); opacity: 0; }} to {{ transform: scale(1); opacity: 1; }} }}
  @keyframes spinStar {{ from {{ transform: rotate(0deg) scale(0); }} 50% {{ transform: rotate(200deg) scale(1.3); }} to {{ transform: rotate(360deg) scale(1); }} }}
  @keyframes confettiFall {{
    0% {{ top: -10px; opacity: 1; transform: rotate(0deg) translateX(0); }}
    100% {{ top: 105vh; opacity: 0; transform: rotate(720deg) translateX(calc(-50px + 100px * var(--r, 0.5))); }}
  }}

  @media print {{
    .reset-container, .viering-overlay {{ display: none; }}
    td.cel {{ height: 40px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <h1>{naam_esc}</h1>
  <p>{school_esc}</p>
</div>
<div class="subheader">Raak je vakje aan als je klaar bent!</div>

<div class="tabel-container">
<table>
  <thead>
    <tr>
{header_html}    </tr>
  </thead>
  <tbody>
{rijen_html}  </tbody>
</table>
</div>

<div class="reset-container">
  <button class="reset-btn" onclick="resetAlles()">Alles wissen (opnieuw beginnen)</button>
</div>

<script>
const N_TAKEN = {n_taken};
const N_LL = {len(leerlingen)};

function toggle(cel) {{
  cel.classList.toggle('done');
  cel.textContent = cel.classList.contains('done') ? '\\u2713' : '';
  updateScores();
  slaOp();
}}

function updateScores() {{
  // Score per leerling
  for (let i = 0; i < N_LL; i++) {{
    let done = 0;
    for (let j = 0; j < N_TAKEN; j++) {{
      if (document.getElementById('c' + i + '_' + j).classList.contains('done')) done++;
    }}
    const el = document.getElementById('score' + i);
    if (el) {{
      el.textContent = done + '/' + N_TAKEN;
      el.style.color = done === N_TAKEN ? '#4CAF50' : '{accentkleur}';
      el.style.fontWeight = done === N_TAKEN ? '900' : 'bold';
    }}
    if (done === N_TAKEN && !((el||{{}}).dataset||{{}}).gevierd) {{
      if (el) el.dataset.gevierd = '1';
      viering(i);
    }}
    if (done < N_TAKEN && el) {{ el.dataset.gevierd = ''; }}
  }}
  // Klaar per taak (alleen bij layout "bovenaan")
  for (let j = 0; j < N_TAKEN; j++) {{
    let klaar = 0;
    for (let i = 0; i < N_LL; i++) {{
      if (document.getElementById('c' + i + '_' + j).classList.contains('done')) klaar++;
    }}
    const el = document.getElementById('klaar' + j);
    if (el) {{
      el.textContent = klaar + '/' + N_LL;
      el.style.color = klaar === N_LL ? '#4CAF50' : '{accentkleur}';
    }}
  }}
}}

function viering(leerlingIdx) {{
  // Overlay
  const ov = document.createElement('div');
  ov.className = 'viering-overlay';
  let naam = '';
  const naamTd = document.querySelector('tr:nth-child(' + (leerlingIdx + 1) + ') td.naam');
  const naamTh = document.querySelector('th.naam-kol:nth-of-type(' + (leerlingIdx + 2) + ')');
  if (naamTd) naam = naamTd.textContent;
  else if (naamTh) naam = naamTh.textContent;
  ov.innerHTML = '<div class="viering-box">'
    + '<div class="viering-ster">\\u2B50</div>'
    + '<div class="viering-tekst">Goed gedaan' + (naam ? ', ' + naam : '') + '!</div>'
    + '<div class="viering-sub">Alle taken afgerond!</div>'
    + '</div>';
  document.body.appendChild(ov);

  // Confetti
  for (let i = 0; i < 80; i++) {{
    const c = document.createElement('div');
    c.className = 'confetti';
    c.style.left = Math.random() * 100 + 'vw';
    c.style.animationDelay = Math.random() * 0.5 + 's';
    c.style.animationDuration = (1.5 + Math.random() * 2) + 's';
    const kleuren = ['{hoofdkleur}','{accentkleur}','#F5A623','#E74C8B','#9B59B6','#FF6B6B','#4CAF50'];
    c.style.background = kleuren[Math.floor(Math.random() * kleuren.length)];
    c.style.transform = 'rotate(' + Math.random() * 360 + 'deg)';
    ov.appendChild(c);
  }}

  // Sluit na klik of na 4 seconden
  const sluit = function() {{ if (ov.parentNode) ov.remove(); }};
  ov.addEventListener('click', sluit);
  ov.addEventListener('touchstart', sluit);
  setTimeout(sluit, 2000);
}}

function resetAlles() {{
  const ww = prompt('Voer het wachtwoord van de juf in om alles te wissen:');
  if (ww !== 'juf') {{ if (ww !== null) alert('Verkeerd wachtwoord!'); return; }}
  for (let i = 0; i < N_LL; i++) {{
    for (let j = 0; j < N_TAKEN; j++) {{
      const cel = document.getElementById('c' + i + '_' + j);
      cel.classList.remove('done');
      cel.textContent = '';
    }}
  }}
  updateScores();
  slaOp();
}}

// Sla voortgang op in de browser (blijft bewaard)
function slaOp() {{
  const staat = [];
  for (let i = 0; i < N_LL; i++) {{
    for (let j = 0; j < N_TAKEN; j++) {{
      if (document.getElementById('c' + i + '_' + j).classList.contains('done')) {{
        staat.push(i + '_' + j);
      }}
    }}
  }}
  try {{ localStorage.setItem('vbs_' + document.title, JSON.stringify(staat)); }} catch(e) {{}}
}}

function laadOp() {{
  try {{
    const staat = JSON.parse(localStorage.getItem('vbs_' + document.title));
    if (staat) {{
      staat.forEach(function(id) {{
        const cel = document.getElementById('c' + id);
        if (cel) {{ cel.classList.add('done'); cel.textContent = '\\u2713'; }}
      }});
      updateScores();
    }}
  }} catch(e) {{}}
}}

laadOp();
</script>
</body>
</html>"""

    # Zorg dat bestandspad eindigt op .html
    if not bestandspad.lower().endswith(".html"):
        bestandspad = bestandspad.rsplit(".", 1)[0] + ".html"

    with open(bestandspad, "w", encoding="utf-8") as f:
        f.write(pagina)

    return bestandspad


# ============================================================
# GUI - Stap-voor-stap Wizard
# ============================================================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Eve's Zelfstandig Werk Generator")
        self.root.geometry("800x650")
        self.root.minsize(700, 550)
        self.root.configure(bg=WIT)

        self.data = laad_data()

        self.inst = self.data["instellingen"]

        self.huidig_jaar = None
        self.huidige_klas = None

        self._bouw_layout()
        self._toon_stap_schooljaar()

    # ----------------------------------------------------------
    # LAYOUT: vaste header + wisselend inhoudspaneel
    # ----------------------------------------------------------
    def _bouw_layout(self):
        accent = self.inst.get("accentkleur", "#27A9E1")
        hoofd = self.inst.get("hoofdkleur", "#AACD55")

        # Header
        hdr = tk.Frame(self.root, bg=accent, height=55)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Eve's Zelfstandig Werk Generator",
                 font=("Segoe UI", 18, "bold"), fg=WIT, bg=accent).pack(side="left", padx=20)

        # Tandwiel knop (instellingen)
        gear = tk.Label(hdr, text="\u2699", font=("Segoe UI", 20), fg=WIT, bg=accent,
                        cursor="hand2")
        gear.pack(side="right", padx=(0, 15))
        gear.bind("<Button-1>", lambda e: self._toon_instellingen())

        self.school_label = tk.Label(hdr, text=self.inst.get("schoolnaam", ""),
                                      font=("Segoe UI", 12), fg=WIT, bg=accent)
        self.school_label.pack(side="right", padx=(0, 10))

        # Stappenbalk
        self.stappen_frame = tk.Frame(self.root, bg=hoofd, height=40)
        self.stappen_frame.pack(fill="x")
        self.stappen_frame.pack_propagate(False)
        self.stappen_label = tk.Label(
            self.stappen_frame, text="",
            font=("Segoe UI", 12, "bold"), fg=WIT, bg=hoofd,
        )
        self.stappen_label.pack(expand=True)

        # Inhoud (wordt gewisseld per stap)
        self.inhoud = tk.Frame(self.root, bg=WIT)
        self.inhoud.pack(fill="both", expand=True, padx=20, pady=15)

        # Statusbalk
        status_frame = tk.Frame(self.root, bg=LICHTGRIJS)
        status_frame.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="")
        tk.Label(status_frame, textvariable=self.status_var,
                 font=("Segoe UI", 9), bg=LICHTGRIJS, fg=DONKERGRIJS,
                 anchor="w", padx=10).pack(side="left")
        tk.Label(status_frame, text=f"v{VERSIE}",
                 font=("Segoe UI", 9), bg=LICHTGRIJS, fg="#bbb",
                 anchor="e", padx=10).pack(side="right")

    def _wis_inhoud(self):
        for w in self.inhoud.winfo_children():
            w.destroy()

    def _stel_stap_in(self, tekst):
        self.stappen_label.config(text=tekst)

    # ----------------------------------------------------------
    # HELPERS: mooie knoppen
    # ----------------------------------------------------------
    def _grote_knop(self, parent, tekst, commando, kleur=GROEN, breedte=25):
        # macOS negeert fg/bg op native buttons - we gebruiken een Label-in-Frame als knop
        frame = tk.Frame(parent, bg=kleur, cursor="hand2")
        lbl = tk.Label(
            frame, text=tekst, font=("Segoe UI", 13, "bold"),
            fg=WIT, bg=kleur, cursor="hand2", width=breedte, pady=10,
        )
        lbl.pack(fill="both", expand=True)
        for w in [frame, lbl]:
            w.bind("<Button-1>", lambda e: commando())
            hover_kleur = GROEN_DONKER if kleur == GROEN else BLAUW_DONKER
            w.bind("<Enter>", lambda e, c=hover_kleur: (frame.config(bg=c), lbl.config(bg=c)))
            w.bind("<Leave>", lambda e, c=kleur: (frame.config(bg=c), lbl.config(bg=c)))
        return frame

    def _kleine_knop(self, parent, tekst, commando, kleur=GRIJS):
        frame = tk.Frame(parent, bg=kleur, cursor="hand2")
        lbl = tk.Label(
            frame, text=tekst, font=("Segoe UI", 10),
            fg=ZWART, bg=kleur, cursor="hand2", padx=12, pady=4,
        )
        lbl.pack(fill="both", expand=True)
        for w in [frame, lbl]:
            w.bind("<Button-1>", lambda e: commando())
            w.bind("<Enter>", lambda e: (frame.config(bg="#ccc"), lbl.config(bg="#ccc")))
            w.bind("<Leave>", lambda e, c=kleur: (frame.config(bg=c), lbl.config(bg=c)))
        return frame

    # ----------------------------------------------------------
    # HELPER: scrollbare kaarten-lijst
    # ----------------------------------------------------------
    def _maak_kaarten_lijst(self, parent):
        """Maak een scrollbaar frame voor kaarten. Geeft het inner frame terug."""
        lijst_frame = tk.Frame(parent, bg=WIT)
        lijst_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(lijst_frame, bg=WIT, highlightthickness=0)
        scrollbar = tk.Scrollbar(lijst_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=WIT)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(
                        canvas.find_all()[0], width=e.width) if canvas.find_all() else None)
        return inner

    def _maak_kaart(self, parent, titel, subtitel, kleur, on_click, on_delete=None):
        """Maak een klikbare kaart met gekleurde linkerbalk."""
        kaart = tk.Frame(parent, bg=WIT, highlightbackground=GRIJS, highlightthickness=1)
        kaart.pack(fill="x", padx=8, pady=5)

        balk = tk.Frame(kaart, bg=kleur, width=8)
        balk.pack(side="left", fill="y")

        inhoud = tk.Frame(kaart, bg=WIT, padx=15, pady=12)
        inhoud.pack(side="left", fill="both", expand=True)

        lbl_t = tk.Label(inhoud, text=titel, font=("Segoe UI", 15, "bold"),
                         fg=ZWART, bg=WIT, anchor="w", cursor="hand2")
        lbl_t.pack(anchor="w")

        lbl_s = tk.Label(inhoud, text=subtitel, font=("Segoe UI", 10),
                         fg=DONKERGRIJS, bg=WIT, anchor="w", cursor="hand2")
        lbl_s.pack(anchor="w", pady=(2, 0))

        for w in [kaart, balk, inhoud, lbl_t, lbl_s]:
            w.bind("<Button-1>", lambda e: on_click())
            w.configure(cursor="hand2")

        if on_delete:
            tk.Button(kaart, text=" \u2715 ", command=on_delete,
                      font=("Segoe UI", 12), fg="#cc0000", bg=WIT,
                      activebackground="#ffcccc", relief="flat", cursor="hand2", bd=0,
                      ).pack(side="right", padx=(0, 8), pady=8)

        return kaart

    # ----------------------------------------------------------
    # DATA HELPERS
    # ----------------------------------------------------------
    def _jaar_data(self):
        """Geeft het dict van het huidige schooljaar."""
        return self.data["schooljaren"].get(self.huidig_jaar, {})

    def _klas_data(self):
        """Geeft het dict van de huidige klas."""
        return self._jaar_data().get("klassen", {}).get(self.huidige_klas, {})

    def _leerlingen(self):
        return self._klas_data().get("leerlingen", [])

    def _opdrachten(self):
        return self._klas_data().get("opdrachten", [])

    # ==========================================================
    # STAP 1: SCHOOLJAAR
    # ==========================================================
    def _toon_stap_schooljaar(self):
        self._wis_inhoud()
        self._stel_stap_in("Stap 1 van 4  \u2014  Kies een schooljaar")

        jaren = self.data["schooljaren"]

        if jaren:
            tk.Label(self.inhoud, text="Kies een schooljaar",
                     font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT,
                     ).pack(anchor="w", pady=(0, 15))

            inner = self._maak_kaarten_lijst(self.inhoud)

            kleuren = ["#27A9E1", "#AACD55", "#F5A623", "#9B59B6", "#1ABC9C"]
            for idx, jaar in enumerate(sorted(jaren.keys(), reverse=True)):
                klassen = jaren[jaar].get("klassen", {})
                n_kl = len(klassen)
                n_ll = sum(len(k.get("leerlingen", [])) for k in klassen.values())
                sub = f"{n_kl} klassen, {n_ll} leerlingen" if n_kl else "Nog geen klassen"

                self._maak_kaart(
                    inner, jaar, sub, kleuren[idx % len(kleuren)],
                    on_click=lambda j=jaar: self._selecteer_jaar(j),
                    on_delete=lambda j=jaar: self._verwijder_jaar(j),
                )
        else:
            lege = tk.Frame(self.inhoud, bg=LICHTGRIJS, padx=30, pady=30)
            lege.pack(expand=True, fill="both", pady=20)
            tk.Label(lege, text="Welkom!", font=("Segoe UI", 22, "bold"),
                     fg=BLAUW, bg=LICHTGRIJS).pack(pady=(0, 8))
            tk.Label(lege, text="Maak hieronder je eerste schooljaar aan.",
                     font=("Segoe UI", 12), fg=DONKERGRIJS, bg=LICHTGRIJS,
                     justify="center").pack()

        self._grote_knop(self.inhoud, "+  Nieuw schooljaar",
                         self._nieuw_schooljaar, kleur=BLAUW).pack(pady=(15, 0))

    def _selecteer_jaar(self, jaar):
        self.huidig_jaar = jaar
        self._toon_stap_klassen()

    def _verwijder_jaar(self, jaar):
        if messagebox.askyesno("Schooljaar verwijderen?",
                               f"'{jaar}' en ALLES erin verwijderen?"):
            del self.data["schooljaren"][jaar]
            bewaar_data(self.data)
            self._toon_stap_schooljaar()

    def _nieuw_schooljaar(self):
        self._wis_inhoud()
        self._stel_stap_in("Nieuw schooljaar")

        tk.Label(self.inhoud, text="Welk schooljaar?",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT,
                 ).pack(anchor="w", pady=(0, 5))
        tk.Label(self.inhoud, text='Bijvoorbeeld: "2025-2026"',
                 font=("Segoe UI", 11), fg=DONKERGRIJS, bg=WIT,
                 ).pack(anchor="w", pady=(0, 15))

        entry = tk.Entry(self.inhoud, font=("Segoe UI", 16), relief="solid", bd=1)
        entry.pack(fill="x", ipady=8, pady=(0, 20))

        # Stel huidig schooljaar voor
        vandaag = date.today()
        start = vandaag.year if vandaag.month >= 9 else vandaag.year - 1
        entry.insert(0, f"{start}-{start + 1}")
        entry.select_range(0, "end")
        entry.focus_set()

        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x")

        def opslaan():
            naam = entry.get().strip()
            if not naam:
                messagebox.showwarning("Invullen", "Geef het schooljaar een naam.")
                return
            if naam in self.data["schooljaren"]:
                messagebox.showwarning("Bestaat al", f"'{naam}' bestaat al.")
                return
            self.data["schooljaren"][naam] = {"klassen": {}}
            bewaar_data(self.data)
            self.huidig_jaar = naam
            self._toon_stap_klassen()

        self._grote_knop(nav, "Aanmaken", opslaan, kleur=GROEN).pack(side="left")
        self._kleine_knop(nav, "Annuleren", self._toon_stap_schooljaar).pack(side="right")
        entry.bind("<Return>", lambda e: opslaan())

    # ==========================================================
    # STAP 2: KLASSEN
    # ==========================================================
    def _toon_stap_klassen(self):
        self._wis_inhoud()
        self._stel_stap_in(f"Stap 2 van 4  \u2014  Klassen in {self.huidig_jaar}")

        klassen = self._jaar_data().get("klassen", {})

        tk.Label(self.inhoud, text=f"Klassen in {self.huidig_jaar}",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT,
                 ).pack(anchor="w", pady=(0, 15))

        if klassen:
            inner = self._maak_kaarten_lijst(self.inhoud)
            kleuren = ["#27A9E1", "#AACD55", "#F5A623", "#E74C8B", "#9B59B6",
                        "#1ABC9C", "#E67E22", "#3498DB", "#2ECC71", "#E74C3C"]

            for idx, klas_naam in enumerate(sorted(klassen.keys())):
                ll = klassen[klas_naam].get("leerlingen", [])
                n = len(ll)
                if ll:
                    preview = ", ".join(ll[:5]) + ("  ..." if n > 5 else "")
                    sub = f"{n} leerlingen  \u2014  {preview}"
                else:
                    sub = "Nog geen leerlingen"

                self._maak_kaart(
                    inner, klas_naam, sub, kleuren[idx % len(kleuren)],
                    on_click=lambda k=klas_naam: self._selecteer_klas(k),
                    on_delete=lambda k=klas_naam: self._verwijder_klas(k),
                )
        else:
            tk.Label(self.inhoud,
                     text="Nog geen klassen in dit schooljaar.\nMaak hieronder je eerste klas aan.",
                     font=("Segoe UI", 12), fg=DONKERGRIJS, bg=WIT, justify="center",
                     ).pack(expand=True)

        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x", pady=(15, 0))
        self._kleine_knop(nav, "\u2190  Schooljaren", self._toon_stap_schooljaar).pack(side="left")
        self._grote_knop(nav, "+  Nieuwe klas", self._nieuwe_klas, kleur=BLAUW,
                         breedte=18).pack(side="right")

    def _selecteer_klas(self, naam):
        self.huidige_klas = naam
        self._toon_stap_leerlingen()

    def _verwijder_klas(self, naam):
        if messagebox.askyesno("Klas verwijderen?",
                               f"'{naam}' en alle leerlingen/opdrachten verwijderen?"):
            del self.data["schooljaren"][self.huidig_jaar]["klassen"][naam]
            bewaar_data(self.data)
            self._toon_stap_klassen()

    def _nieuwe_klas(self):
        self._wis_inhoud()
        self._stel_stap_in(f"Nieuwe klas in {self.huidig_jaar}")

        tk.Label(self.inhoud, text="Hoe heet de klas?",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT,
                 ).pack(anchor="w", pady=(0, 5))
        tk.Label(self.inhoud, text='Bijvoorbeeld: "3de leerjaar A" of "Klas van juf Eva"',
                 font=("Segoe UI", 11), fg=DONKERGRIJS, bg=WIT,
                 ).pack(anchor="w", pady=(0, 15))

        entry = tk.Entry(self.inhoud, font=("Segoe UI", 16), relief="solid", bd=1)
        entry.pack(fill="x", ipady=8, pady=(0, 20))
        entry.focus_set()

        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x")

        def opslaan():
            naam = entry.get().strip()
            if not naam:
                messagebox.showwarning("Invullen", "Geef de klas een naam.")
                return
            klassen = self.data["schooljaren"][self.huidig_jaar]["klassen"]
            if naam in klassen:
                messagebox.showwarning("Bestaat al", f"'{naam}' bestaat al.")
                return
            klassen[naam] = {"leerlingen": [], "opdrachten": []}
            bewaar_data(self.data)
            self.huidige_klas = naam
            self._toon_stap_leerlingen()

        self._grote_knop(nav, "Klas aanmaken", opslaan, kleur=GROEN).pack(side="left")
        self._kleine_knop(nav, "Annuleren", self._toon_stap_klassen).pack(side="right")
        entry.bind("<Return>", lambda e: opslaan())

    # ==========================================================
    # STAP 3: LEERLINGEN
    # ==========================================================
    def _toon_stap_leerlingen(self):
        self._wis_inhoud()
        klas = self.huidige_klas
        leerlingen = self._leerlingen()
        self._stel_stap_in(f"Stap 3 van 4  \u2014  Leerlingen van {klas}")

        top = tk.Frame(self.inhoud, bg=WIT)
        top.pack(fill="x")

        tk.Label(top, text=f"Leerlingen in {klas}",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT,
                 ).pack(anchor="w", pady=(0, 5))

        # Invoer
        invoer = tk.Frame(top, bg=WIT)
        invoer.pack(fill="x", pady=(5, 10))
        tk.Label(invoer, text="Naam:", font=("Segoe UI", 12), fg=ZWART, bg=WIT).pack(side="left")
        self.entry_leerling = tk.Entry(invoer, font=("Segoe UI", 14), relief="solid", bd=1)
        self.entry_leerling.pack(side="left", fill="x", expand=True, padx=(10, 10), ipady=5)
        tk.Button(invoer, text="  Toevoegen  ", command=self._voeg_leerling_toe,
                  font=("Segoe UI", 11, "bold"), fg=WIT, bg=GROEN,
                  activebackground=GROEN_DONKER, relief="flat", cursor="hand2").pack(side="left")
        self.entry_leerling.bind("<Return>", lambda e: self._voeg_leerling_toe())
        self.entry_leerling.focus_set()

        tk.Button(top, text="Meerdere leerlingen tegelijk toevoegen (plak een lijst)",
                  command=self._bulk_leerlingen, font=("Segoe UI", 10), fg=BLAUW, bg=WIT,
                  activebackground=LICHTGRIJS, relief="flat", cursor="hand2",
                  ).pack(anchor="w", pady=(0, 10))

        # Lijst
        self.lijst_ll_frame = tk.Frame(self.inhoud, bg=WIT)
        self.lijst_ll_frame.pack(fill="both", expand=True)
        self._ververs_leerlingen_lijst()

        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x", pady=(15, 0))
        self._kleine_knop(nav, "\u2190  Klassen", self._toon_stap_klassen).pack(side="left")
        if leerlingen:
            self._grote_knop(nav, "Verder: opdracht maken  \u2192",
                             self._toon_stap_opdracht, kleur=BLAUW, breedte=25).pack(side="right")

    def _ververs_leerlingen_lijst(self):
        for w in self.lijst_ll_frame.winfo_children():
            w.destroy()
        leerlingen = self._leerlingen()
        if not leerlingen:
            tk.Label(self.lijst_ll_frame, text="\nVoeg hierboven leerlingen toe.",
                     font=("Segoe UI", 12), fg=DONKERGRIJS, bg=WIT).pack(expand=True)
            return

        canvas = tk.Canvas(self.lijst_ll_frame, bg=WIT, highlightthickness=0)
        sb = tk.Scrollbar(self.lijst_ll_frame, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=WIT)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for i, naam in enumerate(leerlingen, 1):
            bg = LICHTGRIJS if i % 2 else WIT
            f = tk.Frame(sf, bg=bg)
            f.pack(fill="x", padx=5, pady=1)
            tk.Label(f, text=f"  {i}.", font=("Segoe UI", 12), fg=DONKERGRIJS,
                     bg=bg, width=4).pack(side="left")
            tk.Label(f, text=naam, font=("Segoe UI", 13), fg=ZWART, bg=bg,
                     anchor="w").pack(side="left", fill="x", expand=True, padx=5, pady=6)
            tk.Button(f, text=" \u2715 ", command=lambda n=naam: self._verwijder_leerling(n),
                      font=("Segoe UI", 10), fg="#cc0000", bg=bg,
                      activebackground="#ffcccc", relief="flat", cursor="hand2").pack(side="right", padx=5)

    def _voeg_leerling_toe(self):
        naam = self.entry_leerling.get().strip()
        if not naam:
            return
        self._klas_data()["leerlingen"].append(naam)
        bewaar_data(self.data)
        self.entry_leerling.delete(0, "end")
        self.entry_leerling.focus_set()
        self.status_var.set(f"'{naam}' toegevoegd")
        self._toon_stap_leerlingen()

    def _verwijder_leerling(self, naam):
        self._klas_data()["leerlingen"].remove(naam)
        bewaar_data(self.data)
        self._toon_stap_leerlingen()

    def _bulk_leerlingen(self):
        self._wis_inhoud()
        self._stel_stap_in(f"Leerlingen toevoegen aan {self.huidige_klas}")

        tk.Label(self.inhoud, text="Plak of typ hieronder alle namen",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT).pack(anchor="w", pady=(0, 5))
        tk.Label(self.inhoud, text="Eén naam per regel.",
                 font=("Segoe UI", 11), fg=DONKERGRIJS, bg=WIT).pack(anchor="w", pady=(0, 10))

        txt = scrolledtext.ScrolledText(self.inhoud, font=("Segoe UI", 13), height=12,
                                         relief="solid", bd=1)
        txt.pack(fill="both", expand=True)
        txt.focus_set()

        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x", pady=(15, 0))

        def opslaan():
            namen = [n.strip() for n in txt.get("1.0", "end").strip().split("\n") if n.strip()]
            if not namen:
                messagebox.showwarning("Geen namen", "Typ of plak minstens één naam.")
                return
            self._klas_data()["leerlingen"].extend(namen)
            bewaar_data(self.data)
            self.status_var.set(f"{len(namen)} leerlingen toegevoegd")
            self._toon_stap_leerlingen()

        self._grote_knop(nav, "Toevoegen", opslaan, kleur=GROEN, breedte=20).pack(side="left")
        self._kleine_knop(nav, "Annuleren", self._toon_stap_leerlingen).pack(side="right")

    # ==========================================================
    # STAP 4: OPDRACHTEN
    # ==========================================================
    def _toon_stap_opdracht(self):
        self._wis_inhoud()
        klas = self.huidige_klas
        self._stel_stap_in(f"Stap 4 van 4  \u2014  Opdracht voor {klas}")

        eerdere = self._opdrachten()

        tk.Label(self.inhoud, text="Wat wil je doen?",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT).pack(anchor="w", pady=(0, 15))

        self._grote_knop(self.inhoud, "+  Nieuwe opdracht maken",
                         self._nieuwe_opdracht, kleur=BLAUW).pack(fill="x", pady=(0, 15))

        if eerdere:
            tk.Label(self.inhoud, text="Of kies een eerdere opdracht:",
                     font=("Segoe UI", 12), fg=DONKERGRIJS, bg=WIT).pack(anchor="w", pady=(5, 8))

            inner = self._maak_kaarten_lijst(self.inhoud)
            for opdr in reversed(eerdere):
                taken = opdr["taken"]
                preview = ", ".join(taken[:3]) + (" ..." if len(taken) > 3 else "")

                kaart = self._maak_kaart(
                    inner, opdr["naam"],
                    f"{len(taken)} taken  \u2014  {preview}",
                    GROEN,
                    on_click=lambda o=opdr: self._genereer_bestaande(o),
                    on_delete=lambda o=opdr: self._verwijder_opdracht(o),
                )

        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x", pady=(10, 0))
        self._kleine_knop(nav, "\u2190  Leerlingen", self._toon_stap_leerlingen).pack(side="left")

    def _verwijder_opdracht(self, opdracht):
        if messagebox.askyesno("Verwijderen?", f"'{opdracht['naam']}' verwijderen?"):
            self._klas_data()["opdrachten"].remove(opdracht)
            bewaar_data(self.data)
            self._toon_stap_opdracht()

    def _maak_bestandsnaam(self, opdracht_naam):
        def veilig(t):
            return "".join(c if c.isalnum() or c in " _-" else "_" for c in t)
        d = date.today().strftime("%Y-%m-%d")
        return f"{veilig(self.huidige_klas)} - {veilig(opdracht_naam)} - {d}.html"

    def _genereer_bestaande(self, opdracht):
        leerlingen = self._leerlingen()
        naam = opdracht["naam"]
        taken = opdracht["taken"]
        pad = filedialog.asksaveasfilename(
            title="Waar wil je het bestand opslaan?", defaultextension=".html",
            filetypes=[("Smartboard pagina", "*.html")],
            initialfile=self._maak_bestandsnaam(naam), initialdir=_data_map())
        if not pad:
            return
        try:
            html_pad = genereer_smartboard(leerlingen, naam, taken, pad,
                                          hoofdkleur=self.inst.get("hoofdkleur", "#AACD55"),
                                          accentkleur=self.inst.get("accentkleur", "#27A9E1"),
                                          schoolnaam=self.inst.get("schoolnaam", ""),
                                          layout=self.inst.get("layout", "bovenaan"))
            self._toon_klaar(html_pad, naam, len(leerlingen), len(taken))
        except Exception as e:
            messagebox.showerror("Er ging iets mis", str(e))

    def _nieuwe_opdracht(self):
        self._wis_inhoud()
        self._stel_stap_in(f"Nieuwe opdracht voor {self.huidige_klas}")

        tk.Label(self.inhoud, text="Nieuwe opdracht",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT).pack(anchor="w", pady=(0, 10))

        tk.Label(self.inhoud, text="Naam van de opdracht:",
                 font=("Segoe UI", 12), fg=ZWART, bg=WIT).pack(anchor="w", pady=(5, 3))
        self.entry_opdracht = tk.Entry(self.inhoud, font=("Segoe UI", 14), relief="solid", bd=1)
        self.entry_opdracht.pack(fill="x", ipady=6, pady=(0, 10))
        self.entry_opdracht.insert(0, "Zelfstandig werk - ")
        self.entry_opdracht.focus_set()
        self.entry_opdracht.icursor(len("Zelfstandig werk - "))

        tk.Label(self.inhoud, text="Taken (één per regel):",
                 font=("Segoe UI", 12), fg=ZWART, bg=WIT).pack(anchor="w", pady=(5, 3))
        self.txt_taken = scrolledtext.ScrolledText(self.inhoud, font=("Segoe UI", 13),
                                                    height=8, relief="solid", bd=1)
        self.txt_taken.pack(fill="both", expand=True, pady=(0, 10))

        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x", pady=(10, 0))
        self._kleine_knop(nav, "\u2190  Terug", self._toon_stap_opdracht).pack(side="left")
        self._grote_knop(nav, "Opslaan en genereren", self._maak_html,
                         kleur=BLAUW, breedte=22).pack(side="right")

    def _maak_html(self):
        naam = self.entry_opdracht.get().strip()
        taken_tekst = self.txt_taken.get("1.0", "end").strip()
        if not naam:
            messagebox.showwarning("Invullen", "Geef de opdracht een naam.")
            return
        taken = [t.strip() for t in taken_tekst.split("\n") if t.strip()]
        if not taken:
            messagebox.showwarning("Invullen", "Voeg minstens één taak toe.")
            return

        # Bewaar
        opdracht = {"naam": naam, "taken": taken}
        self._klas_data()["opdrachten"].append(opdracht)
        bewaar_data(self.data)

        # Genereer
        leerlingen = self._leerlingen()
        pad = filedialog.asksaveasfilename(
            title="Waar wil je het bestand opslaan?", defaultextension=".html",
            filetypes=[("Smartboard pagina", "*.html")],
            initialfile=self._maak_bestandsnaam(naam), initialdir=_data_map())
        if not pad:
            return
        try:
            html_pad = genereer_smartboard(leerlingen, naam, taken, pad,
                                          hoofdkleur=self.inst.get("hoofdkleur", "#AACD55"),
                                          accentkleur=self.inst.get("accentkleur", "#27A9E1"),
                                          schoolnaam=self.inst.get("schoolnaam", ""),
                                          layout=self.inst.get("layout", "bovenaan"))
            self._toon_klaar(html_pad, naam, len(leerlingen), len(taken))
        except Exception as e:
            messagebox.showerror("Er ging iets mis", str(e))

    # ==========================================================
    # KLAAR-SCHERM
    # ==========================================================
    def _toon_klaar(self, html_pad, opdracht_naam, n_ll, n_taken):
        self._wis_inhoud()
        self._stel_stap_in("Klaar!")

        tk.Label(self.inhoud, text="\u2705", font=("Segoe UI", 48), bg=WIT).pack(pady=(10, 0))
        tk.Label(self.inhoud, text="Je smartboard-pagina is klaar!",
                 font=("Segoe UI", 20, "bold"), fg=GROEN_DONKER, bg=WIT).pack(pady=(0, 15))

        info = tk.Frame(self.inhoud, bg=LICHTGRIJS, padx=20, pady=15)
        info.pack(fill="x", pady=(0, 10))
        for lbl, val in [("Schooljaar:", self.huidig_jaar), ("Klas:", self.huidige_klas),
                          ("Opdracht:", opdracht_naam),
                          ("Leerlingen:", str(n_ll)), ("Taken:", str(n_taken))]:
            r = tk.Frame(info, bg=LICHTGRIJS)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=lbl, font=("Segoe UI", 11, "bold"), fg=ZWART, bg=LICHTGRIJS,
                     width=12, anchor="e").pack(side="left")
            tk.Label(r, text=val, font=("Segoe UI", 11), fg=ZWART, bg=LICHTGRIJS,
                     anchor="w").pack(side="left", padx=(10, 0))

        tk.Label(self.inhoud,
                 text="Open dit bestand op het smartboard in de browser.\n"
                      "Leerlingen raken hun vakje aan = vinkje!\n"
                      "De voortgang blijft bewaard, ook na herladen.",
                 font=("Segoe UI", 11), fg=DONKERGRIJS, bg=WIT, justify="center",
                 ).pack(pady=(10, 15))

        btns = tk.Frame(self.inhoud, bg=WIT)
        btns.pack()
        self._grote_knop(btns, "Openen in browser",
                         lambda: self._open_bestand(html_pad),
                         kleur=BLAUW, breedte=20).pack(side="left", padx=5)
        self._grote_knop(btns, "Nog een opdracht",
                         self._toon_stap_opdracht,
                         kleur=GROEN, breedte=20).pack(side="left", padx=5)

        self._kleine_knop(self.inhoud, "Terug naar het begin",
                          self._toon_stap_schooljaar).pack(pady=(15, 0))

    def _open_bestand(self, pad):
        try:
            if sys.platform == "win32":
                os.startfile(pad)
            elif sys.platform == "darwin":
                os.system(f'open "{pad}"')
            else:
                os.system(f'xdg-open "{pad}"')
        except Exception:
            messagebox.showinfo("Bestand", f"Open het bestand handmatig:\n{pad}")

    # ==========================================================
    # INSTELLINGEN
    # ==========================================================
    def _toon_instellingen(self):
        self._wis_inhoud()
        self._stel_stap_in("Instellingen")

        tk.Label(self.inhoud, text="Instellingen",
                 font=("Segoe UI", 16, "bold"), fg=ZWART, bg=WIT).pack(anchor="w", pady=(0, 15))

        # Schoolnaam
        tk.Label(self.inhoud, text="Naam van de school:",
                 font=("Segoe UI", 12), fg=ZWART, bg=WIT).pack(anchor="w", pady=(5, 3))
        self.entry_schoolnaam = tk.Entry(self.inhoud, font=("Segoe UI", 14), relief="solid", bd=1)
        self.entry_schoolnaam.pack(fill="x", ipady=6, pady=(0, 15))
        self.entry_schoolnaam.insert(0, self.inst.get("schoolnaam", ""))

        # Kleuren
        tk.Label(self.inhoud, text="Kleuren:",
                 font=("Segoe UI", 12), fg=ZWART, bg=WIT).pack(anchor="w", pady=(5, 8))

        kleur_frame = tk.Frame(self.inhoud, bg=WIT)
        kleur_frame.pack(fill="x", pady=(0, 10))

        # Hoofdkleur
        hk_frame = tk.Frame(kleur_frame, bg=WIT)
        hk_frame.pack(side="left", expand=True, fill="x", padx=(0, 10))
        tk.Label(hk_frame, text="Hoofdkleur", font=("Segoe UI", 11), fg=DONKERGRIJS,
                 bg=WIT).pack(anchor="w")
        tk.Label(hk_frame, text="(headers, knoppen, tabel)",
                 font=("Segoe UI", 9), fg="#aaa", bg=WIT).pack(anchor="w")
        self.preview_hoofd = tk.Frame(hk_frame, bg=self.inst.get("hoofdkleur", "#AACD55"),
                                       width=200, height=50, cursor="hand2")
        self.preview_hoofd.pack(fill="x", pady=(5, 0), ipady=15)
        self.preview_hoofd.pack_propagate(False)
        self.lbl_hoofd = tk.Label(self.preview_hoofd, text=self.inst.get("hoofdkleur", "#AACD55"),
                                   font=("Segoe UI", 12, "bold"), fg=WIT,
                                   bg=self.inst.get("hoofdkleur", "#AACD55"), cursor="hand2")
        self.lbl_hoofd.pack(expand=True)
        for w in [self.preview_hoofd, self.lbl_hoofd]:
            w.bind("<Button-1>", lambda e: self._kies_kleur("hoofdkleur"))

        # Accentkleur
        ak_frame = tk.Frame(kleur_frame, bg=WIT)
        ak_frame.pack(side="left", expand=True, fill="x", padx=(10, 0))
        tk.Label(ak_frame, text="Accentkleur", font=("Segoe UI", 11), fg=DONKERGRIJS,
                 bg=WIT).pack(anchor="w")
        tk.Label(ak_frame, text="(titelbalk, namen, score)",
                 font=("Segoe UI", 9), fg="#aaa", bg=WIT).pack(anchor="w")
        self.preview_accent = tk.Frame(ak_frame, bg=self.inst.get("accentkleur", "#27A9E1"),
                                        width=200, height=50, cursor="hand2")
        self.preview_accent.pack(fill="x", pady=(5, 0), ipady=15)
        self.preview_accent.pack_propagate(False)
        self.lbl_accent = tk.Label(self.preview_accent, text=self.inst.get("accentkleur", "#27A9E1"),
                                    font=("Segoe UI", 12, "bold"), fg=WIT,
                                    bg=self.inst.get("accentkleur", "#27A9E1"), cursor="hand2")
        self.lbl_accent.pack(expand=True)
        for w in [self.preview_accent, self.lbl_accent]:
            w.bind("<Button-1>", lambda e: self._kies_kleur("accentkleur"))

        # Tip
        tk.Label(self.inhoud, text="Klik op een kleurvak om een andere kleur te kiezen.",
                 font=("Segoe UI", 10, "italic"), fg="#aaa", bg=WIT).pack(anchor="w", pady=(5, 15))

        # Layout keuze
        tk.Label(self.inhoud, text="Layout op het smartboard:",
                 font=("Segoe UI", 12), fg=ZWART, bg=WIT).pack(anchor="w", pady=(5, 5))

        layout_frame = tk.Frame(self.inhoud, bg=WIT)
        layout_frame.pack(fill="x", pady=(0, 5))

        self.layout_var = tk.StringVar(value=self.inst.get("layout", "bovenaan"))

        tk.Radiobutton(
            layout_frame, text="Leerlingen bovenaan (standaard)",
            variable=self.layout_var, value="bovenaan",
            font=("Segoe UI", 11), fg=ZWART, bg=WIT, activebackground=WIT,
            selectcolor=WIT,
        ).pack(anchor="w")
        tk.Radiobutton(
            layout_frame, text="Leerlingen links",
            variable=self.layout_var, value="links",
            font=("Segoe UI", 11), fg=ZWART, bg=WIT, activebackground=WIT,
            selectcolor=WIT,
        ).pack(anchor="w")

        # Spacer
        tk.Frame(self.inhoud, bg=WIT).pack(fill="both", expand=True)

        # Knoppen
        nav = tk.Frame(self.inhoud, bg=WIT)
        nav.pack(fill="x", pady=(15, 0))
        self._kleine_knop(nav, "\u2190  Terug", self._instellingen_annuleren).pack(side="left")
        self._grote_knop(nav, "Opslaan", self._instellingen_opslaan,
                         kleur=self.inst.get("accentkleur", "#27A9E1"), breedte=15).pack(side="right")

    def _kies_kleur(self, welke):
        huidige = self.inst.get(welke, "#AACD55")
        kleur = colorchooser.askcolor(color=huidige, title="Kies een kleur")
        if kleur and kleur[1]:
            hex_kleur = kleur[1]
            self.inst[welke] = hex_kleur
            if welke == "hoofdkleur":
                self.preview_hoofd.config(bg=hex_kleur)
                self.lbl_hoofd.config(bg=hex_kleur, text=hex_kleur)
            else:
                self.preview_accent.config(bg=hex_kleur)
                self.lbl_accent.config(bg=hex_kleur, text=hex_kleur)

    def _instellingen_opslaan(self):
        self.inst["schoolnaam"] = self.entry_schoolnaam.get().strip() or "Mijn School"
        self.inst["layout"] = self.layout_var.get()
        self.data["instellingen"] = self.inst
        bewaar_data(self.data)

        # Herlaad de layout met nieuwe kleuren
        for w in self.root.winfo_children():
            w.destroy()
        self._bouw_layout()
        self.status_var.set("Instellingen opgeslagen!")
        self._toon_stap_schooljaar()

    def _instellingen_annuleren(self):
        # Reload instellingen van disk (ongedaan maken van preview-wijzigingen)
        self.data = laad_data()
        if "instellingen" not in self.data:
            self.data["instellingen"] = dict(STANDAARD_INSTELLINGEN)
        self.inst = self.data["instellingen"]
        self._toon_stap_schooljaar()


# ============================================================
# UPDATE CHECK
# ============================================================
def _check_update(callback):
    """Check GitHub voor een nieuwere versie (draait in achtergrond-thread)."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = Request(url, headers={"Accept": "application/vnd.github.v3+json",
                                     "User-Agent": "EvesZelfstandigWerk"})
        with urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        laatste_tag = data.get("tag_name", "").lstrip("v")
        if not laatste_tag:
            return

        # Vergelijk versies
        def versie_tuple(v):
            return tuple(int(x) for x in v.split(".") if x.isdigit())

        if versie_tuple(laatste_tag) > versie_tuple(VERSIE):
            # Zoek de juiste download URL voor dit platform
            if sys.platform == "win32":
                zoek = "Windows"
            elif sys.platform == "darwin":
                zoek = "macOS"
            else:
                zoek = "Linux"

            download_url = data.get("html_url", "")
            for asset in data.get("assets", []):
                if zoek in asset.get("name", ""):
                    download_url = asset["browser_download_url"]
                    break

            callback(laatste_tag, download_url)
    except Exception:
        pass  # Stil falen - geen internet is geen probleem


# ============================================================
# START
# ============================================================
def main():
    root = tk.Tk()
    try:
        if sys.platform == "win32":
            root.iconbitmap(default="")
    except Exception:
        pass
    app = App(root)

    # Check voor updates in de achtergrond
    def on_update(nieuwe_versie, download_url):
        root.after(0, lambda: _toon_update(root, nieuwe_versie, download_url))

    threading.Thread(target=_check_update, args=(on_update,), daemon=True).start()

    root.mainloop()


def _toon_update(root, nieuwe_versie, download_url):
    """Toon een update-melding bovenaan het venster."""
    bar = tk.Frame(root, bg="#FFF3CD", height=40)
    bar.pack(fill="x", side="top", before=root.winfo_children()[0])
    bar.pack_propagate(False)

    tk.Label(
        bar, text=f"Nieuwe versie beschikbaar: v{nieuwe_versie}  (jij hebt v{VERSIE})",
        font=("Segoe UI", 11), fg="#856404", bg="#FFF3CD",
    ).pack(side="left", padx=15)

    def download():
        webbrowser.open(download_url)
        bar.destroy()

    tk.Button(
        bar, text="Downloaden", command=download,
        font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#27A9E1",
        activebackground="#1E8CBF", relief="flat", cursor="hand2",
        padx=12, pady=2,
    ).pack(side="right", padx=(0, 10), pady=5)

    tk.Button(
        bar, text="\u2715", command=bar.destroy,
        font=("Segoe UI", 10), fg="#856404", bg="#FFF3CD",
        activebackground="#FFE69C", relief="flat", cursor="hand2",
        bd=0,
    ).pack(side="right", padx=(0, 5), pady=5)


if __name__ == "__main__":
    main()
