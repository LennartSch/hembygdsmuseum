# Hembygdsmuseum - Användarmanual

## Installation och Start

### Krav
- Python 3.7 eller senare
- Tkinter (ingår vanligtvis i Python)
- SQLite3 (ingår vanligtvis i Python)

### Starta programmet
```bash
python3 hembygdsmuseum.py
```

Eller med shebang:
```bash
chmod +x hembygdsmuseum.py
./hembygdsmuseum.py
```

## Funktioner

### 1. Registrera Föremål
Den första fliken används för att lägga till nya föremål i databasen.

**Obligatoriska fält:**
- **Accessionsnummer** - Unikt nummer för föremålet (t.ex. 2026.001)
  - Använd "Generera"-knappen för att automatiskt få nästa lediga nummer
- **Namn** - Vad föremålet heter (t.ex. "Mjölkskål", "Slev")

**Valfria fält:**
- Beskrivning - Detaljerad beskrivning av föremålet
- Kategori - Välj från fördefinierade kategorier
- Material - Vad föremålet är tillverkat av
- Tillverkningsår - När det tillverkades (kan vara ungefärligt)
- Tillverkningsplats - Var det tillverkades
- Tillverkare - Vem som tillverkade det
- Mått (L×B×H) - Måtten i centimeter
- Vikt - Vikten i gram
- Skick - Utmärkt/Gott/Dåligt
- Placering - Var föremålet förvaras
- Registrerad av - Ditt namn

**Så här gör du:**
1. Klicka på "Generera" för att få ett accessionsnummer
2. Fyll i namn och övriga uppgifter
3. Klicka på "Spara föremål"
4. Formuläret rensas automatiskt och nästa nummer genereras

### 2. Sök Föremål
Här kan du söka efter och visa föremål.

**Sökalternativ:**
- **Sökterm** - Sök i namn, beskrivning eller accessionsnummer
- **Kategori** - Filtrera på specifik kategori
- **Sök** - Utför sökning
- **Visa alla** - Visa alla föremål i databasen

**Visa detaljer:**
- Dubbelklicka på ett föremål i listan
- Eller välj ett föremål och klicka på "Visa detaljer"

### 3. Kategorier
Hantera kategorier för att organisera föremålen.

**Fördefinierade kategorier:**
- Hushåll
- Jordbruk
- Textil
- Verktyg
- Möbler
- Dokumentation
- Konst
- Leksaker
- Kläder
- Husgeråd
- Hantverk
- Övrigt

**Lägg till egen kategori:**
1. Skriv namnet på den nya kategorin
2. Klicka på "Lägg till"

### 4. Platser
Hantera förvaringsplatser för föremålen.

**Platshierarki:**
- Byggnad (t.ex. "Huvudbyggnad", "Magasin A")
- Rum (t.ex. "Utställningssal", "Förråd")
- Hylla/Sektion (t.ex. "Hylla 3", "Sektion B")

**Lägg till ny plats:**
1. Fyll i byggnad (obligatoriskt)
2. Fyll i rum och hylla/sektion (valfritt)
3. Klicka på "Lägg till plats"

### 5. Givare
Registrera personer eller institutioner som donerat föremål.

**Information att registrera:**
- Namn (obligatoriskt)
- Adress
- Telefon
- E-post
- Anteckningar

**Användning:**
1. Fyll i givarens uppgifter
2. Klicka på "Lägg till givare"

*Observera: För att koppla en givare till ett föremål krävs databasåtkomst via SQL (funktion under utveckling).*

### 6. Statistik
Visa översikt över samlingen.

**Information som visas:**
- Totalt antal föremål
- Fördelning per kategori
- De 10 senast registrerade föremålen

Klicka på "Uppdatera statistik" för att få senaste data.

## Menyfunktioner

### Arkiv-menyn
- **Backup databas** - Skapar en säkerhetskopia av databasen i mappen "backup"
  - Format: `hembygdsmuseum_backup_ÅÅÅÅMMDD_HHMMSS.db`
  - Rekommendation: Gör backup regelbundet!
- **Avsluta** - Stäng programmet

### Hjälp-menyn
- **Om programmet** - Visa information om programmet

## Databasstruktur

Databasen heter `hembygdsmuseum.db` och skapas automatiskt första gången du startar programmet.

**Huvudtabeller:**
- `foremal` - Alla museiföremål
- `kategorier` - Kategorier för klassificering
- `platser` - Förvaringsplatser
- `givare` - Donatorer
- `foremal_givare` - Koppling mellan föremål och givare
- `foton` - Bilder av föremål (ej implementerat i GUI)
- `utstallningar` - Utställningar (ej implementerat i GUI)
- `konservering` - Konserveringshistorik (ej implementerat i GUI)

## Tips och Tricks

### Accessionsnummer
- Formatet ÅÅÅÅ.NNN är standard (t.ex. 2026.001, 2026.002)
- Använd "Generera"-knappen för att undvika dubbletter
- Numreringen börjar om varje år

### Sökfunktion
- Sökningen är inte skiftlägeskänslig
- Du kan söka på delar av ord (t.ex. "mjölk" hittar "mjölkskål")
- Kombinera sökterm och kategori för precisare resultat

### Backup
- Gör backup innan du gör stora ändringar
- Spara backups på extern plats för extra säkerhet
- Backup-filer kan öppnas direkt som nya databaser

### Best Practice
1. Registrera föremål så snart de kommer in
2. Var konsekvent med namngivning och kategorisering
3. Fyll i så mycket information som möjligt
4. Ta foton av föremålen (funktion för bildhantering kommer)
5. Gör regelbundna säkerhetskopior

## Framtida Funktioner

Följande funktioner är planerade:
- [ ] Bildhantering - Ladda upp och visa foton av föremål
- [ ] Utställningshantering - Planera och dokumentera utställningar
- [ ] Konserveringslogg - Spåra reparationer och underhåll
- [ ] QR-kodsgenerering - Skapa etiketter för föremål
- [ ] Export till Excel/PDF - Skapa rapporter och inventarielistor
- [ ] Avancerad sökning - Fler sökfilter och sorteringsmöjligheter
- [ ] Användarbehörigheter - Olika åtkomstnivåer
- [ ] Lånestatus - Spåra utlånade föremål

## Felsökning

### Programmet startar inte
- Kontrollera att Python 3 är installerat: `python3 --version`
- Kontrollera att Tkinter finns: `python3 -m tkinter`

### Kan inte spara föremål
- Kontrollera att accessionsnumret är unikt
- Kontrollera att namn är ifyllt
- Kolla att du har skrivbehörighet i mappen

### Databasen är skadad
- Återställ från senaste backup
- Kontakta support om problemet kvarstår

## Support och Utveckling

Detta är ett open source-projekt skapat för svenska hembygdsmuseer.

För frågor, buggrapporter eller funktionsförslag:
- Skapa en issue på GitHub
- Mejla till [din e-post här]

## Licens

Detta program är fritt att använda och modifiera för ideella ändamål.

---

**Version:** 1.0
**Senast uppdaterad:** 2026-02-12
**Skapad med:** Python 3, SQLite, Tkinter
