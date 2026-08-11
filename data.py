import os
import sqlite3
from datetime import date, datetime
from kivy.utils import platform
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from kivymd.uix.dialog import MDDialog
from licence import dossier_sustem

DATE_FORMAT = "%d~%m~%Y"
date_day = date.today().strftime(DATE_FORMAT)
DB_PATH = os.path.join(dossier_sustem, "data0.dat")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
tab_test = "produits"
nbr_jour_essaie = 14


def creer_tab_vend():
    c.execute('''CREATE TABLE IF NOT EXISTS Ventes(
        Nom VARCHAR,
        Quantite INTEGER,
        Prix_ventes DOUBLE NOT NULL,
        Gain DOUBLE,
        Total DOUBLE,
        Date TEXT,
        Heure TEXT DEFAULT ''
    )''')
    cols = [r[1] for r in c.execute('PRAGMA table_info(Ventes)').fetchall()]
    if "Heure" not in cols:
        c.execute("ALTER TABLE Ventes ADD COLUMN Heure TEXT DEFAULT ''")
    conn.commit()


def creer_nouv_tab():
    c.execute(f'''CREATE TABLE IF NOT EXISTS {tab_test} (
        Nom VARCHAR PRIMARY KEY,
        Quantite INTEGER,
        Prix_achat DOUBLE DEFAULT NULL,
        Prix_vente DOUBLE DEFAULT '' NOT NULL,
        Description TEXT DEFAULT '',
        Image TEXT DEFAULT ''
    )''')
    # Migration des anciennes bases EasyBoutik
    cols = [r[1] for r in c.execute(f'PRAGMA table_info({tab_test})').fetchall()]
    if "Image" not in cols:
        c.execute(f'ALTER TABLE {tab_test} ADD COLUMN Image TEXT DEFAULT \'\'')
    conn.commit()


def creer_nouv_line(nom, quantite, prix_vente, prix_achat, desc, image_path=""):
    try:
        existant = voir_tab_1_l(nom)
        if existant:
            nouvelle_qte = existant[1] + quantite
            if image_path:
                c.execute(f'UPDATE {tab_test} SET Quantite=?, Description=?, Image=? WHERE Nom=?',
                          (nouvelle_qte, desc, image_path, nom))
            else:
                c.execute(f'UPDATE {tab_test} SET Quantite=?, Description=? WHERE Nom=?',
                          (nouvelle_qte, desc, nom))
        else:
            c.execute(
                f'INSERT INTO {tab_test}(Nom, Quantite, Prix_achat, Prix_vente, Description, Image) VALUES(?,?,?,?,?,?)',
                (nom, quantite, prix_achat, prix_vente, desc, image_path)
            )
        conn.commit()
        return True
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print(e)
        return False


def supprimer_line_tab(nom):
    try:
        c.execute(f'DELETE FROM {tab_test} WHERE Nom=?', (nom,))
        conn.commit()
    except sqlite3.OperationalError:
        pass


def modif_line_tab(nom, colonne, nouv_val):
    try:
        c.execute(f'UPDATE {tab_test} SET {colonne}=? WHERE Nom=?', (nouv_val, nom))
        conn.commit()
        return True
    except (sqlite3.OperationalError, sqlite3.IntegrityError) as e:
        print(e)
        return False


def ajouter_image(nom, image_path):
    return modif_line_tab(nom, "Image", image_path or "")


def voir_tab_1_l(nom):
    c.execute(f'SELECT * FROM {tab_test} WHERE Nom=?', (nom,))
    return c.fetchone()


def voir_tab_all_l():
    c.execute(f'SELECT * FROM {tab_test}')
    return c.fetchall()


def vendre_db(nom, quantite_v):
    row = voir_tab_1_l(nom)
    if row is None:
        return None, "introuvable"
    nom_db, qte, prix_achat, prix_vente, desc, image = row
    benef_u = prix_vente - prix_achat
    if qte < quantite_v:
        return None, "stock"
    nouvelle_qte = qte - quantite_v
    c.execute(f'UPDATE {tab_test} SET Quantite=? WHERE Nom=?', (nouvelle_qte, nom))
    gain = benef_u * quantite_v
    total = prix_vente * quantite_v
    heure = datetime.now().strftime("%H:%M")
    c.execute('INSERT INTO Ventes(Nom, Quantite, Prix_ventes, Gain, Total, Date, Heure) VALUES(?,?,?,?,?,?,?)',
              (nom, quantite_v, prix_vente, gain, total, date_day, heure))
    conn.commit()
    return (gain, total), "ok"


def statistiques_jour(jour=None):
    jour = jour or date.today().strftime(DATE_FORMAT)
    c.execute('SELECT COALESCE(SUM(Gain),0), COALESCE(SUM(Total),0), COALESCE(SUM(Quantite),0), COUNT(*) FROM Ventes WHERE Date=?', (jour,))
    gain, total, qte, nb_ventes = c.fetchone()
    return float(gain or 0), float(total or 0), int(qte or 0), int(nb_ventes or 0)


def ventes_du_jour(jour=None):
    """Liste des ventes du jour, dans l'ordre chronologique."""
    jour = jour or date.today().strftime(DATE_FORMAT)
    c.execute('SELECT Nom, Quantite, Total, Heure, rowid FROM Ventes WHERE Date=? ORDER BY rowid', (jour,))
    return c.fetchall()


def creer_pdf():
    try:
        jour = date.today().strftime(DATE_FORMAT)
        gain_jour, ventes_jour, qte_jour, nb_ventes_jour = statistiques_jour(jour)
        if platform == "android":
            pdf_path = os.path.join(dossier_sustem, f"Rapport_{jour}.pdf")
        else:
            docs = os.path.join(os.path.expanduser("~"), "Documents")
            os.makedirs(docs, exist_ok=True)
            pdf_path = os.path.join(docs, f"Rapport_{jour}.pdf")

        pdf = canvas.Canvas(pdf_path)
        p_width = 595
        pdf.setFillColor(colors.HexColor("#1976D2"))
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(p_width / 2, 800, "EASYBOUTIK — RAPPORT JOURNALIER")
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.black)
        pdf.drawCentredString(p_width / 2, 782, f"Date : {jour}")

        summary = [
            ["VENTES DU JOUR", "BÉNÉFICE DU JOUR", "ARTICLES VENDUS"],
            [f"{ventes_jour:.0f} FCFA", f"{gain_jour:.0f} FCFA", str(qte_jour)]
        ]
        table = Table(summary, colWidths=[165, 165, 165])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,0), colors.HexColor('#1976D2')),
            ('BACKGROUND', (1,0), (1,0), colors.HexColor('#2E7D32')),
            ('BACKGROUND', (2,0), (2,0), colors.HexColor('#F57C00')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))
        table.wrapOn(pdf, 500, 100)
        table.drawOn(pdf, 50, 715)

        c.execute('SELECT Nom, Quantite, Prix_ventes, Gain, Total FROM Ventes WHERE Date=?', (jour,))
        rows = c.fetchall()
        data = [["Produit", "Qté", "Prix vente", "Bénéfice", "Total"]]
        data += [[r[0], r[1], f"{r[2]:.0f}", f"{r[3]:.0f}", f"{r[4]:.0f}"] for r in rows]
        if len(data) == 1:
            data.append(["Aucune vente", "-", "-", "-", "-"])
        t2 = Table(data, colWidths=[150, 55, 100, 100, 100], repeatRows=1)
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#37474F')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F5F7FA')]),
        ]))
        _, h = t2.wrapOn(pdf, 500, 600)
        t2.drawOn(pdf, 45, max(90, 690-h))
        pdf.setFillColor(colors.HexColor('#2E7D32'))
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, 55, f"BÉNÉFICE DU JOUR : {gain_jour:.0f} FCFA")
        pdf.setFillColor(colors.HexColor('#1976D2'))
        pdf.drawRightString(545, 55, f"VENTES DU JOUR : {ventes_jour:.0f} FCFA")
        pdf.save()
        MDDialog(text="Rapport journalier sauvegardé").open()
        return True
    except Exception as e:
        MDDialog(text=f"Erreur : {e}").open()
        return False


def rapport():
    if platform == "android":
        pdf_path = os.path.join(dossier_sustem, f"Rapport_{date.today().strftime(DATE_FORMAT)}.pdf")
        if os.path.exists(pdf_path):
            try:
                from jnius import autoclass
                Intent = autoclass('android.content.Intent')
                FileProvider = autoclass('androidx.core.content.FileProvider')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                File = autoclass('java.io.File')
                context = PythonActivity.mActivity
                uri = FileProvider.getUriForFile(context, context.getPackageName() + '.fileprovider', File(pdf_path))
                intent = Intent(Intent.ACTION_VIEW)
                intent.setDataAndType(uri, "application/pdf")
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                context.startActivity(intent)
            except Exception as e:
                MDDialog(text=f"Impossible d'ouvrir le PDF : {e}").open()
        else:
            MDDialog(text="Aucun rapport journalier trouvé").open()
    else:
        import subprocess
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        pdf_path = os.path.join(docs, f"Rapport_{date.today().strftime(DATE_FORMAT)}.pdf")
        if os.path.exists(pdf_path):
            try:
                os.startfile(pdf_path)  # Windows
            except AttributeError:
                try:
                    subprocess.Popen(["open", pdf_path])  # macOS
                except Exception:
                    subprocess.Popen(["xdg-open", pdf_path])  # Linux
        else:
            MDDialog(text="Aucun rapport trouvé").open()
