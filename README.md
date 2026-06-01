# Eve's Zelfstandig Werk Generator

Een gebruiksvriendelijke tool waarmee leerkrachten zelfstandige werkbladen maken voor op het **smartboard**. Leerlingen vinken hun taken af door het scherm aan te raken.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Wat doet het?

1. **Schooljaar** aanmaken (bijv. 2025-2026)
2. **Klassen** beheren met leerlingen
3. **Opdrachten** aanmaken met taken
4. **HTML-bestand** genereren dat je opent op het smartboard

De leerlingen raken hun vakje aan op het smartboard en er verschijnt een vinkje. Als alle taken klaar zijn, krijgen ze een confetti-animatie!

### Features

- Stap-voor-stap wizard, volledig in het Nederlands
- Touch-optimized voor smartboards
- Voortgang wordt automatisch bewaard in de browser
- Confetti-animatie bij voltooiing
- Reset alleen mogelijk met wachtwoord (voor de leerkracht)
- Klassen, leerlingen en opdrachten worden bewaard tussen sessies
- Werkt offline, geen internet nodig
- VBS Aaigem huisstijl (aanpasbaar)

## Installatie

### Kant-en-klare downloads

Ga naar [Releases](../../releases) en download de versie voor jouw besturingssysteem:

| Platform | Bestand |
|----------|---------|
| Windows | `Eves.Zelfstandig.Werk.exe` |
| macOS | `Eves.Zelfstandig.Werk.app.zip` |
| Linux | `Eves.Zelfstandig.Werk.linux` |

Dubbelklik om te openen. Geen installatie nodig.

### Zelf draaien vanuit broncode

```bash
# Vereisten: Python 3.9+ met tkinter
git clone https://github.com/jurgencoetsiers/Eve.git
cd Eve
python zelfstandig_werk_app.py
```

### Zelf bouwen als app

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "Eves Zelfstandig Werk" zelfstandig_werk_app.py
```

De app verschijnt in de `dist/` map.

## Gebruik

### In de app

1. Maak een **schooljaar** aan
2. Voeg een **klas** toe met leerlingen
3. Maak een **opdracht** met taken
4. Klik **"Opslaan en genereren"**
5. Open het HTML-bestand op het smartboard in een browser

### Op het smartboard

- Leerlingen raken hun vakje aan = vinkje
- Nog eens raken = vinkje weg
- Score wordt automatisch bijgehouden
- Alle taken klaar = confetti!
- Pagina herladen = voortgang blijft bewaard
- **"Alles wissen"** knop is beveiligd met wachtwoord `juf`

## Gegevensopslag

Klassen en leerlingen worden bewaard in:
```
~/Documents/Eve's Zelfstandig Werk/klassen_en_leerlingen.json
```

## Bijdragen

Bijdragen zijn welkom! Open een issue of stuur een pull request.

## Licentie

MIT License - zie [LICENSE](LICENSE)
