# Veille stock iPhone Duo — Blanc stellaire 256 Go — Apple Store Île-de-France

Interroge l'endpoint public d'apple.com qui alimente le bouton « Vérifier la disponibilité »
(`/fr/shop/retail/pickup-message`) et envoie un push sur ton iPhone via **ntfy** dès qu'un
des 9 Apple Store d'IDF (Opéra, Marché Saint-Germain, Champs-Élysées, Les Quatre Temps,
Rosny 2, Vélizy 2, Parly 2, Carré Sénart, Val d'Europe) a le modèle en retrait.

Référence France du modèle : **MK2D4F/A** (iPhone Duo, Blanc stellaire, 256 Go, 2 339 €).
Autres références FR : MK2E4F/A (Ciel nocturne 256), MK2F4F/A (Blanc 512), MK2H4F/A (Blanc 1 To), MK2K4F/A (Blanc 2 To).

## Mise en route (5 minutes)

1. **ntfy sur l'iPhone** : installe l'app *ntfy* (App Store, gratuite), abonne-toi à un topic
   difficile à deviner, ex. `duo-philippe-8f3a`.
2. **Test local sur le Mac** :
   ```bash
   NTFY_TOPIC=duo-philippe-8f3a python3 check_stock.py
   ```
   Tu dois voir les 9 magasins avec leur statut. Pour boucler toutes les 2 min :
   ```bash
   NTFY_TOPIC=duo-philippe-8f3a python3 check_stock.py --watch 120
   ```
3. **Agent 24/7 gratuit (GitHub Actions)** : pousse ce dossier dans un repo GitHub **public**
   (les Actions planifiées y sont gratuites), ajoute le secret `NTFY_TOPIC`
   (Settings → Secrets and variables → Actions), puis lance une fois le workflow à la main
   (onglet Actions → *Run workflow*). Il tourne ensuite toutes les 5 min.

## Quand l'alerte arrive

Ouvre le lien de la notification → apple.com/fr/shop/buy-iphone/iphone-duo → Blanc stellaire,
256 Go → **Retrait** → choisis le magasin et un créneau. Le stock part en quelques minutes :
avoir l'Apple ID et la carte déjà enregistrés dans l'app Apple Store fait gagner la course.

## Limites

- Endpoint non documenté : Apple peut le modifier ou le bloquer (403/541). Le script
  s'arrête proprement, il ne spamme pas.
- Ne voit que le stock « retrait en magasin » réservable en ligne, pas le walk-in.
- GitHub planifie à ±quelques minutes près.
