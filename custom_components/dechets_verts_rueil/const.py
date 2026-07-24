"""Constantes de l'intégration Déchets verts Rueil-Malmaison."""

DOMAIN = "dechets_verts_rueil"

# API Opendatasoft du Département des Hauts-de-Seine (collecte des déchets végétaux)
DATASET_URL = (
    "https://opendata.hauts-de-seine.fr/api/explore/v2.1/catalog/"
    "datasets/fr-219200631-collecte-des-dechets-vegetaux/records"
)

# Base Adresse Nationale (géocodage gratuit, sans clé)
GEOCODE_URL = "https://api-adresse.data.gouv.fr/search/"

CONF_ADDRESS = "address"
CONF_LAT = "latitude"
CONF_LON = "longitude"

MANUFACTURER = "Département des Hauts-de-Seine"
