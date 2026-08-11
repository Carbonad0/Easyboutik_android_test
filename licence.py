import base64
import secrets
import sqlite3
from datetime import datetime, timedelta, date
from kivymd.uix.dialog import MDDialog
import sys
import os
from kivy.utils import platform

import rsa_lite

date_day = date.today().strftime("%d/%m/%Y")

# ---------------------------------------------------------------------------
# CLÉ PUBLIQUE — sert uniquement à VÉRIFIER les licences émises avec
# admin_tool/2_emettre_licence.py. Elle ne permet à personne de fabriquer une
# licence valide : c'est la clé privée (jamais présente ici) qui signe.
#
# ⚠️ Remplace ces valeurs par celles générées avec admin_tool/1_generer_cles.py
#    (contenu de cle_publique_a_copier.json) avant de publier l'app.
# ---------------------------------------------------------------------------
PUBLIC_KEY = {
    "n": 23923758458427897414516951540987927574791811039393673063416259079103989155539161495838341087068125489500434342066221692863483996473953990169719642587413559827337699427601125984001747940656292037349341774427240463175629325647623787035715659485471091116765173099471221497048632964704633070183423845511441904240963041564722587056673920277379237350577383368074302051982231132293353458136316654467500475354904176524174759579347839032969210844773587714012036689855403923377699309195903927039140131674556418274468847596394807069207976293932360460301053506817184372009471564593218698130389768641897094116176401730182673259767,
    "e": 65537,
}


def get_data_dir():
    if platform == "android":
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except Exception:
            return os.path.join(os.path.expanduser("~"), ".easyboutik")
    path = os.path.join(os.path.expanduser("~"), ".easyboutik")
    os.makedirs(path, exist_ok=True)
    return path


dossier_sustem = get_data_dir()
os.makedirs(dossier_sustem, exist_ok=True)

conn_l = sqlite3.connect(os.path.join(dossier_sustem, "licon.dat"))
c_l = conn_l.cursor()


# ---------------------------------------------------------------------------
# IDENTIFIANT APPAREIL
# ---------------------------------------------------------------------------
# uuid.getnode() (ancienne méthode) n'est plus fiable sur Android 10+ : l'OS
# restreint/randomise souvent l'accès à l'adresse MAC réelle. On utilise à la
# place, par ordre de préférence :
#   1. L'ANDROID_ID du système (stable tant que l'app n'est pas désinstallée)
#   2. Un identifiant aléatoire généré une fois et conservé dans un fichier
#      local (fonctionne sur desktop et en secours sur Android)
def _lire_android_id():
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Settings = autoclass("android.provider.Settings$Secure")
        resolver = PythonActivity.mActivity.getContentResolver()
        val = Settings.getString(resolver, "android_id")
        return val.upper() if val else None
    except Exception:
        return None


def obt_id_m_u():
    id_file = os.path.join(dossier_sustem, "device_id.txt")
    if os.path.exists(id_file):
        try:
            with open(id_file, "r", encoding="utf-8") as f:
                existing = f.read().strip()
            if existing:
                return existing
        except OSError:
            pass

    new_id = _lire_android_id() if platform == "android" else None
    if not new_id:
        new_id = secrets.token_hex(8).upper()

    try:
        with open(id_file, "w", encoding="utf-8") as f:
            f.write(new_id)
    except OSError:
        pass
    return new_id


def creer_doc():
    if platform == "android":
        chemin = os.path.join(dossier_sustem, "ID_Machine.txt")
    else:
        docs = os.path.join(os.path.expanduser("~"), "Documents")
        os.makedirs(docs, exist_ok=True)
        chemin = os.path.join(docs, "ID Machine.txt")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("* * * * * EASYBOUTIK * * * * *\n\n")
        f.write(f"ID Machine : {obt_id_m_u()}\n")
        f.write(f"Date : {date_day}\n")
    return chemin


def creer_tab_duree():
    c_l.execute("""CREATE TABLE IF NOT EXISTS duree(
        start TEXT, connect TEXT, expiration TEXT)""")
    conn_l.commit()


def creer_tab_licence():
    c_l.execute("CREATE TABLE IF NOT EXISTS licence(code TEXT, expiration TEXT, forfait TEXT)")
    conn_l.commit()


# ---------------------------------------------------------------------------
# VÉRIFICATION DE LICENCE (par signature — aucun secret côté client)
# ---------------------------------------------------------------------------
def verif_code_licence(code_saisi, device_id_attendu=None):
    """Vérifie un code de licence reçu de l'admin (via WhatsApp).
    Retourne (ok, expiration, forfait) si valide, sinon (False, None, None)."""
    device_id_attendu = device_id_attendu or obt_id_m_u()
    try:
        payload_b64, sig_b64 = code_saisi.strip().split(".")
        payload = base64.urlsafe_b64decode(payload_b64.encode())
        signature = base64.urlsafe_b64decode(sig_b64.encode())
    except Exception:
        return False, None, None

    if not rsa_lite.verify(payload, signature, PUBLIC_KEY):
        return False, None, None  # signature invalide -> code falsifié ou corrompu

    try:
        device_id, expiration, forfait = payload.decode().split("|")
    except Exception:
        return False, None, None

    if device_id.upper() != device_id_attendu.upper():
        return False, None, None  # licence émise pour un autre appareil

    return True, expiration, forfait


def save_licence(code, expir, forfait):
    c_l.execute("DELETE FROM licence")
    c_l.execute("INSERT INTO licence VALUES (?, ?, ?)", (code, expir, forfait))
    conn_l.commit()


def charger_licence():
    c_l.execute("SELECT code FROM licence")
    row = c_l.fetchone()
    return row[0] if row else None


def verif_licence():
    """Vérifie présence, signature, appareil et expiration de la licence
    stockée localement. Comme le code contient sa propre signature, on peut
    revérifier son authenticité hors-ligne à chaque lancement (protège contre
    la modification directe de la base sqlite)."""
    c_l.execute("SELECT code, expiration FROM licence")
    row = c_l.fetchone()
    if row is None:
        return False

    code_s, expir_s = row
    ok, expiration, _forfait = verif_code_licence(code_s)
    if not ok or expiration != expir_s:
        return False

    try:
        expiration_dt = datetime.strptime(expir_s, "%d/%m/%Y")
    except ValueError:
        return False

    # Une licence expirée ne doit jamais donner accès à l'application.
    if datetime.now() >= expiration_dt + timedelta(days=1):
        return False

    return True


def save_expir(expir):
    maintenant = datetime.now().isoformat()
    c_l.execute("SELECT COUNT(*) FROM duree")
    count = c_l.fetchone()[0]
    if count == 0:
        c_l.execute("INSERT INTO duree VALUES (?,?,?)", (maintenant, maintenant, expir))
    else:
        c_l.execute(
            "UPDATE duree SET start=?, connect=?, expiration=?",
            (maintenant, maintenant, expir),
        )
    conn_l.commit()


def compte_le_temp(callback_expir=None):
    if not verif_licence():
        return False

    c_l.execute("CREATE TABLE IF NOT EXISTS duree(start TEXT, connect TEXT, expiration TEXT)")
    conn_l.commit()
    c_l.execute("SELECT start, connect, expiration FROM duree")
    row = c_l.fetchone()
    maintenant = datetime.now()

    if row is None or row[2] is None:
        return True

    try:
        last_view = datetime.fromisoformat(row[1])
        exp = datetime.strptime(row[2], "%d/%m/%Y")
    except (ValueError, TypeError):
        return False

    if last_view > maintenant:
        from kivy.clock import Clock
        MDDialog(
            title="Erreur Système",
            text="Vous avez modifié l'heure.\nL'application va se fermer.",
        ).open()
        # .open() ne fait que programmer l'affichage à la prochaine frame :
        # un sys.exit() immédiat fermait l'appli avant que le dialogue soit visible.
        Clock.schedule_once(lambda dt: sys.exit(), 2.5)
        return False

    c_l.execute("UPDATE duree SET connect=?", (maintenant.isoformat(),))
    conn_l.commit()

    # On considère la licence expirée à la fin de sa dernière journée.
    if maintenant >= exp + timedelta(days=1):
        if callback_expir:
            callback_expir()
        return False

    temp_rest = exp + timedelta(days=1) - maintenant
    if temp_rest.total_seconds() <= 24 * 3600:
        heures = max(1, int(temp_rest.total_seconds() // 3600))
        MDDialog(title="Licence", text=f"Il vous reste environ {heures} h d'utilisation").open()
    elif temp_rest.days <= 7:
        MDDialog(title="Licence", text=f"Il vous reste {temp_rest.days} jours").open()
    return True


def alert_reset():
    db_exists = os.path.exists(os.path.join(dossier_sustem, "licon.dat"))

    c_l.execute("SELECT COUNT(*) FROM licence")
    actif = c_l.fetchone()[0] > 0

    if actif and not db_exists:
        from kivy.clock import Clock
        MDDialog(
            title="SÉCURITÉ",
            text="Tentative de reset détectée",
        ).open()
        Clock.schedule_once(lambda dt: sys.exit(), 2.5)
