"""Criteres de selection partages : collecte v1, rapport qualite, comparaison v0/v1.

Valides par l'equipe Data le 10 nov. 2026. Ordre des listes = priorite :
un produit present dans plusieurs familles recoit la premiere query_category.
"""

# Mention d'un arome dans la liste d'ingredients (division Flavors)
AROME_RX = r"(?i)ar[oô]mes?\b|aromatis|extrait (?:naturel )?de vanille|gousse de vanille|flavou?r"

# Ingredient parfumant : parfum/fragrance/aroma (INCI), huile essentielle,
# allergenes parfumants (Reglement UE 1223/2009, annexe III)
PARFUM_RX = (
    r"(?i)parfum|fragrance|\baroma\b|essential oil|huile essentielle|limonene|linalool"
    r"|geraniol|citronellol|citral|coumarin|eugenol|benzyl (?:alcohol|benzoate|salicylate)"
    r"|hexyl cinnamal"
)

# Tags exclus de Flavors quelle que soit la famille
FLAVORS_EXCLUS = ["en:cheeses", "en:biscuits", "en:biscuits-and-cakes", "en:alcoholic-beverages"]

# Boissons proteinees : pas de tag dedie fiable -> tag protein-shakes ou nom "proteine"
# associe a un tag boisson / preparation / poudre proteinee
PROTEINE_SQL = (
    "(list_contains(categories_tags, 'en:protein-shakes') OR "
    "(regexp_matches(product_name, '(?i)prot[eé]in') AND list_has_any(categories_tags, "
    "['en:beverages', 'en:dairy-drinks', 'en:beverage-preparations', 'en:protein-powders'])))"
)

# Format des boissons proteinees
POUDRE_TAGS = ["en:protein-powders", "en:beverage-preparations", "en:instant-beverages"]
POUDRE_NOM_RX = r"(?i)poudre|powder|\bwhey\b|isolat|\bgainer\b|\bdose"

FLAVORS_FAMILLES = [
    ("boissons_proteinees", None),  # cf. PROTEINE_SQL
    ("boissons_vegetales", [
        "en:plant-based-milk-alternatives", "en:soy-based-drinks", "en:oat-based-drinks",
        "en:almond-based-drinks", "en:rice-based-drinks", "en:coconut-based-drinks",
    ]),
    ("boissons_lactees", [
        "en:dairy-drinks", "en:flavoured-milks", "en:milkshakes", "en:fermented-milk-drinks",
        "en:yogurt-drinks", "en:chocolate-milks",
    ]),
    ("desserts_aromatises", [
        "en:flavoured-yogurts", "en:vanilla-yogurt", "en:flavoured-fermented-dairy-desserts",
        "en:entremets-mousses-and-creamy-puddings", "en:creamy-puddings", "en:sweet-mousses",
        "en:dairy-mousses", "en:chocolate-mousses", "en:rice-puddings", "en:flans",
        "en:creme-brulee", "en:non-dairy-desserts", "en:non-dairy-yogurts",
    ]),
    ("boissons_aromatisees", [
        "en:sodas", "en:colas", "en:iced-teas", "en:flavoured-syrups", "en:energy-drinks",
        "en:fruit-soft-drinks", "en:lemonades", "en:tonic-water", "en:kombuchas",
        "en:flavored-waters",
    ]),
]

# (query_category, tags, filtre parfume obligatoire)
FRAGRANCE_FAMILLES = [
    ("parfums", ["en:perfumes", "en:eau-de-toilette", "en:women-perfumes", "en:cologne",
                 "en:men-perfumes"], False),
    ("savons_rasage", ["en:shaving-soaps"], True),
    ("shampoings_gels_douche", ["en:shampoos-shower-gels"], True),
    ("deodorants", ["en:deodorants", "en:roll-on-deodorants", "en:deodorants-sticks",
                    "fr:deodorant-a-la-pierre-d-alun", "en:deodorants-anti-transpirants",
                    "fr:deodorants-sticks", "fr:deodorant"], True),
    ("savons", ["en:soaps", "en:marseille-soaps", "en:liquid-soaps", "fr:savons-liquides",
                "en:dermatological-soaps", "fr:savon", "en:bar-soaps", "fr:savon-surgras",
                "fr:savons-surgras", "fr:savons", "en:aleppo-soaps", "fr:savon-de-marseille"],
     False),
    ("gels_douche", ["en:shower-gels", "fr:cremes-douche", "en:gels-douche", "fr:gel-douche",
                     "fr:gel-douche-gommant", "fr:huiles-douche", "fr:gels-douche-surgras"],
     False),
]

FLAVORS_PAR_CATEGORIE = 200
GRAINE = 42
