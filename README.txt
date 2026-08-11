EASYBOUTIK Android v3.4

Corrections apportées à v3.3 :
- licence.py : les alertes "horloge modifiée" et "tentative de reset" fermaient
  l'application avant que le dialogue ait pu s'afficher (sys.exit() appelé
  juste après .open(), qui est non bloquant). Le sys.exit() est maintenant
  différé de 2.5s pour laisser le temps de lire le message.
- data.py : ajout d'une colonne "Heure" sur les ventes + fonction
  ventes_du_jour() pour lister les ventes horodatées du jour.
- data.py : ouverture du rapport PDF sécurisée sur Mac (repli sur "open"
  avant "xdg-open").

Interface (main.py) :
- Icônes Material Design à la place des emojis (nav basse, dashboard, stock).
- Barre de navigation basse : icône + libellé empilés, écran actif surligné
  (style app mobile moderne, cf. maquette).
- Thème clair par défaut (bascule sombre toujours disponible).
- Écran "Vendre" : sélection du produit par carte avec miniature + stepper
  de quantité (-/+) au lieu d'un simple champ numérique.
- Nouvel écran "Rapport" intégré : cartes de statistiques (ventes, bénéfice,
  nombre de ventes, produits vendus) + liste horodatée des ventes du jour,
  avec un bouton pour sauvegarder/ouvrir le PDF. Auparavant "Rapports"
  ouvrait directement le PDF sans rien montrer dans l'app.

Le style reste un glassmorphism léger (transparence + bordure fine, sans
flou temps réel) pour rester fluide sur Android, comme dans v3.3.
