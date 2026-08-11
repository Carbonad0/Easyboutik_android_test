import os
import shutil
from datetime import datetime

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.behaviors.hover_behavior import HoverBehavior
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.scrollview import MDScrollView

from data import *
from licence import *


class SmoothButton(HoverBehavior, MDRaisedButton):
    """Bouton avec feedback au survol/appui (actions, formulaires)."""
    normal_color = ListProperty([0.20, 0.45, 0.90, 1])
    hover_color = ListProperty([0.25, 0.52, 0.98, 1])
    pressed_color = ListProperty([0.14, 0.34, 0.76, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radius = [16, 16, 16, 16]
        self.elevation = 2
        if "md_bg_color" in kwargs:
            self.normal_color = list(kwargs["md_bg_color"])
            self.hover_color = [min(c * 1.10, 1) for c in self.normal_color[:3]] + [1]
            self.pressed_color = [max(c * 0.82, 0) for c in self.normal_color[:3]] + [1]

    def on_enter(self, *args):
        Animation(elevation=5, duration=0.10).start(self)

    def on_leave(self, *args):
        if not self.state == "down":
            Animation(elevation=1, duration=0.10).start(self)

    def on_press(self):
        Animation(elevation=1, duration=0.06).start(self)
        super().on_press()

    def on_release(self):
        super().on_release()
        Animation(elevation=2, duration=0.10).start(self)


class SmoothIconButton(HoverBehavior, MDIconButton):
    """Icône avec feedback visuel au survol et à la pression (barre du haut)."""
    normal_icon_color = ListProperty([0.94, 0.96, 1, 1])
    hover_icon_color = ListProperty([0.25, 0.52, 0.98, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.icon_size = "24dp"

    def on_enter(self, *args):
        Animation(icon_size=dp(28), duration=0.10).start(self)
        if hasattr(self, "icon_color"):
            self.icon_color = self.hover_icon_color

    def on_leave(self, *args):
        Animation(icon_size=dp(24), duration=0.10).start(self)
        if hasattr(self, "icon_color"):
            self.icon_color = self.normal_icon_color

    def on_press(self):
        Animation(icon_size=dp(21), duration=0.06).start(self)
        super().on_press()

    def on_release(self):
        super().on_release()
        Animation(icon_size=dp(24), duration=0.08).start(self)


class NavButton(HoverBehavior, ButtonBehavior, MDBoxLayout):
    """Bouton de navigation basse : icône Material au-dessus d'un label,
    avec un fond arrondi qui s'allume quand l'écran est actif."""
    nav_icon = StringProperty("circle-outline")
    label_text = StringProperty("")
    nav_active_color = ListProperty([0.20, 0.45, 0.90, 1])
    is_current = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing="2dp", padding=("2dp", "6dp"), **kwargs)
        with self.canvas.before:
            self._bg_color = Color(0, 0, 0, 0)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
        self._icon_widget = MDIcon(
            icon=self.nav_icon, halign="center", theme_text_color="Custom",
            text_color=self.nav_active_color, font_size="22sp",
            size_hint_y=None, height="24dp",
        )
        self._label_widget = MDLabel(
            text=self.label_text, halign="center", font_style="Caption",
            theme_text_color="Custom", text_color=self.nav_active_color,
            size_hint_y=None, height="14dp",
        )
        self.add_widget(self._icon_widget)
        self.add_widget(self._label_widget)
        self.bind(
            pos=self._update_bg, size=self._update_bg,
            nav_icon=self._sync_icon, label_text=self._sync_label,
            nav_active_color=self._sync_color, is_current=self._sync_active,
        )

    def _update_bg(self, *args):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size

    def _sync_icon(self, *args):
        self._icon_widget.icon = self.nav_icon

    def _sync_label(self, *args):
        self._label_widget.text = self.label_text

    def _sync_color(self, *args):
        self._icon_widget.text_color = self.nav_active_color
        self._label_widget.text_color = self.nav_active_color
        self._sync_active()

    def _sync_active(self, *args):
        self._bg_color.rgba = (self.nav_active_color[:3] + [0.16]) if self.is_current else [0, 0, 0, 0]

    def on_disabled(self, instance, value):
        self.opacity = 0.35 if value else 1

    def on_enter(self, *args):
        Animation(opacity=0.75, duration=0.08).start(self)

    def on_leave(self, *args):
        if not self.disabled:
            Animation(opacity=1, duration=0.08).start(self)

    def on_press(self):
        Animation(opacity=0.55, duration=0.05).start(self)

    def on_release(self):
        Animation(opacity=1, duration=0.10).start(self)


KV = """
MDScreenManager:
    MDScreen:
        name: "main"
        MDBoxLayout:
            orientation: "vertical"
            md_bg_color: app.content_bg_color

            MDBoxLayout:
                id: topbar
                orientation: "horizontal"
                size_hint_y: None
                height: "58dp"
                padding: "14dp", "5dp"
                md_bg_color: app.topbar_bg_color
                elevation: 2

                MDBoxLayout:
                    orientation: "vertical"
                    MDLabel:
                        id: top_title
                        text: "EASYBOUTIK"
                        bold: True
                        font_style: "H6"
                        theme_text_color: "Custom"
                        text_color: app.top_title_color
                        valign: "bottom"
                    MDLabel:
                        text: "Version 3.4"
                        font_style: "Caption"
                        theme_text_color: "Secondary"
                        valign: "top"
                        size_hint_y: None
                        height: "14dp"

                Widget:

                SmoothIconButton:
                    id: btn_theme_top
                    icon: "theme-light-dark"
                    theme_icon_color: "Custom"
                    icon_color: app.top_icon_color
                    on_release: app.changer_theme()

            MDBoxLayout:
                id: frame_contenu
                orientation: "vertical"
                size_hint_y: 1
                padding: "12dp", "10dp"
                spacing: "10dp"
                md_bg_color: app.content_bg_color

            MDLabel:
                id: lbl_benef
                text: "Bénéfice du jour : 0 FCFA"
                halign: "right"
                bold: True
                size_hint_y: None
                height: "30dp"
                theme_text_color: "Custom"
                text_color: app.benef_color
                padding: "0dp", "0dp", "12dp", "2dp"

            MDBoxLayout:
                id: bottom_nav
                orientation: "horizontal"
                size_hint_y: None
                height: "76dp"
                padding: "10dp", "6dp", "10dp", "6dp"
                spacing: "4dp"
                md_bg_color: app.nav_bg_color
                elevation: 8

                NavButton:
                    id: menu_accueil
                    nav_icon: "home-outline"
                    label_text: "Accueil"
                    nav_active_color: app.menu_colors[0]
                    on_release: app.si_autorise(app.afficher_accueil)

                NavButton:
                    id: menu_ajouter
                    nav_icon: "plus-box-outline"
                    label_text: "Ajouter"
                    nav_active_color: app.menu_colors[1]
                    on_release: app.si_autorise(app.afficher_ajouter_produit)

                NavButton:
                    id: menu_vendre
                    nav_icon: "cart-outline"
                    label_text: "Vendre"
                    nav_active_color: app.menu_colors[2]
                    on_release: app.si_autorise(app.afficher_vendre)

                NavButton:
                    id: menu_stock
                    nav_icon: "package-variant-closed"
                    label_text: "Stock"
                    nav_active_color: app.menu_colors[3]
                    on_release: app.si_autorise(app.afficher_stock)

                NavButton:
                    id: menu_rapport
                    nav_icon: "chart-box-outline"
                    label_text: "Rapports"
                    nav_active_color: app.menu_colors[4]
                    on_release: app.si_autorise(app.afficher_rapport)
"""


class GlassCard(MDCard):
    """Carte glassmorphism légère : surface translucide, bordure et halo subtil.

    Le vrai flou temps réel est volontairement évité pour conserver de bonnes
    performances sur les téléphones modestes.
    """

    def __init__(self, **kwargs):
        bg = kwargs.get("md_bg_color", [0.10, 0.13, 0.19, 0.72])
        super().__init__(**kwargs)
        self.radius = [22, 22, 22, 22]
        self.elevation = kwargs.get("elevation", 2)
        self.md_bg_color = bg

        with self.canvas.after:
            Color(1, 1, 1, 0.13)
            self._glass_border = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(22)),
                width=1.0,
            )

        self.bind(pos=self._update_glass, size=self._update_glass)

    def _update_glass(self, *args):
        self._glass_border.rounded_rectangle = (
            self.x, self.y, self.width, self.height, dp(22)
        )


class ClickableCard(ButtonBehavior, GlassCard):
    """GlassCard cliquable — utilisée pour sélectionner un produit dans la liste de vente."""
    pass


class EasyBoutikApp(MDApp):
    dialog = None
    licence_active = False
    image_selection = StringProperty("")

    # Palette moderne : indigo / emerald / amber / violet / cyan.
    menu_colors = [
        (0.31, 0.27, 0.90, 1),
        (0.08, 0.60, 0.43, 1),
        (0.92, 0.55, 0.08, 1),
        (0.46, 0.32, 0.88, 1),
        (0.06, 0.57, 0.66, 1),
    ]

    # Valeurs initiales : thème clair (comme la maquette), verrouillable en sombre.
    menu_text_color = (0.10, 0.12, 0.18, 1)
    drawer_bg_color = (0.965, 0.975, 0.99, 1)
    content_bg_color = (0.965, 0.97, 0.985, 1)
    card_bg_color = (1, 1, 1, 1)
    topbar_bg_color = (1, 1, 1, 1)
    top_icon_color = (0.10, 0.12, 0.18, 1)
    top_title_color = (0.10, 0.12, 0.18, 1)
    benef_color = (0.15, 0.78, 0.40, 1)
    license_button_color = (0.24, 0.32, 0.78, 1)
    nav_bg_color = (1, 1, 1, 0.97)

    def build(self):
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.accent_palette = "Teal"
        self.theme_cls.material_style = "M3"
        self.title = "EASYBOUTIK"
        return Builder.load_string(KV)

    def on_start(self):
        creer_nouv_tab()
        creer_tab_vend()
        creer_tab_duree()
        creer_tab_licence()
        alert_reset()

        # IMPORTANT : aucune fonctionnalité métier n'est accessible sans licence.
        self.licence_active = verif_licence()
        self.appliquer_couleurs()

        if self.licence_active:
            if not compte_le_temp(callback_expir=self.verrouiller_application):
                self.verrouiller_application(show_dialog=False)
            else:
                self.afficher_accueil()
        else:
            self.verrouiller_application(show_dialog=False)
            Clock.schedule_once(lambda dt: self.ouvrir_licence(), 0.5)

        Clock.schedule_interval(lambda dt: self._verifier_licence_periodique(), 60)
        Clock.schedule_interval(lambda dt: self.mettre_a_jour_dashboard(), 20)
        Clock.schedule_interval(lambda dt: self.mettre_a_jour_temps_restant(), 60)

    def _verifier_licence_periodique(self):
        if not self.licence_active:
            return
        if not verif_licence() or not compte_le_temp(callback_expir=None):
            self.verrouiller_application()

    # ------------------------------------------------------------------
    # THÈME
    # ------------------------------------------------------------------
    def changer_theme(self):
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.theme_style = "Light"
            self.menu_text_color = (0.10, 0.12, 0.18, 1)
            self.drawer_bg_color = (0.965, 0.975, 0.99, 1)
            self.content_bg_color = (0.965, 0.97, 0.985, 1)
            self.card_bg_color = (1, 1, 1, 1)
            self.topbar_bg_color = (1, 1, 1, 1)
            self.top_icon_color = (0.10, 0.12, 0.18, 1)
            self.top_title_color = (0.10, 0.12, 0.18, 1)
            self.license_button_color = (0.24, 0.32, 0.78, 1)
            self.nav_bg_color = (1, 1, 1, 0.97)
        else:
            self.theme_cls.theme_style = "Dark"
            self.menu_text_color = (0.94, 0.96, 1, 1)
            self.drawer_bg_color = (0.055, 0.075, 0.12, 1)
            self.content_bg_color = (0.055, 0.065, 0.09, 1)
            self.card_bg_color = (0.10, 0.12, 0.16, 1)
            self.topbar_bg_color = (0.075, 0.09, 0.14, 1)
            self.top_icon_color = (0.94, 0.96, 1, 1)
            self.top_title_color = (0.94, 0.96, 1, 1)
            self.license_button_color = (0.45, 0.55, 1, 1)
            self.nav_bg_color = (0.075, 0.09, 0.14, 0.96)

        self.appliquer_couleurs()
        if self.licence_active:
            self.afficher_accueil()

    def appliquer_couleurs(self):
        root = self.root
        if not root:
            return
        root.ids.bottom_nav.md_bg_color = self.nav_bg_color
        root.ids.frame_contenu.md_bg_color = self.content_bg_color
        root.ids.topbar.md_bg_color = self.topbar_bg_color
        root.ids.btn_theme_top.icon_color = self.top_icon_color
        root.ids.btn_theme_top.normal_icon_color = self.top_icon_color
        root.ids.btn_theme_top.hover_icon_color = (0.20, 0.50, 0.95, 1)
        root.ids.lbl_benef.text_color = self.benef_color
        root.ids.top_title.text_color = self.top_title_color

        for name, color in zip(
            ("menu_accueil", "menu_ajouter", "menu_vendre", "menu_stock", "menu_rapport"),
            self.menu_colors,
        ):
            root.ids[name].nav_active_color = list(color)

        self._appliquer_etat_verrouillage()

    # ------------------------------------------------------------------
    # LICENCE / VERROUILLAGE
    # ------------------------------------------------------------------
    def si_autorise(self, callback):
        if self.licence_active and verif_licence():
            callback()
        else:
            self.verrouiller_application()

    def _appliquer_etat_verrouillage(self):
        if not self.root:
            return
        disabled = not self.licence_active
        for name in ("menu_accueil", "menu_ajouter", "menu_vendre", "menu_stock", "menu_rapport"):
            self.root.ids[name].disabled = disabled
        self.root.ids.btn_theme_top.disabled = False

    def _marquer_nav_actif(self, name):
        if not self.root:
            return
        for n in ("menu_accueil", "menu_ajouter", "menu_vendre", "menu_stock", "menu_rapport"):
            self.root.ids[n].is_current = (n == name)

    def verrouiller_application(self, show_dialog=True):
        self.licence_active = False
        if self.root:
            self._appliquer_etat_verrouillage()
            content = self.root.ids.frame_contenu
            content.clear_widgets()
            content.md_bg_color = self.content_bg_color

            card = GlassCard(
                orientation="vertical",
                size_hint=(0.92, None),
                height="270dp",
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                padding="20dp",
                spacing="12dp",
                radius=[22, 22, 22, 22],
                elevation=3,
                md_bg_color=self.card_bg_color,
            )
            card.add_widget(MDIcon(icon="lock-outline", halign="center", font_size="40sp",
                                    theme_text_color="Custom", text_color=self.menu_colors[0]))
            card.add_widget(MDLabel(text="EASYBOUTIK est verrouillé", font_style="H5", bold=True, halign="center"))
            card.add_widget(MDLabel(
                text="Une licence valide est nécessaire pour accéder\naux ventes, au stock et aux rapports.",
                halign="center", theme_text_color="Secondary",
            ))
            btn = SmoothButton(
                text="Activer ma licence", icon="key-outline",
                md_bg_color=(0.31, 0.27, 0.90, 1),
                size_hint_x=1, size_hint_y=None, height="52dp",
            )
            btn.bind(on_release=lambda x: self.ouvrir_licence())
            card.add_widget(btn)
            content.add_widget(card)
            self.mettre_a_jour_temps_restant()

        if show_dialog:
            Clock.schedule_once(lambda dt: self.ouvrir_licence(), 0.15)

    # ------------------------------------------------------------------
    # UTILITAIRES UI
    # ------------------------------------------------------------------
    def nettoyer(self):
        content = self.root.ids.frame_contenu
        content.clear_widgets()
        content.opacity = 0
        Animation(opacity=1, duration=0.18).start(content)

    def show_message(self, title, message):
        if self.dialog:
            try:
                self.dialog.dismiss()
            except Exception:
                pass
        self.dialog = MDDialog(
            title=title,
            text=message,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())],
        )
        self.dialog.open()

    def card(self, title, value, icon, color):
        box = MDBoxLayout(orientation="vertical", padding="14dp", spacing="4dp")
        header = MDBoxLayout(size_hint_y=None, height="24dp", spacing="6dp")
        header.add_widget(MDIcon(icon=icon, theme_text_color="Custom", text_color=color,
                                  size_hint_x=None, width="22dp", font_size="18sp"))
        header.add_widget(MDLabel(text=title, bold=True, theme_text_color="Secondary", font_style="Caption"))
        box.add_widget(header)
        box.add_widget(MDLabel(text=value, font_style="H5", bold=True, theme_text_color="Custom", text_color=color))
        card = GlassCard(
            orientation="vertical",
            size_hint_y=None,
            height="105dp",
            radius=[22, 22, 22, 22],
            elevation=2,
            padding="4dp",
            md_bg_color=[self.card_bg_color[0], self.card_bg_color[1], self.card_bg_color[2], 0.85],
        )
        card.add_widget(box)
        return card

    def mettre_a_jour_dashboard(self):
        if not self.licence_active:
            return
        gain, ventes, qte, nb = statistiques_jour()
        self.root.ids.lbl_benef.text = f"Bénéfice du jour : {gain:,.0f} FCFA".replace(",", " ")

    def afficher_accueil(self):
        if not self.licence_active:
            return
        self.nettoyer()
        gain, ventes, qte, nb = statistiques_jour()
        products = len(voir_tab_all_l())
        content = self.root.ids.frame_contenu
        content.add_widget(MDLabel(text="Tableau de bord", font_style="H4", bold=True, size_hint_y=None, height="48dp"))
        content.add_widget(MDLabel(text=datetime.now().strftime("%A %d %B %Y"), theme_text_color="Secondary", size_hint_y=None, height="28dp"))

        stats = MDBoxLayout(spacing="8dp", size_hint_y=None, height="105dp")
        stats.add_widget(self.card("VENTES DU JOUR", f"{ventes:,.0f} FCFA".replace(",", " "), "cash-multiple", (0.12, 0.50, 0.90, 1)))
        stats.add_widget(self.card("BÉNÉFICE DU JOUR", f"{gain:,.0f} FCFA".replace(",", " "), "chart-line", (0.12, 0.65, 0.32, 1)))
        content.add_widget(stats)

        stats2 = MDBoxLayout(spacing="8dp", size_hint_y=None, height="105dp")
        stats2.add_widget(self.card("ARTICLES VENDUS", str(qte), "cart-outline", (0.95, 0.55, 0.10, 1)))
        stats2.add_widget(self.card("PRODUITS EN STOCK", str(products), "package-variant", (0.45, 0.35, 0.80, 1)))
        content.add_widget(stats2)

        content.add_widget(MDLabel(text="ACTIONS RAPIDES", bold=True, size_hint_y=None, height="35dp"))
        actions = MDBoxLayout(spacing="8dp", size_hint_y=None, height="55dp")
        for text, icon, color, callback in [
            ("Ajouter", "plus-box-outline", (0.13, 0.60, 0.35, 1), self.afficher_ajouter_produit),
            ("Vendre", "cart-outline", (0.95, 0.55, 0.10, 1), self.afficher_vendre),
        ]:
            b = SmoothButton(text=text, icon=icon, md_bg_color=color)
            b.bind(on_release=lambda x, cb=callback: cb())
            actions.add_widget(b)
        content.add_widget(actions)
        self._marquer_nav_actif("menu_accueil")

    # ------------------------------------------------------------------
    # IMAGES PRODUITS
    # ------------------------------------------------------------------
    def choisir_image(self, callback):
        try:
            from plyer import filechooser
            filechooser.open_file(on_selection=lambda selection: self._image_selected(selection, callback))
        except Exception as e:
            self.show_message("Image", f"Sélecteur indisponible : {e}")

    def _image_selected(self, selection, callback):
        if selection:
            callback(selection[0])

    def copier_image(self, src, nom):
        if not src or not os.path.exists(src):
            return ""
        image_dir = os.path.join(dossier_sustem, "images")
        os.makedirs(image_dir, exist_ok=True)
        safe = "".join(ch for ch in nom if ch.isalnum() or ch in "-_ ").strip().replace(" ", "_") or "produit"
        ext = os.path.splitext(src)[1].lower() or ".jpg"
        dest = os.path.join(image_dir, safe + ext)
        try:
            shutil.copy2(src, dest)
            return dest
        except Exception:
            return src

    def afficher_ajouter_produit(self):
        if not self.licence_active:
            return
        self.nettoyer()
        content = self.root.ids.frame_contenu
        content.add_widget(MDLabel(text="Ajouter un produit", font_style="H4", bold=True, size_hint_y=None, height="48dp"))
        nom = MDTextField(hint_text="Nom du produit")
        qte = MDTextField(hint_text="Quantité", input_filter="int")
        achat = MDTextField(hint_text="Prix d'achat", input_filter="float")
        vente = MDTextField(hint_text="Prix de vente", input_filter="float")
        desc = MDTextField(hint_text="Description (optionnel)")
        for w in (nom, qte, achat, vente, desc):
            content.add_widget(w)
        image_label = MDLabel(text="Aucune image sélectionnée", theme_text_color="Secondary", size_hint_y=None, height="35dp")
        content.add_widget(image_label)

        def selected(path):
            self.image_selection = path
            image_label.text = "Image sélectionnée"

        bimg = SmoothButton(text="Ajouter une image", icon="camera-outline", md_bg_color=(0.35, 0.30, 0.80, 1))
        bimg.bind(on_release=lambda x: self.choisir_image(selected))
        content.add_widget(bimg)
        msg = MDLabel(text="", halign="center", size_hint_y=None, height="32dp")
        content.add_widget(msg)

        def save(*args):
            try:
                n = nom.text.strip().lower(); q = int(qte.text); a = float(achat.text); v = float(vente.text); d = desc.text.strip()
                if not n or q <= 0 or a <= 0 or v <= 0:
                    raise ValueError
                path = self.copier_image(self.image_selection, n) if self.image_selection else ""
                if creer_nouv_line(n, q, v, a, d, path):
                    msg.text = "✓ Produit enregistré"
                    msg.theme_text_color = "Custom"
                    msg.text_color = (0.2, 0.75, 0.35, 1)
                    self.image_selection = ""
                    for field in (nom, qte, achat, vente, desc):
                        field.text = ""
                    self.mettre_a_jour_dashboard()
                else:
                    msg.text = "Impossible d'enregistrer"
            except Exception:
                msg.text = "Vérifiez les informations saisies"
                msg.text_color = (0.95, 0.25, 0.20, 1)

        save_btn = SmoothButton(text="Enregistrer le produit", icon="content-save-outline", md_bg_color=(0.12, 0.65, 0.32, 1), size_hint_y=None, height="52dp")
        save_btn.bind(on_release=save)
        content.add_widget(save_btn)
        self._marquer_nav_actif("menu_ajouter")

    def _produit_row(self, nom, qte, pv, img, on_release):
        """Ligne compacte (miniature + nom + stock + prix) utilisée dans la sélection de vente."""
        row = ClickableCard(
            orientation="horizontal", size_hint_y=None, height="76dp",
            radius=[16, 16, 16, 16], padding="8dp", spacing="10dp",
            elevation=1, md_bg_color=self.card_bg_color,
        )
        if img and os.path.exists(img):
            row.add_widget(Image(source=img, size_hint_x=None, width="58dp", allow_stretch=True, keep_ratio=True))
        else:
            ph = MDBoxLayout(size_hint_x=None, width="58dp", md_bg_color=(0.85, 0.87, 0.92, 1) if self.theme_cls.theme_style == "Light" else (0.20, 0.24, 0.31, 1))
            ph.add_widget(MDIcon(icon="package-variant", halign="center", theme_text_color="Secondary"))
            row.add_widget(ph)

        info = MDBoxLayout(orientation="vertical")
        info.add_widget(MDLabel(text=nom.title(), bold=True))
        stock_color = (0.95, 0.25, 0.20, 1) if qte <= 5 else (0.15, 0.70, 0.35, 1)
        info.add_widget(MDLabel(text=f"Stock disponible : {qte}", theme_text_color="Custom", text_color=stock_color, font_style="Caption"))
        info.add_widget(MDLabel(text=f"{pv:.0f} FCFA", bold=True, theme_text_color="Custom", text_color=(0.12, 0.50, 0.90, 1)))
        row.add_widget(info)
        row.bind(on_release=on_release)
        return row

    def afficher_vendre(self):
        if not self.licence_active:
            return
        self.nettoyer()
        content = self.root.ids.frame_contenu
        content.add_widget(MDLabel(text="Nouvelle vente", font_style="H4", bold=True, size_hint_y=None, height="48dp"))
        search = MDTextField(hint_text="Rechercher un produit...")
        content.add_widget(search)

        scroll = MDScrollView(size_hint_y=None, height="230dp")
        lst = MDBoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None)
        lst.bind(minimum_height=lst.setter("height"))
        scroll.add_widget(lst)
        content.add_widget(scroll)

        selected_box = MDBoxLayout(size_hint_y=None, height="0dp")
        content.add_widget(selected_box)

        qty_value = [1]
        qty_label = MDLabel(text="1", halign="center", font_style="H5", bold=True, size_hint_x=None, width="50dp")
        stepper = MDBoxLayout(size_hint_y=None, height="55dp", spacing="18dp", pos_hint={"center_x": 0.5})

        def dec(*args):
            if qty_value[0] > 1:
                qty_value[0] -= 1
                qty_label.text = str(qty_value[0])

        def inc(*args):
            qty_value[0] += 1
            qty_label.text = str(qty_value[0])

        stepper.add_widget(Widget())
        btn_minus = MDIconButton(icon="minus-circle-outline", theme_icon_color="Custom", icon_color=(0.95, 0.55, 0.10, 1))
        btn_minus.bind(on_release=dec)
        stepper.add_widget(btn_minus)
        stepper.add_widget(qty_label)
        btn_plus = MDIconButton(icon="plus-circle-outline", theme_icon_color="Custom", icon_color=(0.95, 0.55, 0.10, 1))
        btn_plus.bind(on_release=inc)
        stepper.add_widget(btn_plus)
        stepper.add_widget(Widget())
        content.add_widget(stepper)

        msg = MDLabel(text="", halign="center", size_hint_y=None, height="30dp")
        content.add_widget(msg)

        chosen = [None]

        def choose(nom, *args):
            chosen[0] = nom
            search.text = nom
            refresh()

        def refresh(*args):
            lst.clear_widgets()
            term = search.text.lower().strip()
            produits = voir_tab_all_l()
            for p in produits:
                nom, qte, pa, pv, desc, img = p
                if term and term not in nom.lower() and nom != chosen[0]:
                    continue
                row = self._produit_row(nom, qte, pv, img, lambda x, n=nom: choose(n))
                lst.add_widget(row)

        refresh()
        search.bind(text=refresh)

        def sell(*args):
            n = chosen[0]
            q = qty_value[0]
            if not n:
                self.show_message("Vente", "Sélectionnez un produit dans la liste.")
                return
            result, status = vendre_db(n, q)
            if status == "ok":
                self.show_message("Vente enregistrée", f"Vente : {result[1]:.0f} FCFA\nBénéfice : {result[0]:.0f} FCFA")
                self.mettre_a_jour_dashboard()
                qty_value[0] = 1
                qty_label.text = "1"
                chosen[0] = None
                search.text = ""
                refresh()
            elif status == "stock":
                self.show_message("Stock insuffisant", "La quantité demandée dépasse le stock disponible.")
            else:
                self.show_message("Produit introuvable", "Sélectionnez un produit existant.")

        btn = SmoothButton(text="VALIDER LA VENTE", icon="check-circle-outline", md_bg_color=(0.95, 0.55, 0.10, 1), size_hint_y=None, height="55dp")
        btn.bind(on_release=sell)
        content.add_widget(btn)
        self._marquer_nav_actif("menu_vendre")

    def afficher_stock(self):
        if not self.licence_active:
            return
        self.nettoyer()
        content = self.root.ids.frame_contenu
        content.add_widget(MDLabel(text="Mon stock", font_style="H4", bold=True, size_hint_y=None, height="48dp"))
        search = MDTextField(hint_text="Rechercher...")
        content.add_widget(search)

        scroll = MDScrollView(bar_width="3dp", effect_cls="ScrollEffect")
        box = MDBoxLayout(orientation="vertical", spacing="10dp", padding="2dp", size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        scroll.add_widget(box)
        content.add_widget(scroll)

        def refresh(*args):
            box.clear_widgets()
            term = search.text.lower().strip()
            produits = voir_tab_all_l()
            if not produits:
                box.add_widget(MDLabel(text="Aucun produit enregistré.", halign="center", theme_text_color="Secondary", size_hint_y=None, height="80dp"))
                return
            for p in produits:
                nom, qte, pa, pv, desc, img = p
                if term and term not in nom.lower():
                    continue

                card = MDCard(
                    orientation="horizontal", size_hint_y=None, height="125dp",
                    radius=[18, 18, 18, 18], padding="8dp", spacing="8dp",
                    elevation=2, md_bg_color=self.card_bg_color,
                )

                if img and os.path.exists(img):
                    card.add_widget(Image(source=img, size_hint_x=None, width="105dp", allow_stretch=True, keep_ratio=True))
                else:
                    placeholder = MDBoxLayout(size_hint_x=None, width="105dp", md_bg_color=(0.20, 0.24, 0.31, 1))
                    placeholder.add_widget(MDIcon(icon="package-variant", halign="center", font_size="30sp"))
                    card.add_widget(placeholder)

                info = MDBoxLayout(orientation="vertical", spacing="2dp")
                info.add_widget(MDLabel(text=nom.title(), bold=True, font_style="H6"))
                stock_color = (0.95, 0.25, 0.20, 1) if qte <= 5 else (0.15, 0.70, 0.35, 1)
                info.add_widget(MDLabel(text=f"Stock : {qte}", theme_text_color="Custom", text_color=stock_color))
                info.add_widget(MDLabel(text=f"Vente : {pv:.0f} FCFA  •  Bénéfice/u : {pv-pa:.0f} FCFA", theme_text_color="Secondary"))
                if desc:
                    info.add_widget(MDLabel(text=desc, theme_text_color="Secondary", max_lines=1))
                card.add_widget(info)

                actions = MDBoxLayout(orientation="vertical", size_hint_x=None, width="45dp")
                edit = MDIconButton(icon="image-edit-outline", theme_icon_color="Custom", icon_color=(0.20, 0.55, 0.95, 1))
                edit.bind(on_release=lambda x, n=nom: self.ajouter_image_existante(n, refresh))
                actions.add_widget(edit)
                delete = MDIconButton(icon="delete-outline", theme_icon_color="Custom", icon_color=(0.95, 0.25, 0.20, 1))
                delete.bind(on_release=lambda x, n=nom: self.confirmer_suppression(n, refresh))
                actions.add_widget(delete)
                card.add_widget(actions)
                box.add_widget(card)

        search.bind(text=refresh)
        refresh()
        self._marquer_nav_actif("menu_stock")

    def ajouter_image_existante(self, nom, refresh):
        def selected(src):
            path = self.copier_image(src, nom)
            ajouter_image(nom, path)
            refresh()
            self.show_message("Image", "Image du produit mise à jour.")
        self.choisir_image(selected)

    def confirmer_suppression(self, nom, refresh):
        def supprimer(*args):
            supprimer_line_tab(nom)
            self.dialog.dismiss()
            refresh()
            self.mettre_a_jour_dashboard()
        self.dialog = MDDialog(
            title="Supprimer le produit ?",
            text=f"« {nom} » sera supprimé.",
            buttons=[
                MDFlatButton(text="Annuler", on_release=lambda x: self.dialog.dismiss()),
                SmoothButton(text="Supprimer", md_bg_color=(0.90, 0.20, 0.18, 1), on_release=supprimer),
            ],
        )
        self.dialog.open()

    # ------------------------------------------------------------------
    # RAPPORT (écran intégré, plus seulement l'ouverture du PDF)
    # ------------------------------------------------------------------
    def afficher_rapport(self):
        if not self.licence_active:
            return
        self.nettoyer()
        content = self.root.ids.frame_contenu
        gain, ventes, qte, nb = statistiques_jour()

        content.add_widget(MDLabel(text="Rapport journalier", font_style="H4", bold=True, size_hint_y=None, height="48dp"))
        content.add_widget(MDLabel(text=datetime.now().strftime("%A %d %B %Y"), theme_text_color="Secondary", size_hint_y=None, height="26dp"))

        stats = MDBoxLayout(spacing="8dp", size_hint_y=None, height="105dp")
        stats.add_widget(self.card("VENTES TOTALES", f"{ventes:,.0f} FCFA".replace(",", " "), "cash-multiple", (0.12, 0.50, 0.90, 1)))
        stats.add_widget(self.card("BÉNÉFICE TOTAL", f"{gain:,.0f} FCFA".replace(",", " "), "chart-line", (0.12, 0.65, 0.32, 1)))
        content.add_widget(stats)

        stats2 = MDBoxLayout(spacing="8dp", size_hint_y=None, height="105dp")
        stats2.add_widget(self.card("NOMBRE DE VENTES", str(nb), "receipt-text-outline", (0.95, 0.55, 0.10, 1)))
        stats2.add_widget(self.card("PRODUITS VENDUS", str(qte), "package-variant", (0.46, 0.32, 0.88, 1)))
        content.add_widget(stats2)

        content.add_widget(MDLabel(text="Liste des ventes", bold=True, size_hint_y=None, height="30dp"))
        scroll = MDScrollView()
        box = MDBoxLayout(orientation="vertical", spacing="2dp", size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        ventes_liste = ventes_du_jour()
        if not ventes_liste:
            box.add_widget(MDLabel(text="Aucune vente aujourd'hui.", theme_text_color="Secondary", size_hint_y=None, height="40dp"))
        else:
            for nom, q, total, heure, _rowid in ventes_liste:
                row = MDBoxLayout(size_hint_y=None, height="32dp")
                row.add_widget(MDLabel(text=heure or "--:--", size_hint_x=0.2, theme_text_color="Secondary", font_style="Caption"))
                row.add_widget(MDLabel(text=f"{nom.title()}  x{q}", size_hint_x=0.55, font_style="Caption"))
                row.add_widget(MDLabel(text=f"{total:.0f} FCFA", size_hint_x=0.25, halign="right",
                                        theme_text_color="Custom", text_color=(0.12, 0.65, 0.32, 1), font_style="Caption"))
                box.add_widget(row)

        scroll.add_widget(box)
        content.add_widget(scroll)

        def on_pdf(*args):
            if creer_pdf():
                rapport()

        btn = SmoothButton(text="SAUVEGARDER LE PDF", icon="file-pdf-box", md_bg_color=(0.46, 0.32, 0.88, 1), size_hint_y=None, height="52dp")
        btn.bind(on_release=on_pdf)
        content.add_widget(btn)
        self._marquer_nav_actif("menu_rapport")

    # ------------------------------------------------------------------
    # LICENCE
    # ------------------------------------------------------------------
    def mettre_a_jour_temps_restant(self):
        try:
            c_l.execute("SELECT expiration FROM duree")
            row = c_l.fetchone()
            if not self.licence_active:
                text = "Licence : non activée"
            elif row and row[0]:
                exp = datetime.strptime(row[0], "%d/%m/%Y")
                reste = exp - datetime.now()
                if reste.total_seconds() <= 0:
                    text = "Licence : expirée"
                elif reste.days >= 1:
                    text = f"Licence : {reste.days} jour(s)"
                else:
                    text = f"Licence : {int(reste.total_seconds() // 3600)} h"
            else:
                text = "Licence : --"
        except Exception:
            text = "Licence : --"
        if self.root and "lbl_temps_restant" in self.root.ids:
            self.root.ids.lbl_temps_restant.text = text

    def ouvrir_licence(self):
        if self.dialog:
            try:
                self.dialog.dismiss()
            except Exception:
                pass

        creer_doc()
        box = MDBoxLayout(orientation="vertical", spacing="10dp", padding="14dp", size_hint_y=None, height="300dp")
        box.add_widget(MDLabel(text="Envoyez votre ID Machine à EASYBOUTIK via WhatsApp,\npuis collez ci-dessous le code reçu en retour.", halign="center"))
        id_label = MDLabel(text=f"ID Machine : {obt_id_m_u()}", halign="center", bold=True,
                            theme_text_color="Custom", text_color=(0.12, 0.50, 0.90, 1), size_hint_y=None, height="30dp")
        box.add_widget(id_label)
        key = MDTextField(hint_text="Code de licence reçu")
        box.add_widget(key)

        def validate(*args):
            ok, exp, forfait = verif_code_licence(key.text.strip())
            if ok:
                save_licence(key.text.strip(), exp, forfait)
                save_expir(exp)
                self.licence_active = True
                self.dialog.dismiss()
                self.appliquer_couleurs()
                self.mettre_a_jour_temps_restant()
                self.afficher_accueil()
                self.show_message("Bienvenue", f"Forfait {forfait} actif jusqu'au {exp}")
            else:
                self.show_message("Erreur", "Code invalide, corrompu, ou émis pour un autre appareil.")
                key.text = ""

        b = SmoothButton(text="Activer la licence", icon="key-outline", md_bg_color=(0.12, 0.65, 0.32, 1))
        b.bind(on_release=validate)
        box.add_widget(b)
        self.dialog = MDDialog(title="Activation EASYBOUTIK", type="custom", content_cls=box, auto_dismiss=False)
        self.dialog.open()

    def sauvegarder_pdf(self):
        if not self.licence_active:
            return
        creer_pdf()

    def ouvrir_rapport(self):
        # Conservé pour compatibilité : ouvre directement le PDF sans passer par l'écran.
        if not self.licence_active:
            return
        rapport()


if __name__ == "__main__":
    EasyBoutikApp().run()
