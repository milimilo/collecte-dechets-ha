"""Constantes de l'intégration Collecte des déchets Rueil-Malmaison."""

DOMAIN = "collecte_dechets"

# Modèle d'URL de l'API Opendatasoft du Département des Hauts-de-Seine
DATASET_URL = (
    "https://opendata.hauts-de-seine.fr/api/explore/v2.1/catalog/"
    "datasets/{dataset}/records"
)

# Base Adresse Nationale (géocodage gratuit, sans clé)
GEOCODE_URL = "https://api-adresse.data.gouv.fr/search/"

CONF_ADDRESS = "address"
CONF_LAT = "latitude"
CONF_LON = "longitude"

MANUFACTURER = "Département des Hauts-de-Seine"
DEVICE_NAME = "Rueil-Malmaison"

# Les 5 flux collectés en porte-à-porte à Rueil-Malmaison.
# Tous partagent le même schéma (jours, frequenc, perioann, periojou, geo_shape).
FLOWS: dict[str, dict[str, str]] = {
    "dechets_verts": {
        "dataset": "fr-219200631-collecte-des-dechets-vegetaux",
        "label": "Déchets verts",
        "icon": "mdi:leaf",
    },
    "ordures_menageres": {
        "dataset": "fr-219200631-collecte-des-ordures-menageres",
        "label": "Ordures ménagères",
        "icon": "mdi:trash-can",
    },
    "emballages": {
        "dataset": "fr-219200631-collecte-des-emballages",
        "label": "Emballages",
        "icon": "mdi:recycle",
    },
    "encombrants": {
        "dataset": "fr-219200631-encombrant",
        "label": "Encombrants",
        "icon": "mdi:sofa",
    },
    "verre": {
        "dataset": "fr-219200631-collecte-du-verre",
        "label": "Verre",
        "icon": "mdi:bottle-wine",
    },
}
