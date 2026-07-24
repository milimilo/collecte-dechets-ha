# Collecte des déchets Rueil-Malmaison — intégration Home Assistant

Affiche les **prochaines collectes de déchets** selon votre adresse à
Rueil-Malmaison (92), pour les 5 flux (ordures ménagères, emballages, verre,
encombrants, déchets verts) collectés en porte-à-porte.

Les données proviennent de l'[open data du Département des Hauts-de-Seine](https://opendata.hauts-de-seine.fr/).
Vous saisissez votre adresse une seule fois à la configuration : l'intégration
la géocode (Base Adresse Nationale), détermine dans quel secteur elle tombe pour
chaque flux, puis calcule les prochaines dates.

## Flux pris en charge

| Flux | Jeu de données | Particularité gérée |
|------|----------------|---------------------|
| Déchets verts | `collecte-des-dechets-vegetaux` | saison mars → mi-décembre |
| Ordures ménagères | `collecte-des-ordures-menageres` | plusieurs jours/semaine |
| Emballages | `collecte-des-emballages` | hebdomadaire |
| Encombrants | `encombrant` | semaine paire / impaire |
| Verre | `collecte-du-verre` | semaine paire / impaire |

## Ce que ça crée

Un appareil **« Rueil-Malmaison »** regroupant :

- **5 capteurs** `sensor.rueil_malmaison_*` (un par flux), de type *date*, indiquant
  la prochaine collecte. Attributs : `jour`, `frequence`, `periode`, `moment`
  (Matin/Soir), `jours_avant`, `prochaines_collectes` (6 prochaines dates).
- **1 calendrier** `calendar.rueil_malmaison_collectes` regroupant toutes les
  collectes à venir, tous flux confondus.

## Installation via HACS

### 1. Ajouter le dépôt personnalisé dans HACS

1. HACS → menu ⋮ en haut à droite → **Dépôts personnalisés**
2. URL : `https://github.com/milimilo/collecte-dechets-ha`
3. Type : **Intégration** → **Ajouter**
4. Cherchez « Collecte des déchets Rueil-Malmaison » → **Télécharger**
5. **Redémarrez Home Assistant**

### 2. Configurer

**Paramètres → Appareils et services → Ajouter une intégration** →
« Collecte des déchets Rueil-Malmaison » → saisissez votre adresse.

## Installation manuelle (sans HACS)

Copiez le dossier `custom_components/collecte_dechets/` dans le dossier
`config/custom_components/` de votre Home Assistant, puis redémarrez.

## Notes

- Couvre uniquement Rueil-Malmaison.
- Rafraîchissement toutes les 12 h ; aucune clé API requise.
- « Moment = Soir » signifie collecte le soir même : sortez le bac dans l'après-midi.
- Hors saison, le capteur des déchets verts pointe automatiquement vers la
  première collecte de l'année suivante.
