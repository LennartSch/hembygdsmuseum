# Hembygdsmuseum - Föremålsdatabas

Ett databashanteringssystem för att registrera, hantera och söka efter föremål i ett hembygdsmuseum.

## Funktioner

- **Registrera föremål** med detaljerad information (accessionsnummer, namn, beskrivning, kategori, material, mått, etc.)
- **Bildhantering** - Lägg till och visa bilder för varje föremål
- **Kategorisering** - Hantera hierarkiska kategorier
- **Förvaringsplatser** - Spåra var föremål förvaras (byggnad, rum, hylla)
- **Givare** - Registrera information om givare
- **Sökning** - Sök och filtrera föremål efter olika kriterier
- **Statistik** - Översikt över samlingen
- **Backup** - Skapa säkerhetskopior av databasen

## Installation

### Förutsättningar

- Python 3.7 eller senare
- tkinter (ingår vanligtvis med Python)
- PIL/Pillow för bildhantering

### Installera beroenden

```bash
pip install Pillow
```

## Användning

### Starta programmet

```bash
# Med startskriptet
./start_hembygdsmuseum.sh

# Eller direkt med Python
python3 hembygdsmuseum.py
```

### Snabbstart

1. **Registrera föremål** - Gå till fliken "Registrera föremål" och fyll i formuläret
2. **Lägg till bilder** - Klicka på "Lägg till bild" för att bifoga foton
3. **Sök föremål** - Använd fliken "Sök föremål" för att hitta registrerade objekt
4. **Hantera kategorier** - Lägg till egna kategorier under fliken "Kategorier"
5. **Platser** - Definiera förvaringsplatser under fliken "Platser"

## Databasstruktur

Systemet använder SQLite och består av följande tabeller:

- `foremal` - Huvudtabell för föremål
- `kategorier` - Hierarkiska kategorier
- `platser` - Förvaringsplatser
- `givare` - Information om givare
- `foton` - Bilder kopplade till föremål
- `utstallningar` - Utställningar
- `konservering` - Konserveringshistorik

## Backup

Skapa backup via menyn: **Arkiv → Backup databas**

Backuper sparas i mappen `backup/` med tidsstämpel.

## Manual

Se [HEMBYGDSMUSEUM_MANUAL.md](HEMBYGDSMUSEUM_MANUAL.md) för detaljerad manual.

## Teknisk information

- **Språk:** Python 3
- **GUI:** Tkinter
- **Databas:** SQLite3
- **Bildhantering:** PIL/Pillow

## Licens

© 2026

## Support

För frågor eller problem, kontakta projektansvarig.
