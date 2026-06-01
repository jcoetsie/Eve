#!/usr/bin/env python3
"""
Eve's Zelfstandig Werk Generator - VBS Aaigem
Stap-voor-stap tool voor leerkrachten.

Bouw als Windows .exe:
  pip install pyinstaller
  pyinstaller --onefile --windowed --name "Eve's Zelfstandig Werk" zelfstandig_werk_app.py
"""

import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import json
import os
import sys
from datetime import date

# ============================================================
# KLEUREN - VBS Aaigem huisstijl
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
# DATA OPSLAG - klassen, leerlingen, opdrachten
# ============================================================
def laad_data():
    pad = _data_pad()
    if os.path.exists(pad):
        try:
            with open(pad, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"klassen": {}, "opdrachten": {}}


def bewaar_data(data):
    pad = _data_pad()
    with open(pad, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================
# HTML GENERATOR - Smartboard Touch (geen macro's nodig!)
# ============================================================
def genereer_smartboard(leerlingen, opdracht_naam, taken, bestandspad):
    """Genereer een HTML-bestand voor het smartboard.

    Touch op een vakje = vinkje aan/uit. Werkt in elke browser.
    Geen installatie, geen macro's, gewoon dubbelklikken om te openen.
    """
    import html as html_mod

    n_taken = len(taken)
    naam_esc = html_mod.escape(opdracht_naam)

    # Bouw tabel-rijen
    rijen_html = ""
    for i, naam in enumerate(leerlingen):
        naam_esc_ll = html_mod.escape(naam)
        even = "even" if i % 2 == 0 else "odd"
        cellen = ""
        for j in range(n_taken):
            cellen += f'      <td class="cel {even}" onclick="toggle(this)" id="c{i}_{j}"></td>\n'
        rijen_html += f"""    <tr class="{even}">
      <td class="naam">{naam_esc_ll}</td>
{cellen}      <td class="score" id="score{i}">0/{n_taken}</td>
    </tr>
"""

    # Bouw taak-headers
    taak_headers = ""
    for taak in taken:
        taak_headers += f"      <th>{html_mod.escape(taak)}</th>\n"

    pagina = f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{naam_esc} - VBS Aaigem</title>
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
    background: #27A9E1;
    color: white;
    text-align: center;
    padding: 18px 20px 10px;
  }}
  .header h1 {{ font-size: 28px; margin-bottom: 4px; }}
  .header p {{ font-size: 16px; opacity: 0.85; }}

  .subheader {{
    background: #AACD55;
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
    background: #AACD55;
    color: white;
    font-weight: bold;
    font-size: 13px;
    padding: 12px 8px;
    border: 2px solid #8AB535;
    text-align: center;
    min-width: 90px;
  }}
  th:first-child {{
    min-width: 160px;
    font-size: 15px;
    background: #8AB535;
  }}
  th:last-child {{
    min-width: 70px;
    background: #27A9E1;
    border-color: #1E8CBF;
  }}

  td {{
    border: 2px solid #ccc;
    text-align: center;
    vertical-align: middle;
  }}

  td.naam {{
    font-weight: bold;
    font-size: 16px;
    color: #27A9E1;
    text-align: left;
    padding: 0 12px;
    background: #E8F5D4;
    white-space: nowrap;
  }}
  tr.odd td.naam {{ background: #D4EEA0; }}

  td.cel {{
    width: 90px;
    height: 55px;
    cursor: pointer;
    font-size: 30px;
    transition: background 0.15s;
    background: #F0FAE0;
  }}
  tr.odd td.cel {{ background: #E4F2CC; }}

  td.cel:hover {{ background: #d4e8b0 !important; }}
  td.cel:active {{ background: #c0d89a !important; }}

  td.cel.done {{
    color: #27A9E1;
    background: #b8e6a0 !important;
  }}
  tr.odd td.cel.done {{
    background: #a8d890 !important;
  }}

  td.score {{
    font-weight: bold;
    font-size: 15px;
    padding: 0 8px;
    background: #D4EEF9;
    color: #27A9E1;
    white-space: nowrap;
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
    font-size: 36px; font-weight: bold; color: #27A9E1;
    margin: 10px 0 5px; font-family: 'Roboto', sans-serif;
  }}
  .viering-sub {{
    font-size: 18px; color: #AACD55; font-weight: bold;
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
  <p>VBS Aaigem</p>
</div>
<div class="subheader">Raak je vakje aan als je klaar bent!</div>

<div class="tabel-container">
<table>
  <thead>
    <tr>
      <th>Leerling</th>
{taak_headers}      <th>Score</th>
    </tr>
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
  for (let i = 0; i < N_LL; i++) {{
    let done = 0;
    for (let j = 0; j < N_TAKEN; j++) {{
      if (document.getElementById('c' + i + '_' + j).classList.contains('done')) done++;
    }}
    const el = document.getElementById('score' + i);
    el.textContent = done + '/' + N_TAKEN;
    el.style.color = done === N_TAKEN ? '#4CAF50' : '#27A9E1';
    el.style.fontWeight = done === N_TAKEN ? '900' : 'bold';
    if (done === N_TAKEN && !el.dataset.gevierd) {{
      el.dataset.gevierd = '1';
      viering(i);
    }}
    if (done < N_TAKEN) {{ el.dataset.gevierd = ''; }}
  }}
}}

function viering(leerlingIdx) {{
  // Overlay
  const ov = document.createElement('div');
  ov.className = 'viering-overlay';
  const naamEl = document.querySelector('tr:nth-child(' + (leerlingIdx + 1) + ') td.naam');
  const naam = naamEl ? naamEl.textContent : '';
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
    const kleuren = ['#AACD55','#27A9E1','#F5A623','#E74C8B','#9B59B6','#FF6B6B','#4CAF50'];
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
        # Migreer oude data-structuur (zonder schooljaren)
        if "klassen" in self.data and "schooljaren" not in self.data:
            self.data = {"schooljaren": {}}
            bewaar_data(self.data)

        if "schooljaren" not in self.data:
            self.data["schooljaren"] = {}

        self.huidig_jaar = None
        self.huidige_klas = None

        self._bouw_layout()
        self._toon_stap_schooljaar()

    # ----------------------------------------------------------
    # LAYOUT: vaste header + wisselend inhoudspaneel
    # ----------------------------------------------------------
    def _bouw_layout(self):
        # Header
        hdr = tk.Frame(self.root, bg=BLAUW, height=55)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Eve's Zelfstandig Werk Generator",
                 font=("Segoe UI", 18, "bold"), fg=WIT, bg=BLAUW).pack(side="left", padx=20)
        tk.Label(hdr, text="VBS Aaigem",
                 font=("Segoe UI", 12), fg=WIT, bg=BLAUW).pack(side="right", padx=20)

        # Stappenbalk
        self.stappen_frame = tk.Frame(self.root, bg=GROEN, height=40)
        self.stappen_frame.pack(fill="x")
        self.stappen_frame.pack_propagate(False)
        self.stappen_label = tk.Label(
            self.stappen_frame, text="",
            font=("Segoe UI", 12, "bold"), fg=WIT, bg=GROEN,
        )
        self.stappen_label.pack(expand=True)

        # Inhoud (wordt gewisseld per stap)
        self.inhoud = tk.Frame(self.root, bg=WIT)
        self.inhoud.pack(fill="both", expand=True, padx=20, pady=15)

        # Statusbalk
        self.status_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self.status_var,
                 font=("Segoe UI", 9), bg=LICHTGRIJS, fg=DONKERGRIJS,
                 anchor="w", padx=10).pack(fill="x", side="bottom")

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
            html_pad = genereer_smartboard(leerlingen, naam, taken, pad)
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
            html_pad = genereer_smartboard(leerlingen, naam, taken, pad)
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
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
