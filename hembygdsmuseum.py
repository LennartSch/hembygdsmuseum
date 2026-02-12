#!/usr/bin/env python3
"""
Hembygdsmuseum - Databashanteringssystem för museiföremål
Skapad för att registrera, hantera och söka efter föremål i ett hembygdsmuseum.
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import shutil
from pathlib import Path
from PIL import Image, ImageTk
import webbrowser
import tempfile
import base64


class MuseumDB:
    """Hanterar databaskommunikation för museet"""

    def __init__(self, db_path="hembygdsmuseum.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.anslut()
        self.skapa_tabeller()

    def anslut(self):
        """Anslut till databasen"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def skapa_tabeller(self):
        """Skapa alla nödvändiga tabeller"""

        # Föremål (huvudtabell)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS foremal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accessionsnummer TEXT UNIQUE NOT NULL,
                namn TEXT NOT NULL,
                beskrivning TEXT,
                kategori_id INTEGER,
                material TEXT,
                tillverkningsar TEXT,
                tillverkningsplats TEXT,
                tillverkare TEXT,
                matt_langd REAL,
                matt_bredd REAL,
                matt_hojd REAL,
                vikt REAL,
                skick TEXT,
                placering_id INTEGER,
                datum_registrerat TEXT NOT NULL,
                registrerad_av TEXT,
                FOREIGN KEY (kategori_id) REFERENCES kategorier(id),
                FOREIGN KEY (placering_id) REFERENCES platser(id) ON DELETE SET NULL
            )
        """)

        # Kategorier (hierarkisk struktur)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS kategorier (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namn TEXT NOT NULL UNIQUE,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES kategorier(id)
            )
        """)

        # Givare
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS givare (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namn TEXT NOT NULL,
                adress TEXT,
                telefon TEXT,
                epost TEXT,
                anteckningar TEXT
            )
        """)

        # Föremål-Givare koppling
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS foremal_givare (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                foremal_id INTEGER NOT NULL,
                givare_id INTEGER NOT NULL,
                gavodatum TEXT,
                forvarvstyp TEXT,
                anteckningar TEXT,
                FOREIGN KEY (foremal_id) REFERENCES foremal(id),
                FOREIGN KEY (givare_id) REFERENCES givare(id)
            )
        """)

        # Förvaringplatser
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS platser (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                byggnad TEXT NOT NULL,
                rum TEXT,
                hylla_sektion TEXT,
                anteckningar TEXT
            )
        """)

        # Foton
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS foton (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                foremal_id INTEGER NOT NULL,
                filsokvag TEXT NOT NULL,
                beskrivning TEXT,
                fotograf TEXT,
                datum TEXT,
                FOREIGN KEY (foremal_id) REFERENCES foremal(id)
            )
        """)

        # Utställningar
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS utstallningar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                namn TEXT NOT NULL,
                startdatum TEXT,
                slutdatum TEXT,
                beskrivning TEXT
            )
        """)

        # Föremål-Utställning koppling
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS foremal_utstallning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                foremal_id INTEGER NOT NULL,
                utstallning_id INTEGER NOT NULL,
                FOREIGN KEY (foremal_id) REFERENCES foremal(id),
                FOREIGN KEY (utstallning_id) REFERENCES utstallningar(id)
            )
        """)

        # Konserveringshistorik
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS konservering (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                foremal_id INTEGER NOT NULL,
                datum TEXT NOT NULL,
                atgard TEXT NOT NULL,
                utford_av TEXT,
                kostnad REAL,
                anteckningar TEXT,
                FOREIGN KEY (foremal_id) REFERENCES foremal(id)
            )
        """)

        self.conn.commit()
        self.lagg_till_standardkategorier()

    def lagg_till_standardkategorier(self):
        """Lägg till grundläggande kategorier om de inte finns"""
        standardkategorier = [
            "Hushåll",
            "Jordbruk",
            "Textil",
            "Verktyg",
            "Möbler",
            "Dokumentation",
            "Konst",
            "Leksaker",
            "Kläder",
            "Husgeråd",
            "Hantverk",
            "Övrigt"
        ]

        for kat in standardkategorier:
            try:
                self.cursor.execute("INSERT INTO kategorier (namn) VALUES (?)", (kat,))
            except sqlite3.IntegrityError:
                pass  # Kategorin finns redan

        self.conn.commit()

    def lagg_till_standardplatser(self):
        """Lägg till standardförvaringplatser"""
        standardplatser = [
            ("Huvudbyggnad", "Utställningssal", None),
            ("Huvudbyggnad", "Förråd", None),
            ("Magasin A", None, None),
            ("Magasin B", None, None),
        ]

        for plats in standardplatser:
            try:
                self.cursor.execute(
                    "INSERT INTO platser (byggnad, rum, hylla_sektion) VALUES (?, ?, ?)",
                    plats
                )
            except sqlite3.IntegrityError:
                pass

        self.conn.commit()

    def hamta_kategorier(self):
        """Hämta alla kategorier"""
        self.cursor.execute("SELECT id, namn FROM kategorier ORDER BY namn")
        return self.cursor.fetchall()

    def hamta_platser(self):
        """Hämta alla platser"""
        self.cursor.execute("""
            SELECT id, byggnad, rum, hylla_sektion
            FROM platser
            ORDER BY byggnad, rum
        """)
        return self.cursor.fetchall()

    def hamta_givare(self):
        """Hämta alla givare (endast id och namn)"""
        self.cursor.execute("SELECT id, namn FROM givare ORDER BY namn")
        return self.cursor.fetchall()

    def hamta_alla_givare_detaljerat(self):
        """Hämta alla givare med fullständig information"""
        self.cursor.execute("""
            SELECT id, namn, adress, telefon, epost, anteckningar
            FROM givare
            ORDER BY namn
        """)
        return self.cursor.fetchall()

    def lagg_till_foremal(self, data):
        """Lägg till nytt föremål"""
        query = """
            INSERT INTO foremal (
                accessionsnummer, namn, beskrivning, kategori_id, material,
                tillverkningsar, tillverkningsplats, tillverkare,
                matt_langd, matt_bredd, matt_hojd, vikt, skick,
                placering_id, datum_registrerat, registrerad_av
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.cursor.execute(query, data)
        self.conn.commit()
        return self.cursor.lastrowid

    def sok_foremal(self, sokterm="", kategori_id=None):
        """Sök efter föremål"""
        query = """
            SELECT f.*, k.namn as kategori_namn, p.byggnad, p.rum
            FROM foremal f
            LEFT JOIN kategorier k ON f.kategori_id = k.id
            LEFT JOIN platser p ON f.placering_id = p.id
            WHERE 1=1
        """
        params = []

        if sokterm:
            query += " AND (f.namn LIKE ? OR f.beskrivning LIKE ? OR f.accessionsnummer LIKE ?)"
            sokterm_wildcard = f"%{sokterm}%"
            params.extend([sokterm_wildcard, sokterm_wildcard, sokterm_wildcard])

        if kategori_id:
            query += " AND f.kategori_id = ?"
            params.append(kategori_id)

        query += " ORDER BY f.accessionsnummer DESC"

        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def hamta_foremal(self, foremal_id):
        """Hämta ett specifikt föremål"""
        self.cursor.execute("""
            SELECT f.*, k.namn as kategori_namn, p.byggnad, p.rum, p.hylla_sektion
            FROM foremal f
            LEFT JOIN kategorier k ON f.kategori_id = k.id
            LEFT JOIN platser p ON f.placering_id = p.id
            WHERE f.id = ?
        """, (foremal_id,))
        return self.cursor.fetchone()

    def lagg_till_kategori(self, namn):
        """Lägg till ny kategori"""
        self.cursor.execute("INSERT INTO kategorier (namn) VALUES (?)", (namn,))
        self.conn.commit()
        return self.cursor.lastrowid

    def lagg_till_plats(self, byggnad, rum, hylla):
        """Lägg till ny plats"""
        self.cursor.execute(
            "INSERT INTO platser (byggnad, rum, hylla_sektion) VALUES (?, ?, ?)",
            (byggnad, rum, hylla)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def ta_bort_plats(self, plats_id):
        """Ta bort en plats (sätter placering_id till NULL för föremål som använder platsen)"""
        self.cursor.execute("DELETE FROM platser WHERE id = ?", (plats_id,))
        self.conn.commit()

    def lagg_till_givare(self, namn, adress, telefon, epost, anteckningar):
        """Lägg till ny givare"""
        self.cursor.execute(
            "INSERT INTO givare (namn, adress, telefon, epost, anteckningar) VALUES (?, ?, ?, ?, ?)",
            (namn, adress, telefon, epost, anteckningar)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def koppla_foremal_givare(self, foremal_id, givare_id, gavodatum, forvarvstyp, anteckningar):
        """Koppla föremål till givare"""
        self.cursor.execute(
            """INSERT INTO foremal_givare
               (foremal_id, givare_id, gavodatum, forvarvstyp, anteckningar)
               VALUES (?, ?, ?, ?, ?)""",
            (foremal_id, givare_id, gavodatum, forvarvstyp, anteckningar)
        )
        self.conn.commit()

    def lagg_till_foto(self, foremal_id, filsokvag, beskrivning=None, fotograf=None):
        """Lägg till ett foto för ett föremål"""
        datum = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            """INSERT INTO foton (foremal_id, filsokvag, beskrivning, fotograf, datum)
               VALUES (?, ?, ?, ?, ?)""",
            (foremal_id, filsokvag, beskrivning, fotograf, datum)
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def hamta_foton(self, foremal_id):
        """Hämta alla foton för ett föremål"""
        self.cursor.execute(
            "SELECT * FROM foton WHERE foremal_id = ? ORDER BY datum DESC",
            (foremal_id,)
        )
        return self.cursor.fetchall()

    def ta_bort_foto(self, foto_id):
        """Ta bort ett foto från databasen"""
        self.cursor.execute("DELETE FROM foton WHERE id = ?", (foto_id,))
        self.conn.commit()

    def hamta_statistik(self):
        """Hämta statistik om samlingen"""
        stats = {}

        # Total antal föremål
        self.cursor.execute("SELECT COUNT(*) FROM foremal")
        stats['totalt'] = self.cursor.fetchone()[0]

        # Antal per kategori
        self.cursor.execute("""
            SELECT k.namn, COUNT(f.id) as antal
            FROM kategorier k
            LEFT JOIN foremal f ON k.id = f.kategori_id
            GROUP BY k.id, k.namn
            ORDER BY antal DESC
        """)
        stats['per_kategori'] = self.cursor.fetchall()

        # Senaste registreringarna
        self.cursor.execute("""
            SELECT accessionsnummer, namn, datum_registrerat
            FROM foremal
            ORDER BY datum_registrerat DESC
            LIMIT 10
        """)
        stats['senaste'] = self.cursor.fetchall()

        return stats

    def stang(self):
        """Stäng databasanslutningen"""
        if self.conn:
            self.conn.close()


class PrintManager:
    """Hanterar utskriftsfunktioner"""

    @staticmethod
    def generera_html_header():
        """Generera HTML-header med styling"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Hembygdsmuseum - Utskrift</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th {
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .info-section {
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
        }
        .label {
            font-weight: bold;
            color: #2c3e50;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            text-align: center;
            color: #7f8c8d;
        }
        @media print {
            body { margin: 20px; }
            .no-print { display: none; }
        }
    </style>
</head>
<body>
"""

    @staticmethod
    def generera_html_footer():
        """Generera HTML-footer"""
        datum = datetime.now().strftime("%Y-%m-%d %H:%M")
        return f"""
    <div class="footer">
        <p>Hembygdsmuseum - Utskrivet {datum}</p>
    </div>
</body>
</html>
"""

    @staticmethod
    def visa_utskrift(html_innehall, titel="Utskrift"):
        """Öppna utskrift i webbläsare"""
        # Skapa temporär HTML-fil
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(PrintManager.generera_html_header())
            f.write(html_innehall)
            f.write(PrintManager.generera_html_footer())
            temp_path = f.name

        # Öppna i webbläsare
        webbrowser.open('file://' + temp_path)
        messagebox.showinfo("Utskrift",
                           "Utskrift öppnad i webbläsare.\n\n"
                           "Använd webbläsarens utskriftsfunktion (Ctrl+P / Cmd+P) för att skriva ut.")

    @staticmethod
    def skriv_ut_foremal(foremal, foton=None):
        """Generera HTML för ett föremål"""
        def format_matt(l, b, h):
            matt = []
            if l: matt.append(f"{l}")
            if b: matt.append(f"{b}")
            if h: matt.append(f"{h}")
            return " × ".join(matt) + " cm" if matt else "Ej angivet"

        def bild_till_base64(bildsokvag):
            """Konvertera bild till base64 för inbäddning i HTML"""
            try:
                if os.path.exists(bildsokvag):
                    # Öppna och skala ner bild för bättre prestanda
                    img = Image.open(bildsokvag)
                    # Skala ner till max 800px bred
                    max_width = 800
                    if img.width > max_width:
                        ratio = max_width / img.width
                        new_height = int(img.height * ratio)
                        img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                    # Konvertera till bytes
                    import io
                    buffer = io.BytesIO()
                    img_format = img.format if img.format else 'JPEG'
                    img.save(buffer, format=img_format)
                    img_bytes = buffer.getvalue()

                    # Konvertera till base64
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    mime_type = f"image/{img_format.lower()}"
                    return f"data:{mime_type};base64,{img_base64}"
            except Exception as e:
                print(f"Fel vid konvertering av bild: {e}")
            return None

        html = f"""
<h1>Föremålsinformation</h1>

<div class="info-section">
    <p><span class="label">ID:</span> {foremal['id']}</p>
    <p><span class="label">Accessionsnummer:</span> {foremal['accessionsnummer']}</p>
    <p><span class="label">Namn:</span> {foremal['namn']}</p>
</div>

<h2>Beskrivning</h2>
<div class="info-section">
    <p>{foremal['beskrivning'] if foremal['beskrivning'] else 'Ingen beskrivning'}</p>
</div>
"""

        # Lägg till bilder om det finns några
        if foton and len(foton) > 0:
            html += """
<h2>Bilder</h2>
<div class="info-section" style="text-align: center;">
"""
            for foto in foton:
                img_data = bild_till_base64(foto['filsokvag'])
                if img_data:
                    filnamn = Path(foto['filsokvag']).name
                    html += f"""
    <div style="margin: 20px 0; page-break-inside: avoid;">
        <img src="{img_data}" style="max-width: 100%; height: auto; border: 1px solid #ddd; padding: 5px;">
        <p style="font-size: 0.9em; color: #666; margin-top: 5px;">{filnamn}</p>
    </div>
"""
            html += """
</div>
"""

        html += f"""
<h2>Klassificering</h2>
<div class="info-section">
    <p><span class="label">Kategori:</span> {foremal['kategori_namn'] if foremal['kategori_namn'] else 'Ej angiven'}</p>
    <p><span class="label">Material:</span> {foremal['material'] if foremal['material'] else 'Ej angivet'}</p>
</div>

<h2>Tillverkning</h2>
<div class="info-section">
    <p><span class="label">År:</span> {foremal['tillverkningsar'] if foremal['tillverkningsar'] else 'Okänt'}</p>
    <p><span class="label">Plats:</span> {foremal['tillverkningsplats'] if foremal['tillverkningsplats'] else 'Okänd'}</p>
    <p><span class="label">Tillverkare:</span> {foremal['tillverkare'] if foremal['tillverkare'] else 'Okänd'}</p>
</div>

<h2>Fysiska egenskaper</h2>
<div class="info-section">
    <p><span class="label">Mått (L×B×H):</span> {format_matt(foremal['matt_langd'], foremal['matt_bredd'], foremal['matt_hojd'])}</p>
    <p><span class="label">Vikt:</span> {foremal['vikt'] if foremal['vikt'] else 'Ej angivet'} {'g' if foremal['vikt'] else ''}</p>
    <p><span class="label">Skick:</span> {foremal['skick'] if foremal['skick'] else 'Ej angivet'}</p>
</div>

<h2>Förvaring</h2>
<div class="info-section">
    <p><span class="label">Byggnad:</span> {foremal['byggnad'] if foremal['byggnad'] else 'Ej angiven'}</p>
    <p><span class="label">Rum:</span> {foremal['rum'] if foremal['rum'] else 'Ej angivet'}</p>
    <p><span class="label">Hylla/Sektion:</span> {foremal['hylla_sektion'] if foremal['hylla_sektion'] else 'Ej angivet'}</p>
</div>

<h2>Registrering</h2>
<div class="info-section">
    <p><span class="label">Datum:</span> {foremal['datum_registrerat']}</p>
    <p><span class="label">Registrerad av:</span> {foremal['registrerad_av'] if foremal['registrerad_av'] else 'Okänd'}</p>
</div>
"""
        return html

    @staticmethod
    def skriv_ut_foremalslista(foremalslista):
        """Generera HTML för lista av föremål"""
        html = f"""
<h1>Föremålslista</h1>
<p>Antal föremål: {len(foremalslista)}</p>

<table>
    <thead>
        <tr>
            <th>Acc.nr</th>
            <th>Namn</th>
            <th>Kategori</th>
            <th>Material</th>
            <th>Plats</th>
        </tr>
    </thead>
    <tbody>
"""
        for foremal in foremalslista:
            plats_str = foremal['byggnad'] if foremal['byggnad'] else ""
            if foremal['rum']:
                plats_str += f" - {foremal['rum']}"

            html += f"""
        <tr>
            <td>{foremal['accessionsnummer']}</td>
            <td>{foremal['namn']}</td>
            <td>{foremal['kategori_namn'] if foremal['kategori_namn'] else ''}</td>
            <td>{foremal['material'] if foremal['material'] else ''}</td>
            <td>{plats_str}</td>
        </tr>
"""
        html += """
    </tbody>
</table>
"""
        return html

    @staticmethod
    def skriv_ut_statistik(stats):
        """Generera HTML för statistik"""
        html = f"""
<h1>Museistatistik</h1>

<div class="info-section">
    <h2>Totalt antal föremål: {stats['totalt']}</h2>
</div>

<h2>Fördelning per kategori</h2>
<table>
    <thead>
        <tr>
            <th>Kategori</th>
            <th>Antal</th>
        </tr>
    </thead>
    <tbody>
"""
        for kat in stats['per_kategori']:
            if kat[1] > 0:
                html += f"""
        <tr>
            <td>{kat[0]}</td>
            <td>{kat[1]}</td>
        </tr>
"""
        html += """
    </tbody>
</table>

<h2>Senaste registreringar</h2>
<table>
    <thead>
        <tr>
            <th>Accessionsnummer</th>
            <th>Namn</th>
            <th>Datum</th>
        </tr>
    </thead>
    <tbody>
"""
        for foremal in stats['senaste']:
            html += f"""
        <tr>
            <td>{foremal['accessionsnummer']}</td>
            <td>{foremal['namn']}</td>
            <td>{foremal['datum_registrerat']}</td>
        </tr>
"""
        html += """
    </tbody>
</table>
"""
        return html

    @staticmethod
    def skriv_ut_platslista(platser):
        """Generera HTML för platslista"""
        html = f"""
<h1>Platslista</h1>
<p>Antal platser: {len(platser)}</p>

<table>
    <thead>
        <tr>
            <th>Byggnad</th>
            <th>Rum</th>
            <th>Hylla/Sektion</th>
        </tr>
    </thead>
    <tbody>
"""
        for plats in platser:
            html += f"""
        <tr>
            <td>{plats['byggnad']}</td>
            <td>{plats['rum'] if plats['rum'] else '-'}</td>
            <td>{plats['hylla_sektion'] if plats['hylla_sektion'] else '-'}</td>
        </tr>
"""
        html += """
    </tbody>
</table>
"""
        return html

    @staticmethod
    def skriv_ut_kategorilista(kategorier):
        """Generera HTML för kategorilista"""
        html = f"""
<h1>Kategorilista</h1>
<p>Antal kategorier: {len(kategorier)}</p>

<table>
    <thead>
        <tr>
            <th>Kategori</th>
        </tr>
    </thead>
    <tbody>
"""
        for kat in kategorier:
            html += f"""
        <tr>
            <td>{kat['namn']}</td>
        </tr>
"""
        html += """
    </tbody>
</table>
"""
        return html

    @staticmethod
    def skriv_ut_givarlista(givare):
        """Generera HTML för givarlista"""
        html = f"""
<h1>Givarlista</h1>
<p>Antal givare: {len(givare)}</p>

<table>
    <thead>
        <tr>
            <th>Namn</th>
            <th>Adress</th>
            <th>Telefon</th>
            <th>E-post</th>
            <th>Anteckningar</th>
        </tr>
    </thead>
    <tbody>
"""
        for givare_rad in givare:
            html += f"""
        <tr>
            <td>{givare_rad['namn']}</td>
            <td>{givare_rad['adress'] if givare_rad['adress'] else '-'}</td>
            <td>{givare_rad['telefon'] if givare_rad['telefon'] else '-'}</td>
            <td>{givare_rad['epost'] if givare_rad['epost'] else '-'}</td>
            <td>{givare_rad['anteckningar'] if givare_rad['anteckningar'] else '-'}</td>
        </tr>
"""
        html += """
    </tbody>
</table>
"""
        return html


class MuseumGUI:
    """Huvudfönster för museidatabasen"""

    def __init__(self, root):
        self.root = root
        self.root.title("Hembygdsmuseum - Föremålsdatabas")
        self.root.geometry("1200x800")

        self.db = MuseumDB()

        # Lista för att hålla bilder som ska läggas till
        self.bilder_att_lagga_till = []

        # Skapa images-mapp om den inte finns
        self.images_dir = Path("images")
        self.images_dir.mkdir(exist_ok=True)

        # Skapa menyfält
        self.skapa_meny()

        # Skapa flikvy
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Skapa flikar
        self.skapa_registrera_flik()
        self.skapa_sok_flik()
        self.skapa_kategorier_flik()
        self.skapa_platser_flik()
        self.skapa_givare_flik()
        self.skapa_statistik_flik()

    def skapa_meny(self):
        """Skapa menyraden"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Arkiv-meny
        arkiv_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arkiv", menu=arkiv_menu)
        arkiv_menu.add_command(label="Backup databas", command=self.backup_databas)
        arkiv_menu.add_separator()
        arkiv_menu.add_command(label="Avsluta", command=self.root.quit)

        # Skriv ut-meny
        skriv_ut_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Skriv ut", menu=skriv_ut_menu)
        skriv_ut_menu.add_command(label="Skriv ut valt föremål", command=self.skriv_ut_valt_foremal)
        skriv_ut_menu.add_command(label="Skriv ut föremålslista", command=self.skriv_ut_foremalslista)
        skriv_ut_menu.add_separator()
        skriv_ut_menu.add_command(label="Skriv ut statistik", command=self.skriv_ut_statistik)
        skriv_ut_menu.add_command(label="Skriv ut platslista", command=self.skriv_ut_platslista)
        skriv_ut_menu.add_command(label="Skriv ut kategorilista", command=self.skriv_ut_kategorilista)
        skriv_ut_menu.add_command(label="Skriv ut givarlista", command=self.skriv_ut_givarlista)

        # Hjälp-meny
        hjalp_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Hjälp", menu=hjalp_menu)
        hjalp_menu.add_command(label="Om programmet", command=self.visa_om)

    def skapa_registrera_flik(self):
        """Flik för att registrera nya föremål"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Registrera föremål")

        # Skapa scrollbar
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Formulärfält
        row = 0

        # Accessionsnummer
        ttk.Label(scrollable_frame, text="Accessionsnummer*:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.acc_nr_entry = ttk.Entry(scrollable_frame, width=30)
        self.acc_nr_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(scrollable_frame, text="Generera", command=self.generera_accnr).grid(row=row, column=2, padx=5)
        row += 1

        # Namn
        ttk.Label(scrollable_frame, text="Namn*:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.namn_entry = ttk.Entry(scrollable_frame, width=50)
        self.namn_entry.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Beskrivning
        ttk.Label(scrollable_frame, text="Beskrivning:").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=5)
        self.beskrivning_text = tk.Text(scrollable_frame, width=50, height=5)
        self.beskrivning_text.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Kategori
        ttk.Label(scrollable_frame, text="Kategori:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.kategori_var = tk.StringVar()
        self.kategori_combo = ttk.Combobox(scrollable_frame, textvariable=self.kategori_var, width=30)
        self.kategori_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        self.uppdatera_kategori_lista()
        row += 1

        # Material
        ttk.Label(scrollable_frame, text="Material:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.material_entry = ttk.Entry(scrollable_frame, width=30)
        self.material_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Tillverkningsår
        ttk.Label(scrollable_frame, text="Tillverkningsår:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.tillv_ar_entry = ttk.Entry(scrollable_frame, width=30)
        self.tillv_ar_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Tillverkningsplats
        ttk.Label(scrollable_frame, text="Tillverkningsplats:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.tillv_plats_entry = ttk.Entry(scrollable_frame, width=30)
        self.tillv_plats_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Tillverkare
        ttk.Label(scrollable_frame, text="Tillverkare:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.tillverkare_entry = ttk.Entry(scrollable_frame, width=30)
        self.tillverkare_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Mått
        ttk.Label(scrollable_frame, text="Mått (cm):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        matt_frame = ttk.Frame(scrollable_frame)
        matt_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(matt_frame, text="L:").pack(side=tk.LEFT)
        self.matt_l_entry = ttk.Entry(matt_frame, width=10)
        self.matt_l_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(matt_frame, text="B:").pack(side=tk.LEFT, padx=(10,0))
        self.matt_b_entry = ttk.Entry(matt_frame, width=10)
        self.matt_b_entry.pack(side=tk.LEFT, padx=2)

        ttk.Label(matt_frame, text="H:").pack(side=tk.LEFT, padx=(10,0))
        self.matt_h_entry = ttk.Entry(matt_frame, width=10)
        self.matt_h_entry.pack(side=tk.LEFT, padx=2)
        row += 1

        # Vikt
        ttk.Label(scrollable_frame, text="Vikt (g):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.vikt_entry = ttk.Entry(scrollable_frame, width=30)
        self.vikt_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Skick
        ttk.Label(scrollable_frame, text="Skick:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.skick_var = tk.StringVar(value="Gott")
        skick_frame = ttk.Frame(scrollable_frame)
        skick_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Radiobutton(skick_frame, text="Utmärkt", variable=self.skick_var, value="Utmärkt").pack(side=tk.LEFT)
        ttk.Radiobutton(skick_frame, text="Gott", variable=self.skick_var, value="Gott").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(skick_frame, text="Dåligt", variable=self.skick_var, value="Dåligt").pack(side=tk.LEFT)
        row += 1

        # Placering
        ttk.Label(scrollable_frame, text="Placering:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.placering_var = tk.StringVar()
        self.placering_combo = ttk.Combobox(scrollable_frame, textvariable=self.placering_var, width=30)
        self.placering_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        self.uppdatera_plats_lista()
        row += 1

        # Registrerad av
        ttk.Label(scrollable_frame, text="Registrerad av:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.reg_av_entry = ttk.Entry(scrollable_frame, width=30)
        self.reg_av_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1

        # Bilder
        ttk.Label(scrollable_frame, text="Bilder:").grid(row=row, column=0, sticky=tk.NW, padx=5, pady=5)
        bild_frame = ttk.Frame(scrollable_frame)
        bild_frame.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)

        ttk.Button(bild_frame, text="Lägg till bild", command=self.lagg_till_bild_registrering).pack(side=tk.LEFT, padx=5)
        ttk.Button(bild_frame, text="Visa bilder", command=self.visa_valda_bilder).pack(side=tk.LEFT, padx=5)

        self.antal_bilder_label = ttk.Label(bild_frame, text="(0 bilder)")
        self.antal_bilder_label.pack(side=tk.LEFT, padx=5)
        row += 1

        # Knappar
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)

        ttk.Button(button_frame, text="Spara föremål", command=self.spara_foremal).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Rensa formulär", command=self.rensa_formular).pack(side=tk.LEFT, padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def skapa_sok_flik(self):
        """Flik för att söka och visa föremål"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Sök föremål")

        # Sökfält
        sok_frame = ttk.LabelFrame(frame, text="Sök", padding=10)
        sok_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(sok_frame, text="Sökterm:").grid(row=0, column=0, padx=5)
        self.sokterm_entry = ttk.Entry(sok_frame, width=40)
        self.sokterm_entry.grid(row=0, column=1, padx=5)

        ttk.Label(sok_frame, text="Kategori:").grid(row=0, column=2, padx=5)
        self.sok_kategori_var = tk.StringVar(value="Alla")
        self.sok_kategori_combo = ttk.Combobox(sok_frame, textvariable=self.sok_kategori_var, width=20)
        self.sok_kategori_combo.grid(row=0, column=3, padx=5)
        self.uppdatera_sok_kategori_lista()

        ttk.Button(sok_frame, text="Sök", command=self.sok_foremal).grid(row=0, column=4, padx=5)
        ttk.Button(sok_frame, text="Visa alla", command=self.visa_alla_foremal).grid(row=0, column=5, padx=5)

        # Resultatträd
        resultat_frame = ttk.Frame(frame)
        resultat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(resultat_frame)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        tree_scroll_x = ttk.Scrollbar(resultat_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        self.resultat_tree = ttk.Treeview(
            resultat_frame,
            columns=("acc", "namn", "kategori", "material", "plats"),
            show="tree headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set
        )

        self.resultat_tree.heading("#0", text="ID")
        self.resultat_tree.heading("acc", text="Acc.nr")
        self.resultat_tree.heading("namn", text="Namn")
        self.resultat_tree.heading("kategori", text="Kategori")
        self.resultat_tree.heading("material", text="Material")
        self.resultat_tree.heading("plats", text="Plats")

        self.resultat_tree.column("#0", width=50)
        self.resultat_tree.column("acc", width=120)
        self.resultat_tree.column("namn", width=250)
        self.resultat_tree.column("kategori", width=150)
        self.resultat_tree.column("material", width=150)
        self.resultat_tree.column("plats", width=200)

        tree_scroll_y.config(command=self.resultat_tree.yview)
        tree_scroll_x.config(command=self.resultat_tree.xview)

        self.resultat_tree.pack(fill=tk.BOTH, expand=True)

        # Dubbelklick för att visa detaljer
        self.resultat_tree.bind("<Double-1>", self.visa_foremal_detaljer)

        # Knappar för att visa detaljer och skriva ut
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=5)
        ttk.Button(button_frame, text="Visa detaljer", command=lambda: self.visa_foremal_detaljer(None)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skriv ut valt föremål", command=self.skriv_ut_valt_foremal).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skriv ut lista", command=self.skriv_ut_foremalslista).pack(side=tk.LEFT, padx=5)

    def skapa_kategorier_flik(self):
        """Flik för att hantera kategorier"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Kategorier")

        # Lägg till ny kategori
        input_frame = ttk.LabelFrame(frame, text="Lägg till ny kategori", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="Kategorinamn:").pack(side=tk.LEFT, padx=5)
        self.ny_kategori_entry = ttk.Entry(input_frame, width=30)
        self.ny_kategori_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="Lägg till", command=self.lagg_till_kategori).pack(side=tk.LEFT, padx=5)

        # Lista befintliga kategorier
        list_frame = ttk.LabelFrame(frame, text="Befintliga kategorier", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.kategori_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=20)
        self.kategori_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.kategori_listbox.yview)

        # Knapp för att skriva ut kategorilista
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Skriv ut kategorilista", command=self.skriv_ut_kategorilista).pack()

        self.uppdatera_kategori_listbox()

    def skapa_platser_flik(self):
        """Flik för att hantera förvaringsplatser"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Platser")

        # Lägg till ny plats
        input_frame = ttk.LabelFrame(frame, text="Lägg till ny plats", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="Byggnad:").grid(row=0, column=0, padx=5, pady=5)
        self.plats_byggnad_entry = ttk.Entry(input_frame, width=25)
        self.plats_byggnad_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Rum:").grid(row=0, column=2, padx=5, pady=5)
        self.plats_rum_entry = ttk.Entry(input_frame, width=25)
        self.plats_rum_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text="Hylla/Sektion:").grid(row=1, column=0, padx=5, pady=5)
        self.plats_hylla_entry = ttk.Entry(input_frame, width=25)
        self.plats_hylla_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="Lägg till plats", command=self.lagg_till_plats).grid(row=1, column=2, columnspan=2, padx=5, pady=5)

        # Lista befintliga platser
        list_frame = ttk.LabelFrame(frame, text="Befintliga platser", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.plats_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=20)
        self.plats_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.plats_listbox.yview)

        # Knappar för att ta bort och skriva ut
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Ta bort vald plats", command=self.ta_bort_vald_plats).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skriv ut platslista", command=self.skriv_ut_platslista).pack(side=tk.LEFT, padx=5)

        self.uppdatera_plats_listbox()

    def skapa_givare_flik(self):
        """Flik för att hantera givare"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Givare")

        # Lägg till ny givare
        input_frame = ttk.LabelFrame(frame, text="Lägg till ny givare", padding=10)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(input_frame, text="Namn:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.givare_namn_entry = ttk.Entry(input_frame, width=40)
        self.givare_namn_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Adress:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.givare_adress_entry = ttk.Entry(input_frame, width=40)
        self.givare_adress_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Telefon:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.givare_telefon_entry = ttk.Entry(input_frame, width=40)
        self.givare_telefon_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="E-post:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.givare_epost_entry = ttk.Entry(input_frame, width=40)
        self.givare_epost_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Anteckningar:").grid(row=4, column=0, sticky=tk.NW, padx=5, pady=5)
        self.givare_anteckningar_text = tk.Text(input_frame, width=40, height=4)
        self.givare_anteckningar_text.grid(row=4, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="Lägg till givare", command=self.lagg_till_givare).grid(row=5, column=0, columnspan=2, pady=10)

        # Lista befintliga givare
        list_frame = ttk.LabelFrame(frame, text="Befintliga givare", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.givare_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=15)
        self.givare_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.givare_listbox.yview)

        # Knapp för att skriva ut givarlista
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Skriv ut givarlista", command=self.skriv_ut_givarlista).pack()

        self.uppdatera_givare_listbox()

    def skapa_statistik_flik(self):
        """Flik för att visa statistik"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Statistik")

        # Knappar för att uppdatera och skriva ut statistik
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Uppdatera statistik", command=self.uppdatera_statistik).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Skriv ut statistik", command=self.skriv_ut_statistik).pack(side=tk.LEFT, padx=5)

        # Text widget för statistik
        self.statistik_text = tk.Text(frame, wrap=tk.WORD, height=30)
        self.statistik_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame, command=self.statistik_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.statistik_text.config(yscrollcommand=scrollbar.set)

        # Visa initial statistik
        self.uppdatera_statistik()

    def lagg_till_bild_registrering(self):
        """Lägg till bild vid registrering"""
        filetypes = [
            ("Bilderfiler", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("Alla filer", "*.*")
        ]

        filenames = filedialog.askopenfilenames(
            title="Välj bilder",
            filetypes=filetypes
        )

        if filenames:
            for filename in filenames:
                if filename not in self.bilder_att_lagga_till:
                    self.bilder_att_lagga_till.append(filename)

            self.antal_bilder_label.config(text=f"({len(self.bilder_att_lagga_till)} bilder)")

    def visa_valda_bilder(self):
        """Visa lista över valda bilder"""
        if not self.bilder_att_lagga_till:
            messagebox.showinfo("Info", "Inga bilder valda ännu")
            return

        # Skapa fönster
        bild_window = tk.Toplevel(self.root)
        bild_window.title("Valda bilder")
        bild_window.geometry("400x300")

        # Lista
        scrollbar = ttk.Scrollbar(bild_window)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(bild_window, yscrollcommand=scrollbar.set)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.config(command=listbox.yview)

        for bild in self.bilder_att_lagga_till:
            listbox.insert(tk.END, Path(bild).name)

        # Knapp för att ta bort bild
        def ta_bort_vald():
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                self.bilder_att_lagga_till.pop(idx)
                listbox.delete(idx)
                self.antal_bilder_label.config(text=f"({len(self.bilder_att_lagga_till)} bilder)")

        ttk.Button(bild_window, text="Ta bort vald", command=ta_bort_vald).pack(pady=5)
        ttk.Button(bild_window, text="Stäng", command=bild_window.destroy).pack(pady=5)

    def generera_accnr(self):
        """Generera nästa accessionsnummer"""
        ar = datetime.now().year
        # Hitta högsta numret för detta år
        sokresultat = self.db.sok_foremal(sokterm=str(ar))
        max_nr = 0
        prefix = f"{ar}."

        for row in sokresultat:
            acc = row['accessionsnummer']
            if acc.startswith(prefix):
                try:
                    nr = int(acc.split('.')[-1])
                    max_nr = max(max_nr, nr)
                except ValueError:
                    pass

        nasta_nr = max_nr + 1
        nytt_acc = f"{ar}.{nasta_nr:03d}"
        self.acc_nr_entry.delete(0, tk.END)
        self.acc_nr_entry.insert(0, nytt_acc)

    def spara_foremal(self):
        """Spara nytt föremål"""
        # Validera obligatoriska fält
        if not self.acc_nr_entry.get():
            messagebox.showerror("Fel", "Accessionsnummer måste anges!")
            return

        if not self.namn_entry.get():
            messagebox.showerror("Fel", "Namn måste anges!")
            return

        # Hämta kategori-id
        kategori_id = None
        kategori_namn = self.kategori_var.get()
        if kategori_namn:
            kategorier = self.db.hamta_kategorier()
            for kat in kategorier:
                if kat['namn'] == kategori_namn:
                    kategori_id = kat['id']
                    break

        # Hämta plats-id
        placering_id = None
        plats_text = self.placering_var.get()
        if plats_text:
            platser = self.db.hamta_platser()
            for plats in platser:
                plats_str = f"{plats['byggnad']}"
                if plats['rum']:
                    plats_str += f" - {plats['rum']}"
                if plats['hylla_sektion']:
                    plats_str += f" - {plats['hylla_sektion']}"
                if plats_str == plats_text:
                    placering_id = plats['id']
                    break

        # Konvertera numeriska värden
        def safe_float(val):
            try:
                return float(val) if val else None
            except ValueError:
                return None

        # Samla data
        data = (
            self.acc_nr_entry.get(),
            self.namn_entry.get(),
            self.beskrivning_text.get("1.0", tk.END).strip(),
            kategori_id,
            self.material_entry.get(),
            self.tillv_ar_entry.get(),
            self.tillv_plats_entry.get(),
            self.tillverkare_entry.get(),
            safe_float(self.matt_l_entry.get()),
            safe_float(self.matt_b_entry.get()),
            safe_float(self.matt_h_entry.get()),
            safe_float(self.vikt_entry.get()),
            self.skick_var.get(),
            placering_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self.reg_av_entry.get()
        )

        try:
            foremal_id = self.db.lagg_till_foremal(data)

            # Spara bilder om några valts
            if self.bilder_att_lagga_till:
                for bild_path in self.bilder_att_lagga_till:
                    try:
                        # Kopiera bild till images-mapp
                        original_name = Path(bild_path).name
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        new_name = f"{foremal_id}_{timestamp}_{original_name}"
                        destination = self.images_dir / new_name

                        shutil.copy2(bild_path, destination)

                        # Spara i databasen
                        self.db.lagg_till_foto(foremal_id, str(destination))
                    except Exception as e:
                        messagebox.showwarning("Varning", f"Kunde inte spara bild {original_name}: {str(e)}")

            antal_bilder = len(self.bilder_att_lagga_till)
            messagebox.showinfo("Sparat", f"Föremål sparat med ID: {foremal_id}\n{antal_bilder} bilder tillagda")
            self.rensa_formular()
            self.generera_accnr()  # Förbereda nästa nummer
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Fel", f"Accessionsnummer finns redan!")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara: {str(e)}")

    def rensa_formular(self):
        """Rensa registreringsformuläret"""
        self.acc_nr_entry.delete(0, tk.END)
        self.namn_entry.delete(0, tk.END)
        self.beskrivning_text.delete("1.0", tk.END)
        self.kategori_var.set("")
        self.material_entry.delete(0, tk.END)
        self.tillv_ar_entry.delete(0, tk.END)
        self.tillv_plats_entry.delete(0, tk.END)
        self.tillverkare_entry.delete(0, tk.END)
        self.matt_l_entry.delete(0, tk.END)
        self.matt_b_entry.delete(0, tk.END)
        self.matt_h_entry.delete(0, tk.END)
        self.vikt_entry.delete(0, tk.END)
        self.skick_var.set("Gott")
        self.placering_var.set("")
        self.reg_av_entry.delete(0, tk.END)
        self.bilder_att_lagga_till = []
        self.antal_bilder_label.config(text="(0 bilder)")

    def uppdatera_kategori_lista(self):
        """Uppdatera kategorilistan i combobox"""
        kategorier = self.db.hamta_kategorier()
        kategori_namn = [kat['namn'] for kat in kategorier]
        self.kategori_combo['values'] = kategori_namn

    def uppdatera_plats_lista(self):
        """Uppdatera platslistan i combobox"""
        platser = self.db.hamta_platser()
        plats_lista = []
        for plats in platser:
            plats_str = f"{plats['byggnad']}"
            if plats['rum']:
                plats_str += f" - {plats['rum']}"
            if plats['hylla_sektion']:
                plats_str += f" - {plats['hylla_sektion']}"
            plats_lista.append(plats_str)
        self.placering_combo['values'] = plats_lista

    def uppdatera_sok_kategori_lista(self):
        """Uppdatera kategorilistan för sökning"""
        kategorier = self.db.hamta_kategorier()
        kategori_namn = ["Alla"] + [kat['namn'] for kat in kategorier]
        self.sok_kategori_combo['values'] = kategori_namn

    def sok_foremal(self):
        """Sök efter föremål"""
        sokterm = self.sokterm_entry.get()
        kategori_namn = self.sok_kategori_var.get()

        kategori_id = None
        if kategori_namn and kategori_namn != "Alla":
            kategorier = self.db.hamta_kategorier()
            for kat in kategorier:
                if kat['namn'] == kategori_namn:
                    kategori_id = kat['id']
                    break

        resultat = self.db.sok_foremal(sokterm, kategori_id)
        self.visa_sokresultat(resultat)

    def visa_alla_foremal(self):
        """Visa alla föremål"""
        resultat = self.db.sok_foremal()
        self.visa_sokresultat(resultat)

    def visa_sokresultat(self, resultat):
        """Visa sökresultat i treeview"""
        # Rensa befintligt innehåll
        for item in self.resultat_tree.get_children():
            self.resultat_tree.delete(item)

        # Lägg till resultat
        for row in resultat:
            plats_str = row['byggnad'] if row['byggnad'] else ""
            if row['rum']:
                plats_str += f" - {row['rum']}"

            self.resultat_tree.insert(
                "",
                tk.END,
                text=str(row['id']),
                values=(
                    row['accessionsnummer'],
                    row['namn'],
                    row['kategori_namn'] if row['kategori_namn'] else "",
                    row['material'] if row['material'] else "",
                    plats_str
                )
            )

        # Visa antal resultat
        messagebox.showinfo("Sökresultat", f"Hittade {len(resultat)} föremål")

    def visa_foremal_detaljer(self, event):
        """Visa detaljer för valt föremål"""
        selection = self.resultat_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj ett föremål först!")
            return

        item = self.resultat_tree.item(selection[0])
        foremal_id = int(item['text'])

        foremal = self.db.hamta_foremal(foremal_id)
        foton = self.db.hamta_foton(foremal_id)

        # Skapa detaljfönster
        detalj_window = tk.Toplevel(self.root)
        detalj_window.title(f"Föremål: {foremal['namn']}")
        detalj_window.geometry("800x900")

        # Lista för att spara bildreferenser (viktigt för att bilderna ska visas)
        detalj_window.image_references = []

        # Skapa textwidget med scrollbar
        text_frame = ttk.Frame(detalj_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)

        # Formatera och visa information
        info = f"""
╔══════════════════════════════════════════════════════════════╗
                        FÖREMÅLSINFORMATION
╚══════════════════════════════════════════════════════════════╝

ID:                    {foremal['id']}
Accessionsnummer:      {foremal['accessionsnummer']}
Namn:                  {foremal['namn']}

Beskrivning:
{foremal['beskrivning'] if foremal['beskrivning'] else 'Ingen beskrivning'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KLASSIFICERING:
Kategori:              {foremal['kategori_namn'] if foremal['kategori_namn'] else 'Ej angiven'}
Material:              {foremal['material'] if foremal['material'] else 'Ej angivet'}

TILLVERKNING:
År:                    {foremal['tillverkningsar'] if foremal['tillverkningsar'] else 'Okänt'}
Plats:                 {foremal['tillverkningsplats'] if foremal['tillverkningsplats'] else 'Okänd'}
Tillverkare:           {foremal['tillverkare'] if foremal['tillverkare'] else 'Okänd'}

FYSISKA EGENSKAPER:
Mått (L×B×H):          {self.format_matt(foremal['matt_langd'], foremal['matt_bredd'], foremal['matt_hojd'])}
Vikt:                  {foremal['vikt'] if foremal['vikt'] else 'Ej angivet'} {'g' if foremal['vikt'] else ''}
Skick:                 {foremal['skick'] if foremal['skick'] else 'Ej angivet'}

FÖRVARING:
Byggnad:               {foremal['byggnad'] if foremal['byggnad'] else 'Ej angiven'}
Rum:                   {foremal['rum'] if foremal['rum'] else 'Ej angivet'}
Hylla/Sektion:         {foremal['hylla_sektion'] if foremal['hylla_sektion'] else 'Ej angivet'}

REGISTRERING:
Datum:                 {foremal['datum_registrerat']}
Registrerad av:        {foremal['registrerad_av'] if foremal['registrerad_av'] else 'Okänd'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        text.insert("1.0", info)
        text.config(state=tk.DISABLED)

        # Bildsektion
        if foton:
            bild_frame = ttk.LabelFrame(detalj_window, text=f"Bilder ({len(foton)} st)", padding=10)
            bild_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            # Skapa canvas med scrollbar för bilder
            canvas = tk.Canvas(bild_frame, height=200)
            scrollbar = ttk.Scrollbar(bild_frame, orient="horizontal", command=canvas.xview)
            scrollable_bild_frame = ttk.Frame(canvas)

            scrollable_bild_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_bild_frame, anchor="nw")
            canvas.configure(xscrollcommand=scrollbar.set)

            # Visa miniatyrer
            col = 0
            for foto in foton:
                try:
                    # Ladda och skala bild
                    img_path = foto['filsokvag']
                    if os.path.exists(img_path):
                        img = Image.open(img_path)
                        img.thumbnail((150, 150))
                        photo = ImageTk.PhotoImage(img)

                        # Spara referens i fönstrets lista (kritiskt för att bilden ska visas!)
                        detalj_window.image_references.append(photo)

                        # Skapa frame för varje bild
                        img_container = ttk.Frame(scrollable_bild_frame)
                        img_container.grid(row=0, column=col, padx=5, pady=5)

                        # Bild
                        img_label = tk.Label(img_container, image=photo)
                        img_label.image = photo  # Behåll referens på labeln
                        img_label.pack()

                        # Klick för att visa fullstorlek
                        img_label.bind("<Button-1>", lambda e, path=img_path: self.visa_bild_fullstorlek(path))

                        # Filnamn
                        ttk.Label(img_container, text=Path(img_path).name, wraplength=150).pack()

                        col += 1
                    else:
                        # Bildfil saknas
                        img_container = ttk.Frame(scrollable_bild_frame)
                        img_container.grid(row=0, column=col, padx=5, pady=5)
                        ttk.Label(img_container, text="Bild saknas", foreground="red").pack()
                        col += 1

                except Exception as e:
                    print(f"Fel vid laddning av bild: {e}")

            canvas.pack(side="top", fill="both", expand=True)
            scrollbar.pack(side="bottom", fill="x")

            # Knapp för att lägga till fler bilder
            ttk.Button(bild_frame, text="Lägg till fler bilder",
                      command=lambda: self.lagg_till_bild_till_foremal(foremal_id, detalj_window)).pack(pady=5)
        else:
            # Ingen bild finns
            bild_frame = ttk.LabelFrame(detalj_window, text="Bilder", padding=10)
            bild_frame.pack(fill=tk.X, padx=10, pady=5)
            ttk.Label(bild_frame, text="Inga bilder registrerade").pack()
            ttk.Button(bild_frame, text="Lägg till bilder",
                      command=lambda: self.lagg_till_bild_till_foremal(foremal_id, detalj_window)).pack(pady=5)

        # Stäng-knapp
        ttk.Button(detalj_window, text="Stäng", command=detalj_window.destroy).pack(pady=10)

    def visa_bild_fullstorlek(self, img_path):
        """Visa bild i fullstorlek"""
        bild_window = tk.Toplevel(self.root)
        bild_window.title(Path(img_path).name)

        try:
            # Ladda bild
            img = Image.open(img_path)

            # Skala ner om bilden är för stor
            max_width = 1000
            max_height = 800
            img.thumbnail((max_width, max_height))

            photo = ImageTk.PhotoImage(img)

            # Visa bild
            label = tk.Label(bild_window, image=photo)
            label.image = photo  # Behåll referens
            label.pack()

            # Stäng-knapp
            ttk.Button(bild_window, text="Stäng", command=bild_window.destroy).pack(pady=5)

        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte visa bild: {str(e)}")
            bild_window.destroy()

    def lagg_till_bild_till_foremal(self, foremal_id, parent_window):
        """Lägg till bild till ett befintligt föremål"""
        filetypes = [
            ("Bilderfiler", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("Alla filer", "*.*")
        ]

        filenames = filedialog.askopenfilenames(
            title="Välj bilder",
            filetypes=filetypes
        )

        if filenames:
            antal_tillagda = 0
            for filename in filenames:
                try:
                    # Kopiera bild till images-mapp
                    original_name = Path(filename).name
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    new_name = f"{foremal_id}_{timestamp}_{original_name}"
                    destination = self.images_dir / new_name

                    shutil.copy2(filename, destination)

                    # Spara i databasen
                    self.db.lagg_till_foto(foremal_id, str(destination))
                    antal_tillagda += 1

                except Exception as e:
                    messagebox.showwarning("Varning", f"Kunde inte spara bild {original_name}: {str(e)}")

            if antal_tillagda > 0:
                messagebox.showinfo("Sparat", f"{antal_tillagda} bilder tillagda")
                # Stäng och öppna detaljfönstret igen för att visa nya bilder
                parent_window.destroy()
                # Simulera att användaren har valt föremålet igen
                # Detta är lite av en workaround, men fungerar

    def format_matt(self, l, b, h):
        """Formatera måttangivelser"""
        matt = []
        if l:
            matt.append(f"{l}")
        if b:
            matt.append(f"{b}")
        if h:
            matt.append(f"{h}")

        if matt:
            return " × ".join(matt) + " cm"
        return "Ej angivet"

    def lagg_till_kategori(self):
        """Lägg till ny kategori"""
        namn = self.ny_kategori_entry.get().strip()
        if not namn:
            messagebox.showwarning("Varning", "Ange ett kategorinamn!")
            return

        try:
            self.db.lagg_till_kategori(namn)
            messagebox.showinfo("Sparat", f"Kategori '{namn}' tillagd!")
            self.ny_kategori_entry.delete(0, tk.END)
            self.uppdatera_kategori_listbox()
            self.uppdatera_kategori_lista()
            self.uppdatera_sok_kategori_lista()
        except sqlite3.IntegrityError:
            messagebox.showerror("Fel", "Kategorin finns redan!")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte lägga till kategori: {str(e)}")

    def uppdatera_kategori_listbox(self):
        """Uppdatera kategorilistan"""
        self.kategori_listbox.delete(0, tk.END)
        kategorier = self.db.hamta_kategorier()
        for kat in kategorier:
            self.kategori_listbox.insert(tk.END, f"{kat['id']}: {kat['namn']}")

    def lagg_till_plats(self):
        """Lägg till ny plats"""
        byggnad = self.plats_byggnad_entry.get().strip()
        rum = self.plats_rum_entry.get().strip()
        hylla = self.plats_hylla_entry.get().strip()

        if not byggnad:
            messagebox.showwarning("Varning", "Ange minst en byggnad!")
            return

        try:
            self.db.lagg_till_plats(byggnad, rum if rum else None, hylla if hylla else None)
            messagebox.showinfo("Sparat", "Plats tillagd!")
            self.plats_byggnad_entry.delete(0, tk.END)
            self.plats_rum_entry.delete(0, tk.END)
            self.plats_hylla_entry.delete(0, tk.END)
            self.uppdatera_plats_listbox()
            self.uppdatera_plats_lista()
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte lägga till plats: {str(e)}")

    def uppdatera_plats_listbox(self):
        """Uppdatera platslistan"""
        self.plats_listbox.delete(0, tk.END)
        platser = self.db.hamta_platser()
        # Lagra plats-ID:n för varje listbox-rad
        self.plats_id_mapping = {}
        for idx, plats in enumerate(platser):
            plats_str = f"{plats['byggnad']}"
            if plats['rum']:
                plats_str += f" - {plats['rum']}"
            if plats['hylla_sektion']:
                plats_str += f" ({plats['hylla_sektion']})"
            self.plats_listbox.insert(tk.END, plats_str)
            self.plats_id_mapping[idx] = plats['id']

    def ta_bort_vald_plats(self):
        """Ta bort vald plats från databasen"""
        selection = self.plats_listbox.curselection()
        if not selection:
            messagebox.showwarning("Varning", "Välj en plats att ta bort!")
            return

        # Hämta plats-id från mappningen
        selected_index = selection[0]
        plats_id = self.plats_id_mapping.get(selected_index)

        # Kontrollera om platsen används av föremål
        self.db.cursor.execute(
            "SELECT COUNT(*) FROM foremal WHERE placering_id = ?",
            (plats_id,)
        )
        antal_foremal = self.db.cursor.fetchone()[0]

        # Bekräfta borttagning
        if antal_foremal > 0:
            svar = messagebox.askyesno(
                "Bekräfta borttagning",
                f"Platsen används av {antal_foremal} föremål.\n\n"
                f"Om du tar bort platsen kommer dessa föremål att få sin placering borttagen.\n\n"
                f"Är du säker på att du vill ta bort platsen?"
            )
        else:
            svar = messagebox.askyesno(
                "Bekräfta borttagning",
                "Är du säker på att du vill ta bort denna plats?"
            )

        if svar:
            try:
                self.db.ta_bort_plats(plats_id)
                messagebox.showinfo("Borttagen", "Platsen har tagits bort!")
                self.uppdatera_plats_listbox()
                self.uppdatera_plats_lista()
            except Exception as e:
                messagebox.showerror("Fel", f"Kunde inte ta bort plats: {str(e)}")

    def lagg_till_givare(self):
        """Lägg till ny givare"""
        namn = self.givare_namn_entry.get().strip()
        if not namn:
            messagebox.showwarning("Varning", "Ange ett namn!")
            return

        adress = self.givare_adress_entry.get().strip()
        telefon = self.givare_telefon_entry.get().strip()
        epost = self.givare_epost_entry.get().strip()
        anteckningar = self.givare_anteckningar_text.get("1.0", tk.END).strip()

        try:
            self.db.lagg_till_givare(namn, adress, telefon, epost, anteckningar)
            messagebox.showinfo("Sparat", f"Givare '{namn}' tillagd!")
            self.givare_namn_entry.delete(0, tk.END)
            self.givare_adress_entry.delete(0, tk.END)
            self.givare_telefon_entry.delete(0, tk.END)
            self.givare_epost_entry.delete(0, tk.END)
            self.givare_anteckningar_text.delete("1.0", tk.END)
            self.uppdatera_givare_listbox()
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte lägga till givare: {str(e)}")

    def uppdatera_givare_listbox(self):
        """Uppdatera givarlistan"""
        self.givare_listbox.delete(0, tk.END)
        givare = self.db.hamta_givare()
        for g in givare:
            self.givare_listbox.insert(tk.END, f"{g['id']}: {g['namn']}")

    def uppdatera_statistik(self):
        """Uppdatera statistikvisning"""
        stats = self.db.hamta_statistik()

        self.statistik_text.config(state=tk.NORMAL)
        self.statistik_text.delete("1.0", tk.END)

        text = f"""
╔══════════════════════════════════════════════════════════════╗
                    MUSEISTATISTIK
╚══════════════════════════════════════════════════════════════╝

TOTALT ANTAL FÖREMÅL: {stats['totalt']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FÖRDELNING PER KATEGORI:

"""

        for kat in stats['per_kategori']:
            if kat[1] > 0:  # Visa bara kategorier med föremål
                text += f"  {kat[0]:<30} {kat[1]:>5} st\n"

        text += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SENASTE REGISTRERINGAR:

"""

        for foremal in stats['senaste']:
            text += f"  {foremal['accessionsnummer']:<15} {foremal['namn']:<40} ({foremal['datum_registrerat']})\n"

        text += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

        self.statistik_text.insert("1.0", text)
        self.statistik_text.config(state=tk.DISABLED)

    def backup_databas(self):
        """Skapa backup av databasen"""
        backup_dir = Path("backup")
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"hembygdsmuseum_backup_{timestamp}.db"

        try:
            shutil.copy2(self.db.db_path, backup_path)
            messagebox.showinfo("Backup", f"Backup skapad:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte skapa backup: {str(e)}")

    def visa_om(self):
        """Visa Om-dialog"""
        messagebox.showinfo(
            "Om Hembygdsmuseum",
            "Hembygdsmuseum - Föremålsdatabas v1.0\n\n"
            "Ett system för att registrera och hantera museiföremål.\n\n"
            "Skapad med Python, SQLite och Tkinter.\n"
            "© 2026"
        )

    # ========== UTSKRIFTSFUNKTIONER ==========

    def skriv_ut_valt_foremal(self):
        """Skriv ut information om valt föremål"""
        selection = self.resultat_tree.selection()
        if not selection:
            messagebox.showwarning("Varning", "Välj ett föremål först!\n\nGå till fliken 'Sök föremål' och välj ett föremål i listan.")
            return

        item = self.resultat_tree.item(selection[0])
        foremal_id = int(item['text'])
        foremal = self.db.hamta_foremal(foremal_id)
        foton = self.db.hamta_foton(foremal_id)

        if foremal:
            html = PrintManager.skriv_ut_foremal(foremal, foton)
            PrintManager.visa_utskrift(html, "Föremålsinformation")
        else:
            messagebox.showerror("Fel", "Kunde inte hämta föremålsinformation")

    def skriv_ut_foremalslista(self):
        """Skriv ut lista över föremål"""
        # Hämta aktuella sökresultat eller alla föremål
        resultat = []
        for item in self.resultat_tree.get_children():
            item_data = self.resultat_tree.item(item)
            foremal_id = int(item_data['text'])
            foremal = self.db.hamta_foremal(foremal_id)
            if foremal:
                resultat.append(foremal)

        if not resultat:
            # Om ingen sökning gjorts, hämta alla föremål
            resultat = self.db.sok_foremal()

        if resultat:
            html = PrintManager.skriv_ut_foremalslista(resultat)
            PrintManager.visa_utskrift(html, "Föremålslista")
        else:
            messagebox.showinfo("Info", "Inga föremål att skriva ut")

    def skriv_ut_statistik(self):
        """Skriv ut statistik"""
        stats = self.db.hamta_statistik()
        html = PrintManager.skriv_ut_statistik(stats)
        PrintManager.visa_utskrift(html, "Museistatistik")

    def skriv_ut_platslista(self):
        """Skriv ut lista över platser"""
        platser = self.db.hamta_platser()
        if platser:
            html = PrintManager.skriv_ut_platslista(platser)
            PrintManager.visa_utskrift(html, "Platslista")
        else:
            messagebox.showinfo("Info", "Inga platser registrerade")

    def skriv_ut_kategorilista(self):
        """Skriv ut lista över kategorier"""
        kategorier = self.db.hamta_kategorier()
        if kategorier:
            html = PrintManager.skriv_ut_kategorilista(kategorier)
            PrintManager.visa_utskrift(html, "Kategorilista")
        else:
            messagebox.showinfo("Info", "Inga kategorier registrerade")

    def skriv_ut_givarlista(self):
        """Skriv ut lista över givare"""
        givare = self.db.hamta_alla_givare_detaljerat()
        if givare:
            html = PrintManager.skriv_ut_givarlista(givare)
            PrintManager.visa_utskrift(html, "Givarlista")
        else:
            messagebox.showinfo("Info", "Inga givare registrerade")


def main():
    """Huvudfunktion"""
    root = tk.Tk()
    app = MuseumGUI(root)

    # Stäng databasanslutningen när fönstret stängs
    def on_closing():
        app.db.stang()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
