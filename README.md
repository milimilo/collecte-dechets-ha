# Déchets verts Rueil-Malmaison — intégration Home Assistant

Affiche les **prochaines collectes de déchets végétaux** selon votre secteur
d'habitation à Rueil-Malmaison (92).

Les données proviennent de l'[open data du Département des Hauts-de-Seine](https://opendata.hauts-de-seine.fr/explore/dataset/fr-219200631-collecte-des-dechets-vegetaux/).
Vous saisissez votre adresse une seule fois à la configuration : l'intégration
la géocode (Base Adresse Nationale), détermine dans quel secteur de collecte
elle tombe, puis calcule les prochaines dates.

## Ce que ça crée

Un appareil « Déchets verts » avec :

| Entité | Type | Contenu |
|--------|------|---------|
| `sensor.dechets_verts_prochaine_collecte` | date | Date de la prochaine collecte. Attributs : jour, fréquence, période, prochaines dates… |
| `sensor.dechets_verts_jours_avant_collecte` | nombre | Nombre de jours restants |
| `calendar.dechets_verts_collecte_des_dechets_verts` | calendrier | Toutes les collectes à venir |

## Installation via HACS

### 1. Publier le dépôt (une fois)

HACS installe depuis un dépôt GitHub. Le code est hébergé sur
`https://github.com/milimilo/ha-dechets-verts-rueil`.

### 2. Ajouter le dépôt personnalisé dans HACS

1. HACS → menu ⋮ en haut à droite → **Dépôts personnalisés**
2. URL : `https://github.com/milimilo/ha-dechets-verts-rueil`
3. Type : **Intégration** → **Ajouter**
4. Cherchez « Déchets verts Rueil-Malmaison » dans HACS → **Télécharger**
5. **Redémarrez Home Assistant**

### 3. Configurer

**Paramètres → Appareils et services → Ajouter une intégration** →
« Déchets verts Rueil-Malmaison » → saisissez votre adresse.

## Installation manuelle (sans HACS)

Copiez le dossier `custom_components/dechets_verts_rueil/` dans le dossier
`config/custom_components/` de votre Home Assistant, puis redémarrez.

## Exemple de notification (la veille au soir)

```yaml
automation:
  - alias: "Rappel déchets verts"
    trigger:
      - platform: time
        at: "19:00:00"
    condition:
      - condition: template
        value_template: "{{ state_attr('sensor.dechets_verts_prochaine_collecte','jours_avant') == 1 }}"
    action:
      - service: notify.notify
        data:
          title: "🌿 Déchets verts demain"
          message: >
            Collecte demain matin. Pensez à sortir le bac ce soir.
```

## Notes

- Couvre uniquement Rueil-Malmaison (jeu de données `fr-219200631`), découpé en
  4 secteurs (2 avec collecte hebdomadaire, 2 sans).
- Rafraîchissement toutes les 12 h ; aucune clé API requise.
- La saison de collecte va de début mars à mi-décembre : hors de cette période,
  les capteurs pointent automatiquement vers la première collecte de l'année suivante.
