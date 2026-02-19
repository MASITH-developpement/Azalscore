"""
AZALS MODULE - PCG 2025: Compte Standard
==========================================

Plan Comptable Général 2025 - Comptes standards conformes à l'ANC
(Autorité des Normes Comptables).

Référence: Règlement ANC n°2014-03 modifié (dernière mise à jour 2025)
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class PCG2025Account:
    """Définition d'un compte PCG 2025."""
    number: str
    label: str
    pcg_class: str
    normal_balance: Literal["D", "C"]  # D=Débit, C=Crédit
    is_summary: bool = False  # Compte de regroupement
    required_for: list[str] | None = None  # BIC, BNC, IS, etc.
    notes: str | None = None


# ============================================================================
# CLASSE 1 - COMPTES DE CAPITAUX
# ============================================================================

PCG2025_CLASSE_1 = [
    # 10 - Capital et réserves
    PCG2025Account("10", "Capital et réserves", "1", "C", True),
    PCG2025Account("101", "Capital", "1", "C", True),
    PCG2025Account("1011", "Capital souscrit - non appelé", "1", "C"),
    PCG2025Account("1012", "Capital souscrit - appelé, non versé", "1", "C"),
    PCG2025Account("1013", "Capital souscrit - appelé, versé", "1", "C"),
    PCG2025Account("102", "Fonds fiduciaires", "1", "C"),
    PCG2025Account("103", "Écarts de réévaluation", "1", "C"),
    PCG2025Account("104", "Primes liées au capital social", "1", "C", True),
    PCG2025Account("1041", "Primes d'émission", "1", "C"),
    PCG2025Account("1042", "Primes de fusion", "1", "C"),
    PCG2025Account("1043", "Primes d'apport", "1", "C"),
    PCG2025Account("1044", "Primes de conversion d'obligations en actions", "1", "C"),
    PCG2025Account("105", "Écarts de réévaluation", "1", "C", True),
    PCG2025Account("1051", "Réserve spéciale de réévaluation", "1", "C"),
    PCG2025Account("1052", "Écart de réévaluation libre", "1", "C"),
    PCG2025Account("1053", "Réserve de réévaluation", "1", "C"),
    PCG2025Account("106", "Réserves", "1", "C", True),
    PCG2025Account("1061", "Réserve légale", "1", "C"),
    PCG2025Account("1063", "Réserves statutaires ou contractuelles", "1", "C"),
    PCG2025Account("1064", "Réserves réglementées", "1", "C"),
    PCG2025Account("1068", "Autres réserves", "1", "C"),
    PCG2025Account("107", "Écart d'équivalence", "1", "C"),
    PCG2025Account("108", "Compte de l'exploitant", "1", "C", notes="Entreprises individuelles"),
    PCG2025Account("109", "Actionnaires - Capital souscrit non appelé", "1", "D"),

    # 11 - Report à nouveau
    PCG2025Account("11", "Report à nouveau", "1", "C", True),
    PCG2025Account("110", "Report à nouveau (solde créditeur)", "1", "C"),
    PCG2025Account("119", "Report à nouveau (solde débiteur)", "1", "D"),

    # 12 - Résultat de l'exercice
    PCG2025Account("12", "Résultat de l'exercice", "1", "C", True),
    PCG2025Account("120", "Résultat de l'exercice (bénéfice)", "1", "C"),
    PCG2025Account("129", "Résultat de l'exercice (perte)", "1", "D"),

    # 13 - Subventions d'investissement
    PCG2025Account("13", "Subventions d'investissement", "1", "C", True),
    PCG2025Account("131", "Subventions d'équipement", "1", "C"),
    PCG2025Account("138", "Autres subventions d'investissement", "1", "C"),
    PCG2025Account("139", "Subventions d'investissement inscrites au compte de résultat", "1", "D"),

    # 14 - Provisions réglementées
    PCG2025Account("14", "Provisions réglementées", "1", "C", True),
    PCG2025Account("142", "Provisions réglementées relatives aux immobilisations", "1", "C"),
    PCG2025Account("143", "Provisions réglementées relatives aux stocks", "1", "C"),
    PCG2025Account("144", "Provisions réglementées relatives aux autres éléments d'actif", "1", "C"),
    PCG2025Account("145", "Amortissements dérogatoires", "1", "C"),
    PCG2025Account("146", "Provision spéciale de réévaluation", "1", "C"),
    PCG2025Account("147", "Plus-values réinvesties", "1", "C"),
    PCG2025Account("148", "Autres provisions réglementées", "1", "C"),

    # 15 - Provisions pour risques et charges
    PCG2025Account("15", "Provisions pour risques et charges", "1", "C", True),
    PCG2025Account("151", "Provisions pour risques", "1", "C", True),
    PCG2025Account("1511", "Provisions pour litiges", "1", "C"),
    PCG2025Account("1514", "Provisions pour amendes et pénalités", "1", "C"),
    PCG2025Account("1515", "Provisions pour pertes de change", "1", "C"),
    PCG2025Account("1516", "Provisions pour pertes sur contrats", "1", "C"),
    PCG2025Account("1518", "Autres provisions pour risques", "1", "C"),
    PCG2025Account("153", "Provisions pour pensions et obligations similaires", "1", "C"),
    PCG2025Account("154", "Provisions pour restructurations", "1", "C"),
    PCG2025Account("155", "Provisions pour impôts", "1", "C"),
    PCG2025Account("156", "Provisions pour renouvellement des immobilisations", "1", "C"),
    PCG2025Account("157", "Provisions pour charges à répartir sur plusieurs exercices", "1", "C"),
    PCG2025Account("158", "Autres provisions pour charges", "1", "C"),

    # 16 - Emprunts et dettes assimilées
    PCG2025Account("16", "Emprunts et dettes assimilées", "1", "C", True),
    PCG2025Account("161", "Emprunts obligataires convertibles", "1", "C"),
    PCG2025Account("163", "Autres emprunts obligataires", "1", "C"),
    PCG2025Account("164", "Emprunts auprès des établissements de crédit", "1", "C", True),
    PCG2025Account("1641", "Emprunts - à plus d'un an à l'origine", "1", "C"),
    PCG2025Account("1643", "Emprunts - moins d'un an à l'origine (facilité de trésorerie)", "1", "C"),
    PCG2025Account("1644", "Emprunts de l'exercice non échus", "1", "C"),
    PCG2025Account("165", "Dépôts et cautionnements reçus", "1", "C"),
    PCG2025Account("166", "Participation des salariés aux résultats", "1", "C", True),
    PCG2025Account("1661", "Comptes bloqués", "1", "C"),
    PCG2025Account("1662", "Fonds de participation", "1", "C"),
    PCG2025Account("167", "Emprunts et dettes assortis de conditions particulières", "1", "C"),
    PCG2025Account("168", "Autres emprunts et dettes assimilées", "1", "C", True),
    PCG2025Account("1681", "Autres emprunts", "1", "C"),
    PCG2025Account("1687", "Autres dettes", "1", "C"),
    PCG2025Account("1688", "Intérêts courus", "1", "C"),
    PCG2025Account("169", "Primes de remboursement des obligations", "1", "D"),

    # 17 - Dettes rattachées à des participations
    PCG2025Account("17", "Dettes rattachées à des participations", "1", "C", True),
    PCG2025Account("171", "Dettes rattachées à des participations (groupe)", "1", "C"),
    PCG2025Account("174", "Dettes rattachées à des participations (hors groupe)", "1", "C"),
    PCG2025Account("178", "Dettes rattachées à des sociétés en participation", "1", "C"),

    # 18 - Comptes de liaison des établissements
    PCG2025Account("18", "Comptes de liaison des établissements et sociétés en participation", "1", "C", True),
    PCG2025Account("181", "Comptes de liaison des établissements", "1", "C"),
    PCG2025Account("186", "Biens et prestations de services échangés entre établissements", "1", "C"),
    PCG2025Account("188", "Comptes de liaison des sociétés en participation", "1", "C"),
]


# ============================================================================
# CLASSE 2 - COMPTES D'IMMOBILISATIONS
# ============================================================================

PCG2025_CLASSE_2 = [
    # 20 - Immobilisations incorporelles
    PCG2025Account("20", "Immobilisations incorporelles", "2", "D", True),
    PCG2025Account("201", "Frais d'établissement", "2", "D"),
    PCG2025Account("203", "Frais de recherche et de développement", "2", "D"),
    PCG2025Account("205", "Concessions et droits similaires, brevets, licences, marques", "2", "D"),
    PCG2025Account("206", "Droit au bail", "2", "D"),
    PCG2025Account("207", "Fonds commercial", "2", "D"),
    PCG2025Account("208", "Autres immobilisations incorporelles", "2", "D"),

    # 21 - Immobilisations corporelles
    PCG2025Account("21", "Immobilisations corporelles", "2", "D", True),
    PCG2025Account("211", "Terrains", "2", "D", True),
    PCG2025Account("2111", "Terrains nus", "2", "D"),
    PCG2025Account("2112", "Terrains aménagés", "2", "D"),
    PCG2025Account("2113", "Sous-sols et sur-sols", "2", "D"),
    PCG2025Account("2114", "Terrains de gisement", "2", "D"),
    PCG2025Account("2115", "Terrains bâtis", "2", "D"),
    PCG2025Account("212", "Agencements et aménagements de terrains", "2", "D"),
    PCG2025Account("213", "Constructions", "2", "D", True),
    PCG2025Account("2131", "Bâtiments", "2", "D"),
    PCG2025Account("2135", "Installations générales, agencements, aménagements", "2", "D"),
    PCG2025Account("2138", "Ouvrages d'infrastructure", "2", "D"),
    PCG2025Account("214", "Constructions sur sol d'autrui", "2", "D"),
    PCG2025Account("215", "Installations techniques, matériel et outillage industriels", "2", "D", True),
    PCG2025Account("2151", "Installations complexes spécialisées", "2", "D"),
    PCG2025Account("2153", "Installations à caractère spécifique", "2", "D"),
    PCG2025Account("2154", "Matériel industriel", "2", "D"),
    PCG2025Account("2155", "Outillage industriel", "2", "D"),
    PCG2025Account("218", "Autres immobilisations corporelles", "2", "D", True),
    PCG2025Account("2181", "Installations générales, agencements, aménagements divers", "2", "D"),
    PCG2025Account("2182", "Matériel de transport", "2", "D"),
    PCG2025Account("2183", "Matériel de bureau et matériel informatique", "2", "D"),
    PCG2025Account("2184", "Mobilier", "2", "D"),
    PCG2025Account("2185", "Cheptel", "2", "D"),
    PCG2025Account("2186", "Emballages récupérables", "2", "D"),

    # 22 - Immobilisations mises en concession
    PCG2025Account("22", "Immobilisations mises en concession", "2", "D", True),

    # 23 - Immobilisations en cours
    PCG2025Account("23", "Immobilisations en cours", "2", "D", True),
    PCG2025Account("231", "Immobilisations corporelles en cours", "2", "D"),
    PCG2025Account("232", "Immobilisations incorporelles en cours", "2", "D"),
    PCG2025Account("237", "Avances et acomptes versés sur immobilisations incorporelles", "2", "D"),
    PCG2025Account("238", "Avances et acomptes versés sur commandes d'immobilisations corporelles", "2", "D"),

    # 26 - Participations et créances rattachées
    PCG2025Account("26", "Participations et créances rattachées à des participations", "2", "D", True),
    PCG2025Account("261", "Titres de participation", "2", "D"),
    PCG2025Account("262", "Titres représentatifs de droits de créance", "2", "D"),
    PCG2025Account("266", "Autres formes de participation", "2", "D"),
    PCG2025Account("267", "Créances rattachées à des participations", "2", "D"),
    PCG2025Account("268", "Créances rattachées à des sociétés en participation", "2", "D"),
    PCG2025Account("269", "Versements restant à effectuer sur titres de participation non libérés", "2", "C"),

    # 27 - Autres immobilisations financières
    PCG2025Account("27", "Autres immobilisations financières", "2", "D", True),
    PCG2025Account("271", "Titres immobilisés autres que les titres immobilisés de l'activité de portefeuille", "2", "D"),
    PCG2025Account("272", "Titres immobilisés - droits de créance", "2", "D"),
    PCG2025Account("273", "Titres immobilisés de l'activité de portefeuille (TIAP)", "2", "D"),
    PCG2025Account("274", "Prêts", "2", "D", True),
    PCG2025Account("2741", "Prêts participatifs", "2", "D"),
    PCG2025Account("2742", "Prêts aux associés", "2", "D"),
    PCG2025Account("2743", "Prêts au personnel", "2", "D"),
    PCG2025Account("2748", "Autres prêts", "2", "D"),
    PCG2025Account("275", "Dépôts et cautionnements versés", "2", "D"),
    PCG2025Account("276", "Autres créances immobilisées", "2", "D"),
    PCG2025Account("279", "Versements restant à effectuer sur titres immobilisés non libérés", "2", "C"),

    # 28 - Amortissements des immobilisations
    PCG2025Account("28", "Amortissements des immobilisations", "2", "C", True),
    PCG2025Account("280", "Amortissements des immobilisations incorporelles", "2", "C", True),
    PCG2025Account("2801", "Amortissements des frais d'établissement", "2", "C"),
    PCG2025Account("2803", "Amortissements des frais de recherche et de développement", "2", "C"),
    PCG2025Account("2805", "Amortissements des concessions et droits similaires", "2", "C"),
    PCG2025Account("2807", "Amortissements du fonds commercial", "2", "C"),
    PCG2025Account("2808", "Amortissements des autres immobilisations incorporelles", "2", "C"),
    PCG2025Account("281", "Amortissements des immobilisations corporelles", "2", "C", True),
    PCG2025Account("2811", "Amortissements des terrains de gisement", "2", "C"),
    PCG2025Account("2812", "Amortissements des agencements, aménagements de terrains", "2", "C"),
    PCG2025Account("2813", "Amortissements des constructions", "2", "C"),
    PCG2025Account("2814", "Amortissements des constructions sur sol d'autrui", "2", "C"),
    PCG2025Account("2815", "Amortissements des installations, matériel et outillage", "2", "C"),
    PCG2025Account("2818", "Amortissements des autres immobilisations corporelles", "2", "C"),
    PCG2025Account("282", "Amortissements des immobilisations mises en concession", "2", "C"),

    # 29 - Dépréciations des immobilisations
    PCG2025Account("29", "Dépréciations des immobilisations", "2", "C", True),
    PCG2025Account("290", "Dépréciations des immobilisations incorporelles", "2", "C"),
    PCG2025Account("291", "Dépréciations des immobilisations corporelles", "2", "C"),
    PCG2025Account("293", "Dépréciations des immobilisations en cours", "2", "C"),
    PCG2025Account("296", "Dépréciations des participations et créances rattachées", "2", "C"),
    PCG2025Account("297", "Dépréciations des autres immobilisations financières", "2", "C"),
]


# ============================================================================
# CLASSE 3 - COMPTES DE STOCKS ET EN-COURS
# ============================================================================

PCG2025_CLASSE_3 = [
    # 31 - Matières premières
    PCG2025Account("31", "Matières premières (et fournitures)", "3", "D", True),
    PCG2025Account("311", "Matières (ou groupe) A", "3", "D"),
    PCG2025Account("312", "Matières (ou groupe) B", "3", "D"),
    PCG2025Account("317", "Fournitures A, B, C...", "3", "D"),

    # 32 - Autres approvisionnements
    PCG2025Account("32", "Autres approvisionnements", "3", "D", True),
    PCG2025Account("321", "Matières consommables", "3", "D"),
    PCG2025Account("322", "Fournitures consommables", "3", "D"),
    PCG2025Account("326", "Emballages", "3", "D", True),
    PCG2025Account("3261", "Emballages perdus", "3", "D"),
    PCG2025Account("3265", "Emballages récupérables non identifiables", "3", "D"),
    PCG2025Account("3267", "Emballages à usage mixte", "3", "D"),

    # 33 - En-cours de production de biens
    PCG2025Account("33", "En-cours de production de biens", "3", "D", True),
    PCG2025Account("331", "Produits en cours", "3", "D"),
    PCG2025Account("335", "Travaux en cours", "3", "D"),

    # 34 - En-cours de production de services
    PCG2025Account("34", "En-cours de production de services", "3", "D", True),
    PCG2025Account("341", "Études en cours", "3", "D"),
    PCG2025Account("345", "Prestations de services en cours", "3", "D"),

    # 35 - Stocks de produits
    PCG2025Account("35", "Stocks de produits", "3", "D", True),
    PCG2025Account("351", "Produits intermédiaires", "3", "D"),
    PCG2025Account("355", "Produits finis", "3", "D"),
    PCG2025Account("358", "Produits résiduels (déchets, rebuts)", "3", "D"),

    # 37 - Stocks de marchandises
    PCG2025Account("37", "Stocks de marchandises", "3", "D", True),
    PCG2025Account("371", "Marchandises (ou groupe) A", "3", "D"),
    PCG2025Account("372", "Marchandises (ou groupe) B", "3", "D"),

    # 39 - Dépréciations des stocks et en-cours
    PCG2025Account("39", "Dépréciations des stocks et en-cours", "3", "C", True),
    PCG2025Account("391", "Dépréciations des matières premières", "3", "C"),
    PCG2025Account("392", "Dépréciations des autres approvisionnements", "3", "C"),
    PCG2025Account("393", "Dépréciations des en-cours de production de biens", "3", "C"),
    PCG2025Account("394", "Dépréciations des en-cours de production de services", "3", "C"),
    PCG2025Account("395", "Dépréciations des stocks de produits", "3", "C"),
    PCG2025Account("397", "Dépréciations des stocks de marchandises", "3", "C"),
]


# ============================================================================
# CLASSE 4 - COMPTES DE TIERS
# ============================================================================

PCG2025_CLASSE_4 = [
    # 40 - Fournisseurs et comptes rattachés
    PCG2025Account("40", "Fournisseurs et comptes rattachés", "4", "C", True),
    PCG2025Account("401", "Fournisseurs", "4", "C", True),
    PCG2025Account("4011", "Fournisseurs - Achats de biens et prestations de services", "4", "C"),
    PCG2025Account("4017", "Fournisseurs - Retenues de garantie", "4", "C"),
    PCG2025Account("403", "Fournisseurs - Effets à payer", "4", "C"),
    PCG2025Account("404", "Fournisseurs d'immobilisations", "4", "C", True),
    PCG2025Account("4041", "Fournisseurs d'immobilisations - Achats", "4", "C"),
    PCG2025Account("4047", "Fournisseurs d'immobilisations - Retenues de garantie", "4", "C"),
    PCG2025Account("405", "Fournisseurs d'immobilisations - Effets à payer", "4", "C"),
    PCG2025Account("408", "Fournisseurs - Factures non parvenues", "4", "C"),
    PCG2025Account("409", "Fournisseurs débiteurs", "4", "D", True),
    PCG2025Account("4091", "Fournisseurs - Avances et acomptes versés", "4", "D"),
    PCG2025Account("4096", "Fournisseurs - Créances pour emballages et matériel à rendre", "4", "D"),
    PCG2025Account("4097", "Fournisseurs - Autres avoirs", "4", "D"),
    PCG2025Account("4098", "RRR à obtenir et autres avoirs non encore reçus", "4", "D"),

    # 41 - Clients et comptes rattachés
    PCG2025Account("41", "Clients et comptes rattachés", "4", "D", True),
    PCG2025Account("411", "Clients", "4", "D", True),
    PCG2025Account("4111", "Clients - Ventes de biens ou de prestations de services", "4", "D"),
    PCG2025Account("4117", "Clients - Retenues de garantie", "4", "D"),
    PCG2025Account("413", "Clients - Effets à recevoir", "4", "D"),
    PCG2025Account("416", "Clients douteux ou litigieux", "4", "D"),
    PCG2025Account("418", "Clients - Produits non encore facturés", "4", "D"),
    PCG2025Account("419", "Clients créditeurs", "4", "C", True),
    PCG2025Account("4191", "Clients - Avances et acomptes reçus", "4", "C"),
    PCG2025Account("4196", "Clients - Dettes pour emballages et matériel consignés", "4", "C"),
    PCG2025Account("4197", "Clients - Autres avoirs", "4", "C"),
    PCG2025Account("4198", "RRR à accorder et autres avoirs à établir", "4", "C"),

    # 42 - Personnel et comptes rattachés
    PCG2025Account("42", "Personnel et comptes rattachés", "4", "C", True),
    PCG2025Account("421", "Personnel - Rémunérations dues", "4", "C"),
    PCG2025Account("422", "Comités d'entreprise, d'établissement...", "4", "C"),
    PCG2025Account("424", "Participation des salariés aux résultats", "4", "C"),
    PCG2025Account("425", "Personnel - Avances et acomptes", "4", "D"),
    PCG2025Account("426", "Personnel - Dépôts", "4", "C"),
    PCG2025Account("427", "Personnel - Oppositions", "4", "C"),
    PCG2025Account("428", "Personnel - Charges à payer et produits à recevoir", "4", "C", True),
    PCG2025Account("4282", "Dettes provisionnées pour congés à payer", "4", "C"),
    PCG2025Account("4284", "Dettes provisionnées pour participation des salariés", "4", "C"),
    PCG2025Account("4286", "Autres charges à payer", "4", "C"),
    PCG2025Account("4287", "Produits à recevoir", "4", "D"),

    # 43 - Sécurité sociale et autres organismes sociaux
    PCG2025Account("43", "Sécurité sociale et autres organismes sociaux", "4", "C", True),
    PCG2025Account("431", "Sécurité sociale", "4", "C"),
    PCG2025Account("437", "Autres organismes sociaux", "4", "C"),
    PCG2025Account("438", "Organismes sociaux - Charges à payer et produits à recevoir", "4", "C", True),
    PCG2025Account("4382", "Charges sociales sur congés à payer", "4", "C"),
    PCG2025Account("4386", "Autres charges à payer", "4", "C"),
    PCG2025Account("4387", "Produits à recevoir", "4", "D"),

    # 44 - État et autres collectivités publiques
    PCG2025Account("44", "État et autres collectivités publiques", "4", "C", True),
    PCG2025Account("441", "État - Subventions à recevoir", "4", "D"),
    PCG2025Account("442", "État - Impôts et taxes recouvrables sur des tiers", "4", "D"),
    PCG2025Account("443", "Opérations particulières avec l'État", "4", "C"),
    PCG2025Account("444", "État - Impôts sur les bénéfices", "4", "C"),
    PCG2025Account("445", "État - Taxes sur le chiffre d'affaires", "4", "C", True),
    PCG2025Account("4452", "TVA due intracommunautaire", "4", "C"),
    PCG2025Account("4455", "Taxes sur le chiffre d'affaires à décaisser", "4", "C", True),
    PCG2025Account("44551", "TVA à décaisser", "4", "C"),
    PCG2025Account("44558", "Taxes assimilées à la TVA", "4", "C"),
    PCG2025Account("4456", "Taxes sur le chiffre d'affaires déductibles", "4", "D", True),
    PCG2025Account("44562", "TVA sur immobilisations", "4", "D"),
    PCG2025Account("44563", "TVA transférée par d'autres entreprises", "4", "D"),
    PCG2025Account("44566", "TVA sur autres biens et services", "4", "D"),
    PCG2025Account("44567", "Crédit de TVA à reporter", "4", "D"),
    PCG2025Account("4457", "Taxes sur le chiffre d'affaires collectées", "4", "C", True),
    PCG2025Account("44571", "TVA collectée", "4", "C"),
    PCG2025Account("44578", "Taxes assimilées à la TVA", "4", "C"),
    PCG2025Account("4458", "Taxes sur le chiffre d'affaires à régulariser ou en attente", "4", "C"),
    PCG2025Account("446", "Obligations cautionnées", "4", "C"),
    PCG2025Account("447", "Autres impôts, taxes et versements assimilés", "4", "C"),
    PCG2025Account("448", "État - Charges à payer et produits à recevoir", "4", "C", True),
    PCG2025Account("4482", "Charges fiscales sur congés à payer", "4", "C"),
    PCG2025Account("4486", "Autres charges à payer", "4", "C"),
    PCG2025Account("4487", "Produits à recevoir", "4", "D"),

    # 45 - Groupe et associés
    PCG2025Account("45", "Groupe et associés", "4", "D", True),
    PCG2025Account("451", "Groupe", "4", "D"),
    PCG2025Account("455", "Associés - Comptes courants", "4", "D", True),
    PCG2025Account("4551", "Principal", "4", "D"),
    PCG2025Account("4558", "Intérêts courus", "4", "D"),
    PCG2025Account("456", "Associés - Opérations sur le capital", "4", "D", True),
    PCG2025Account("4561", "Associés - Comptes d'apport en société", "4", "D"),
    PCG2025Account("4562", "Apporteurs - Capital appelé, non versé", "4", "D"),
    PCG2025Account("4563", "Associés - Versements reçus sur augmentation de capital", "4", "C"),
    PCG2025Account("4564", "Associés - Versements anticipés", "4", "C"),
    PCG2025Account("4566", "Actionnaires défaillants", "4", "D"),
    PCG2025Account("4567", "Associés - Capital à rembourser", "4", "C"),
    PCG2025Account("457", "Associés - Dividendes à payer", "4", "C"),
    PCG2025Account("458", "Associés - Opérations faites en commun", "4", "D"),

    # 46 - Débiteurs divers et créditeurs divers
    PCG2025Account("46", "Débiteurs divers et créditeurs divers", "4", "D", True),
    PCG2025Account("462", "Créances sur cessions d'immobilisations", "4", "D"),
    PCG2025Account("464", "Dettes sur acquisitions de VMP", "4", "C"),
    PCG2025Account("465", "Créances sur cessions de VMP", "4", "D"),
    PCG2025Account("467", "Autres comptes débiteurs ou créditeurs", "4", "D"),
    PCG2025Account("468", "Produits à recevoir et charges à payer", "4", "D"),

    # 47 - Comptes transitoires ou d'attente
    PCG2025Account("47", "Comptes transitoires ou d'attente", "4", "D", True),
    PCG2025Account("471", "Comptes d'attente", "4", "D"),
    PCG2025Account("472", "Compte d'attente", "4", "C"),
    PCG2025Account("476", "Différences de conversion - Actif", "4", "D"),
    PCG2025Account("477", "Différences de conversion - Passif", "4", "C"),
    PCG2025Account("478", "Autres comptes transitoires", "4", "D"),

    # 48 - Comptes de régularisation
    PCG2025Account("48", "Comptes de régularisation", "4", "D", True),
    PCG2025Account("481", "Charges à répartir sur plusieurs exercices", "4", "D"),
    PCG2025Account("486", "Charges constatées d'avance", "4", "D"),
    PCG2025Account("487", "Produits constatés d'avance", "4", "C"),
    PCG2025Account("488", "Comptes de répartition périodique des charges et des produits", "4", "D"),

    # 49 - Dépréciations des comptes de tiers
    PCG2025Account("49", "Dépréciations des comptes de tiers", "4", "C", True),
    PCG2025Account("491", "Dépréciations des comptes clients", "4", "C"),
    PCG2025Account("495", "Dépréciations des comptes du groupe et des associés", "4", "C"),
    PCG2025Account("496", "Dépréciations des comptes de débiteurs divers", "4", "C"),
]


# ============================================================================
# CLASSE 5 - COMPTES FINANCIERS
# ============================================================================

PCG2025_CLASSE_5 = [
    # 50 - Valeurs mobilières de placement
    PCG2025Account("50", "Valeurs mobilières de placement", "5", "D", True),
    PCG2025Account("501", "Parts dans des entreprises liées", "5", "D"),
    PCG2025Account("502", "Actions propres", "5", "D"),
    PCG2025Account("503", "Actions", "5", "D"),
    PCG2025Account("504", "Autres titres conférant un droit de propriété", "5", "D"),
    PCG2025Account("505", "Obligations et bons émis par la société et rachetés par elle", "5", "D"),
    PCG2025Account("506", "Obligations", "5", "D"),
    PCG2025Account("507", "Bons du Trésor et bons de caisse à court terme", "5", "D"),
    PCG2025Account("508", "Autres valeurs mobilières de placement", "5", "D", True),
    PCG2025Account("5081", "Autres valeurs mobilières", "5", "D"),
    PCG2025Account("5082", "Bons de souscription", "5", "D"),
    PCG2025Account("5088", "Intérêts courus sur obligations, bons et valeurs assimilées", "5", "D"),
    PCG2025Account("509", "Versements restant à effectuer sur VMP non libérées", "5", "C"),

    # 51 - Banques, établissements financiers et assimilés
    PCG2025Account("51", "Banques, établissements financiers et assimilés", "5", "D", True),
    PCG2025Account("511", "Valeurs à l'encaissement", "5", "D", True),
    PCG2025Account("5111", "Coupons échus à l'encaissement", "5", "D"),
    PCG2025Account("5112", "Chèques à encaisser", "5", "D"),
    PCG2025Account("5113", "Effets à l'encaissement", "5", "D"),
    PCG2025Account("5114", "Effets à l'escompte", "5", "D"),
    PCG2025Account("512", "Banques", "5", "D", True),
    PCG2025Account("5121", "Banque A", "5", "D"),
    PCG2025Account("5122", "Banque B", "5", "D"),
    PCG2025Account("514", "Chèques postaux", "5", "D"),
    PCG2025Account("515", "Caisses du Trésor et des établissements publics", "5", "D"),
    PCG2025Account("516", "Sociétés de bourse", "5", "D"),
    PCG2025Account("517", "Autres organismes financiers", "5", "D"),
    PCG2025Account("518", "Intérêts courus", "5", "D", True),
    PCG2025Account("5181", "Intérêts courus à payer", "5", "C"),
    PCG2025Account("5188", "Intérêts courus à recevoir", "5", "D"),
    PCG2025Account("519", "Concours bancaires courants", "5", "C", True),
    PCG2025Account("5191", "Crédit de mobilisation de créances commerciales (CMCC)", "5", "C"),
    PCG2025Account("5193", "Mobilisation de créances nées à l'étranger", "5", "C"),
    PCG2025Account("5198", "Intérêts courus sur concours bancaires courants", "5", "C"),

    # 53 - Caisse
    PCG2025Account("53", "Caisse", "5", "D", True),
    PCG2025Account("531", "Caisse siège social", "5", "D"),
    PCG2025Account("532", "Caisse succursale (ou établissement) A", "5", "D"),

    # 54 - Régies d'avances et accréditifs
    PCG2025Account("54", "Régies d'avances et accréditifs", "5", "D", True),
    PCG2025Account("541", "Accréditifs", "5", "D"),
    PCG2025Account("542", "Chèques de voyage", "5", "D"),
    PCG2025Account("543", "Régies d'avances", "5", "D"),

    # 58 - Virements internes
    PCG2025Account("58", "Virements internes", "5", "D", True),
    PCG2025Account("580", "Virements internes", "5", "D"),

    # 59 - Dépréciations des VMP
    PCG2025Account("59", "Dépréciations des valeurs mobilières de placement", "5", "C", True),
    PCG2025Account("590", "Dépréciations des VMP", "5", "C"),
]


# ============================================================================
# CLASSE 6 - COMPTES DE CHARGES
# ============================================================================

PCG2025_CLASSE_6 = [
    # 60 - Achats
    PCG2025Account("60", "Achats (sauf 603)", "6", "D", True),
    PCG2025Account("601", "Achats stockés - Matières premières (et fournitures)", "6", "D"),
    PCG2025Account("602", "Achats stockés - Autres approvisionnements", "6", "D", True),
    PCG2025Account("6021", "Matières consommables", "6", "D"),
    PCG2025Account("6022", "Fournitures consommables", "6", "D"),
    PCG2025Account("6026", "Emballages", "6", "D"),
    PCG2025Account("603", "Variations des stocks", "6", "D", True),
    PCG2025Account("6031", "Variation des stocks de matières premières", "6", "D"),
    PCG2025Account("6032", "Variation des stocks des autres approvisionnements", "6", "D"),
    PCG2025Account("604", "Achats d'études et prestations de services", "6", "D"),
    PCG2025Account("605", "Achats de matériel, équipements et travaux", "6", "D"),
    PCG2025Account("606", "Achats non stockés de matières et fournitures", "6", "D", True),
    PCG2025Account("6061", "Fournitures non stockables (eau, énergie...)", "6", "D"),
    PCG2025Account("6063", "Fournitures d'entretien et de petit équipement", "6", "D"),
    PCG2025Account("6064", "Fournitures administratives", "6", "D"),
    PCG2025Account("6068", "Autres matières et fournitures", "6", "D"),
    PCG2025Account("607", "Achats de marchandises", "6", "D"),
    PCG2025Account("608", "Frais accessoires sur achats", "6", "D"),
    PCG2025Account("609", "Rabais, remises et ristournes obtenus sur achats", "6", "C"),

    # 61 - Services extérieurs
    PCG2025Account("61", "Services extérieurs", "6", "D", True),
    PCG2025Account("611", "Sous-traitance générale", "6", "D"),
    PCG2025Account("612", "Redevances de crédit-bail", "6", "D", True),
    PCG2025Account("6122", "Crédit-bail mobilier", "6", "D"),
    PCG2025Account("6125", "Crédit-bail immobilier", "6", "D"),
    PCG2025Account("613", "Locations", "6", "D", True),
    PCG2025Account("6132", "Locations immobilières", "6", "D"),
    PCG2025Account("6135", "Locations mobilières", "6", "D"),
    PCG2025Account("614", "Charges locatives et de copropriété", "6", "D"),
    PCG2025Account("615", "Entretien et réparations", "6", "D", True),
    PCG2025Account("6152", "Sur biens immobiliers", "6", "D"),
    PCG2025Account("6155", "Sur biens mobiliers", "6", "D"),
    PCG2025Account("616", "Primes d'assurances", "6", "D", True),
    PCG2025Account("6161", "Multirisques", "6", "D"),
    PCG2025Account("6162", "Assurance obligatoire dommage construction", "6", "D"),
    PCG2025Account("6163", "Assurance transport", "6", "D"),
    PCG2025Account("6164", "Risques d'exploitation", "6", "D"),
    PCG2025Account("6165", "Insolvabilité clients", "6", "D"),
    PCG2025Account("617", "Études et recherches", "6", "D"),
    PCG2025Account("618", "Divers", "6", "D", True),
    PCG2025Account("6181", "Documentation générale", "6", "D"),
    PCG2025Account("6183", "Documentation technique", "6", "D"),
    PCG2025Account("6185", "Frais de colloques, séminaires, conférences", "6", "D"),
    PCG2025Account("619", "Rabais, remises et ristournes obtenus sur services extérieurs", "6", "C"),

    # 62 - Autres services extérieurs
    PCG2025Account("62", "Autres services extérieurs", "6", "D", True),
    PCG2025Account("621", "Personnel extérieur à l'entreprise", "6", "D", True),
    PCG2025Account("6211", "Personnel intérimaire", "6", "D"),
    PCG2025Account("6214", "Personnel détaché ou prêté à l'entreprise", "6", "D"),
    PCG2025Account("622", "Rémunérations d'intermédiaires et honoraires", "6", "D", True),
    PCG2025Account("6221", "Commissions et courtages sur achats", "6", "D"),
    PCG2025Account("6222", "Commissions et courtages sur ventes", "6", "D"),
    PCG2025Account("6224", "Rémunérations des transitaires", "6", "D"),
    PCG2025Account("6225", "Rémunérations d'affacturage", "6", "D"),
    PCG2025Account("6226", "Honoraires", "6", "D"),
    PCG2025Account("6227", "Frais d'actes et de contentieux", "6", "D"),
    PCG2025Account("6228", "Divers", "6", "D"),
    PCG2025Account("623", "Publicité, publications, relations publiques", "6", "D", True),
    PCG2025Account("6231", "Annonces et insertions", "6", "D"),
    PCG2025Account("6232", "Échantillons", "6", "D"),
    PCG2025Account("6233", "Foires et expositions", "6", "D"),
    PCG2025Account("6234", "Cadeaux à la clientèle", "6", "D"),
    PCG2025Account("6235", "Primes", "6", "D"),
    PCG2025Account("6236", "Catalogues et imprimés", "6", "D"),
    PCG2025Account("6237", "Publications", "6", "D"),
    PCG2025Account("6238", "Divers (pourboires, dons courants...)", "6", "D"),
    PCG2025Account("624", "Transports de biens et transports collectifs du personnel", "6", "D", True),
    PCG2025Account("6241", "Transports sur achats", "6", "D"),
    PCG2025Account("6242", "Transports sur ventes", "6", "D"),
    PCG2025Account("6243", "Transports entre établissements ou chantiers", "6", "D"),
    PCG2025Account("6244", "Transports administratifs", "6", "D"),
    PCG2025Account("6247", "Transports collectifs du personnel", "6", "D"),
    PCG2025Account("6248", "Divers", "6", "D"),
    PCG2025Account("625", "Déplacements, missions et réceptions", "6", "D", True),
    PCG2025Account("6251", "Voyages et déplacements", "6", "D"),
    PCG2025Account("6255", "Frais de déménagement", "6", "D"),
    PCG2025Account("6256", "Missions", "6", "D"),
    PCG2025Account("6257", "Réceptions", "6", "D"),
    PCG2025Account("626", "Frais postaux et de télécommunications", "6", "D"),
    PCG2025Account("627", "Services bancaires et assimilés", "6", "D", True),
    PCG2025Account("6271", "Frais sur titres (achat, vente, garde)", "6", "D"),
    PCG2025Account("6272", "Commissions et frais sur émission d'emprunts", "6", "D"),
    PCG2025Account("6275", "Frais sur effets", "6", "D"),
    PCG2025Account("6276", "Location de coffres", "6", "D"),
    PCG2025Account("6278", "Autres frais et commissions sur prestations de services", "6", "D"),
    PCG2025Account("628", "Divers", "6", "D", True),
    PCG2025Account("6281", "Cotisations professionnelles", "6", "D"),
    PCG2025Account("6283", "Frais de recrutement de personnel", "6", "D"),
    PCG2025Account("6284", "Frais de formation", "6", "D"),
    PCG2025Account("629", "Rabais, remises et ristournes obtenus sur autres services extérieurs", "6", "C"),

    # 63 - Impôts, taxes et versements assimilés
    PCG2025Account("63", "Impôts, taxes et versements assimilés", "6", "D", True),
    PCG2025Account("631", "Impôts, taxes et versements assimilés sur rémunérations", "6", "D", True),
    PCG2025Account("6311", "Taxe sur les salaires", "6", "D"),
    PCG2025Account("6312", "Taxe d'apprentissage", "6", "D"),
    PCG2025Account("6313", "Participation des employeurs à la formation professionnelle continue", "6", "D"),
    PCG2025Account("6314", "Cotisation pour défaut d'investissement obligatoire dans la construction", "6", "D"),
    PCG2025Account("6318", "Autres impôts, taxes et versements assimilés sur rémunérations", "6", "D"),
    PCG2025Account("633", "Impôts, taxes et versements assimilés sur rémunérations (autres organismes)", "6", "D", True),
    PCG2025Account("6331", "Versement de transport", "6", "D"),
    PCG2025Account("6332", "Contribution sociale généralisée (CSG)", "6", "D"),
    PCG2025Account("6333", "Participation des employeurs à la formation professionnelle continue", "6", "D"),
    PCG2025Account("6334", "Participation des employeurs à l'effort de construction", "6", "D"),
    PCG2025Account("6338", "Autres", "6", "D"),
    PCG2025Account("635", "Autres impôts, taxes et versements assimilés", "6", "D", True),
    PCG2025Account("6351", "Impôts directs", "6", "D"),
    PCG2025Account("6352", "Taxes sur le chiffre d'affaires non récupérables", "6", "D"),
    PCG2025Account("6353", "Impôts indirects", "6", "D"),
    PCG2025Account("6354", "Droits d'enregistrement et de timbre", "6", "D"),
    PCG2025Account("6358", "Autres droits", "6", "D"),

    # 64 - Charges de personnel
    PCG2025Account("64", "Charges de personnel", "6", "D", True),
    PCG2025Account("641", "Rémunérations du personnel", "6", "D"),
    PCG2025Account("644", "Rémunération du travail de l'exploitant", "6", "D"),
    PCG2025Account("645", "Charges de sécurité sociale et de prévoyance", "6", "D", True),
    PCG2025Account("6451", "Cotisations à l'URSSAF", "6", "D"),
    PCG2025Account("6452", "Cotisations aux mutuelles", "6", "D"),
    PCG2025Account("6453", "Cotisations aux caisses de retraites", "6", "D"),
    PCG2025Account("6454", "Cotisations aux ASSEDIC", "6", "D"),
    PCG2025Account("6458", "Cotisations aux autres organismes sociaux", "6", "D"),
    PCG2025Account("646", "Cotisations sociales personnelles de l'exploitant", "6", "D"),
    PCG2025Account("647", "Autres charges sociales", "6", "D"),
    PCG2025Account("648", "Autres charges de personnel", "6", "D"),

    # 65 - Autres charges de gestion courante
    PCG2025Account("65", "Autres charges de gestion courante", "6", "D", True),
    PCG2025Account("651", "Redevances pour concessions, brevets, licences, marques...", "6", "D"),
    PCG2025Account("653", "Jetons de présence", "6", "D"),
    PCG2025Account("654", "Pertes sur créances irrécouvrables", "6", "D", True),
    PCG2025Account("6541", "Créances de l'exercice", "6", "D"),
    PCG2025Account("6544", "Créances des exercices antérieurs", "6", "D"),
    PCG2025Account("655", "Quotes-parts de résultat sur opérations faites en commun", "6", "D", True),
    PCG2025Account("6551", "Quote-part de perte transférée (comptabilité du gérant)", "6", "D"),
    PCG2025Account("6555", "Quote-part de perte supportée (comptabilité du non-gérant)", "6", "D"),
    PCG2025Account("658", "Charges diverses de gestion courante", "6", "D"),

    # 66 - Charges financières
    PCG2025Account("66", "Charges financières", "6", "D", True),
    PCG2025Account("661", "Charges d'intérêts", "6", "D", True),
    PCG2025Account("6611", "Intérêts des emprunts et dettes", "6", "D"),
    PCG2025Account("6615", "Intérêts des comptes courants et dépôts créditeurs", "6", "D"),
    PCG2025Account("6616", "Intérêts bancaires et sur opérations de financement", "6", "D"),
    PCG2025Account("6617", "Intérêts des obligations cautionnées", "6", "D"),
    PCG2025Account("6618", "Intérêts des autres dettes", "6", "D"),
    PCG2025Account("664", "Pertes sur créances liées à des participations", "6", "D"),
    PCG2025Account("665", "Escomptes accordés", "6", "D"),
    PCG2025Account("666", "Pertes de change", "6", "D"),
    PCG2025Account("667", "Charges nettes sur cessions de VMP", "6", "D"),
    PCG2025Account("668", "Autres charges financières", "6", "D"),

    # 67 - Charges exceptionnelles
    PCG2025Account("67", "Charges exceptionnelles", "6", "D", True),
    PCG2025Account("671", "Charges exceptionnelles sur opérations de gestion", "6", "D", True),
    PCG2025Account("6711", "Pénalités sur marchés (et dédits payés)", "6", "D"),
    PCG2025Account("6712", "Pénalités, amendes fiscales et pénales", "6", "D"),
    PCG2025Account("6713", "Dons, libéralités", "6", "D"),
    PCG2025Account("6714", "Créances devenues irrécouvrables dans l'exercice", "6", "D"),
    PCG2025Account("6715", "Subventions accordées", "6", "D"),
    PCG2025Account("6717", "Rappels d'impôts (autres qu'impôts sur les bénéfices)", "6", "D"),
    PCG2025Account("6718", "Autres charges exceptionnelles sur opérations de gestion", "6", "D"),
    PCG2025Account("675", "Valeurs comptables des éléments d'actif cédés", "6", "D", True),
    PCG2025Account("6751", "Immobilisations incorporelles", "6", "D"),
    PCG2025Account("6752", "Immobilisations corporelles", "6", "D"),
    PCG2025Account("6756", "Immobilisations financières", "6", "D"),
    PCG2025Account("6758", "Autres éléments d'actif", "6", "D"),
    PCG2025Account("678", "Autres charges exceptionnelles", "6", "D"),

    # 68 - Dotations aux amortissements, dépréciations et provisions
    PCG2025Account("68", "Dotations aux amortissements, dépréciations et provisions", "6", "D", True),
    PCG2025Account("681", "Dotations aux amortissements, dépréciations et provisions - Charges d'exploitation", "6", "D", True),
    PCG2025Account("6811", "Dotations aux amortissements des immobilisations incorporelles et corporelles", "6", "D"),
    PCG2025Account("6812", "Dotations aux amortissements des charges d'exploitation à répartir", "6", "D"),
    PCG2025Account("6815", "Dotations aux provisions d'exploitation", "6", "D"),
    PCG2025Account("6816", "Dotations pour dépréciations des immobilisations incorporelles et corporelles", "6", "D"),
    PCG2025Account("6817", "Dotations pour dépréciations des actifs circulants", "6", "D"),
    PCG2025Account("686", "Dotations aux amortissements, dépréciations et provisions - Charges financières", "6", "D", True),
    PCG2025Account("6861", "Dotations aux amortissements des primes de remboursement des obligations", "6", "D"),
    PCG2025Account("6865", "Dotations aux provisions financières", "6", "D"),
    PCG2025Account("6866", "Dotations pour dépréciations des éléments financiers", "6", "D"),
    PCG2025Account("6868", "Autres dotations", "6", "D"),
    PCG2025Account("687", "Dotations aux amortissements, dépréciations et provisions - Charges exceptionnelles", "6", "D", True),
    PCG2025Account("6871", "Dotations aux amortissements exceptionnels des immobilisations", "6", "D"),
    PCG2025Account("6872", "Dotations aux provisions réglementées (immobilisations)", "6", "D"),
    PCG2025Account("6873", "Dotations aux provisions réglementées (stocks)", "6", "D"),
    PCG2025Account("6874", "Dotations aux autres provisions réglementées", "6", "D"),
    PCG2025Account("6875", "Dotations aux provisions exceptionnelles", "6", "D"),
    PCG2025Account("6876", "Dotations pour dépréciations exceptionnelles", "6", "D"),

    # 69 - Participation des salariés - Impôts sur les bénéfices
    PCG2025Account("69", "Participation des salariés - Impôts sur les bénéfices et assimilés", "6", "D", True),
    PCG2025Account("691", "Participation des salariés aux résultats", "6", "D"),
    PCG2025Account("695", "Impôts sur les bénéfices", "6", "D", True),
    PCG2025Account("6951", "Impôts dus en France", "6", "D"),
    PCG2025Account("6952", "Contribution additionnelle à l'impôt sur les bénéfices", "6", "D"),
    PCG2025Account("6954", "Impôts dus à l'étranger", "6", "D"),
    PCG2025Account("696", "Suppléments d'impôt sur les sociétés liés aux distributions", "6", "D"),
    PCG2025Account("698", "Intégration fiscale", "6", "D", True),
    PCG2025Account("6981", "Intégration fiscale - Charges", "6", "D"),
    PCG2025Account("6989", "Intégration fiscale - Produits", "6", "C"),
    PCG2025Account("699", "Produits - Report en arrière des déficits", "6", "C"),
]


# ============================================================================
# CLASSE 7 - COMPTES DE PRODUITS
# ============================================================================

PCG2025_CLASSE_7 = [
    # 70 - Ventes de produits fabriqués, prestations de services, marchandises
    PCG2025Account("70", "Ventes de produits fabriqués, prestations de services, marchandises", "7", "C", True),
    PCG2025Account("701", "Ventes de produits finis", "7", "C"),
    PCG2025Account("702", "Ventes de produits intermédiaires", "7", "C"),
    PCG2025Account("703", "Ventes de produits résiduels", "7", "C"),
    PCG2025Account("704", "Travaux", "7", "C"),
    PCG2025Account("705", "Études", "7", "C"),
    PCG2025Account("706", "Prestations de services", "7", "C"),
    PCG2025Account("707", "Ventes de marchandises", "7", "C"),
    PCG2025Account("708", "Produits des activités annexes", "7", "C", True),
    PCG2025Account("7081", "Produits des services exploités dans l'intérêt du personnel", "7", "C"),
    PCG2025Account("7082", "Commissions et courtages", "7", "C"),
    PCG2025Account("7083", "Locations diverses", "7", "C"),
    PCG2025Account("7084", "Mise à disposition de personnel facturée", "7", "C"),
    PCG2025Account("7085", "Ports et frais accessoires facturés", "7", "C"),
    PCG2025Account("7086", "Bonis sur reprises d'emballages consignés", "7", "C"),
    PCG2025Account("7087", "Bonifications obtenues des clients et primes sur ventes", "7", "C"),
    PCG2025Account("7088", "Autres produits d'activités annexes", "7", "C"),
    PCG2025Account("709", "Rabais, remises et ristournes accordés par l'entreprise", "7", "D"),

    # 71 - Production stockée (ou déstockage)
    PCG2025Account("71", "Production stockée (ou déstockage)", "7", "C", True),
    PCG2025Account("713", "Variation des stocks (en-cours de production, produits)", "7", "C", True),
    PCG2025Account("7133", "Variation des en-cours de production de biens", "7", "C"),
    PCG2025Account("7134", "Variation des en-cours de production de services", "7", "C"),
    PCG2025Account("7135", "Variation des stocks de produits", "7", "C"),

    # 72 - Production immobilisée
    PCG2025Account("72", "Production immobilisée", "7", "C", True),
    PCG2025Account("721", "Immobilisations incorporelles", "7", "C"),
    PCG2025Account("722", "Immobilisations corporelles", "7", "C"),

    # 74 - Subventions d'exploitation
    PCG2025Account("74", "Subventions d'exploitation", "7", "C", True),
    PCG2025Account("741", "Subventions d'exploitation reçues", "7", "C"),

    # 75 - Autres produits de gestion courante
    PCG2025Account("75", "Autres produits de gestion courante", "7", "C", True),
    PCG2025Account("751", "Redevances pour concessions, brevets, licences, marques...", "7", "C"),
    PCG2025Account("752", "Revenus des immeubles non affectés aux activités professionnelles", "7", "C"),
    PCG2025Account("753", "Jetons de présence et rémunérations d'administrateurs", "7", "C"),
    PCG2025Account("754", "Ristournes perçues des coopératives", "7", "C"),
    PCG2025Account("755", "Quotes-parts de résultat sur opérations faites en commun", "7", "C", True),
    PCG2025Account("7551", "Quote-part de bénéfice transférée (comptabilité du gérant)", "7", "C"),
    PCG2025Account("7555", "Quote-part de bénéfice attribuée (comptabilité du non-gérant)", "7", "C"),
    PCG2025Account("758", "Produits divers de gestion courante", "7", "C"),

    # 76 - Produits financiers
    PCG2025Account("76", "Produits financiers", "7", "C", True),
    PCG2025Account("761", "Produits de participations", "7", "C", True),
    PCG2025Account("7611", "Revenus des titres de participation", "7", "C"),
    PCG2025Account("7616", "Revenus sur autres formes de participation", "7", "C"),
    PCG2025Account("7617", "Revenus de créances rattachées à des participations", "7", "C"),
    PCG2025Account("762", "Produits des autres immobilisations financières", "7", "C", True),
    PCG2025Account("7621", "Revenus des titres immobilisés", "7", "C"),
    PCG2025Account("7624", "Revenus des prêts", "7", "C"),
    PCG2025Account("7627", "Revenus des créances immobilisées", "7", "C"),
    PCG2025Account("763", "Revenus des autres créances", "7", "C"),
    PCG2025Account("764", "Revenus des valeurs mobilières de placement", "7", "C"),
    PCG2025Account("765", "Escomptes obtenus", "7", "C"),
    PCG2025Account("766", "Gains de change", "7", "C"),
    PCG2025Account("767", "Produits nets sur cessions de valeurs mobilières de placement", "7", "C"),
    PCG2025Account("768", "Autres produits financiers", "7", "C"),

    # 77 - Produits exceptionnels
    PCG2025Account("77", "Produits exceptionnels", "7", "C", True),
    PCG2025Account("771", "Produits exceptionnels sur opérations de gestion", "7", "C", True),
    PCG2025Account("7711", "Dédits et pénalités perçus sur achats et sur ventes", "7", "C"),
    PCG2025Account("7713", "Libéralités reçues", "7", "C"),
    PCG2025Account("7714", "Rentrées sur créances amorties", "7", "C"),
    PCG2025Account("7715", "Subventions d'équilibre", "7", "C"),
    PCG2025Account("7717", "Dégrèvements d'impôts (autres qu'impôts sur les bénéfices)", "7", "C"),
    PCG2025Account("7718", "Autres produits exceptionnels sur opérations de gestion", "7", "C"),
    PCG2025Account("775", "Produits des cessions d'éléments d'actif", "7", "C", True),
    PCG2025Account("7751", "Immobilisations incorporelles", "7", "C"),
    PCG2025Account("7752", "Immobilisations corporelles", "7", "C"),
    PCG2025Account("7756", "Immobilisations financières", "7", "C"),
    PCG2025Account("7758", "Autres éléments d'actif", "7", "C"),
    PCG2025Account("777", "Quote-part des subventions d'investissement virée au résultat de l'exercice", "7", "C"),
    PCG2025Account("778", "Autres produits exceptionnels", "7", "C"),

    # 78 - Reprises sur amortissements, dépréciations et provisions
    PCG2025Account("78", "Reprises sur amortissements, dépréciations et provisions", "7", "C", True),
    PCG2025Account("781", "Reprises sur amortissements, dépréciations et provisions (à inscrire dans produits d'exploitation)", "7", "C", True),
    PCG2025Account("7811", "Reprises sur amortissements des immobilisations incorporelles et corporelles", "7", "C"),
    PCG2025Account("7815", "Reprises sur provisions d'exploitation", "7", "C"),
    PCG2025Account("7816", "Reprises sur dépréciations des immobilisations incorporelles et corporelles", "7", "C"),
    PCG2025Account("7817", "Reprises sur dépréciations des actifs circulants", "7", "C"),
    PCG2025Account("786", "Reprises sur dépréciations et provisions (à inscrire dans produits financiers)", "7", "C", True),
    PCG2025Account("7865", "Reprises sur provisions financières", "7", "C"),
    PCG2025Account("7866", "Reprises sur dépréciations des éléments financiers", "7", "C"),
    PCG2025Account("787", "Reprises sur dépréciations et provisions (à inscrire dans produits exceptionnels)", "7", "C", True),
    PCG2025Account("7872", "Reprises sur provisions réglementées (immobilisations)", "7", "C"),
    PCG2025Account("7873", "Reprises sur provisions réglementées (stocks)", "7", "C"),
    PCG2025Account("7874", "Reprises sur autres provisions réglementées", "7", "C"),
    PCG2025Account("7875", "Reprises sur provisions exceptionnelles", "7", "C"),
    PCG2025Account("7876", "Reprises sur dépréciations exceptionnelles", "7", "C"),

    # 79 - Transferts de charges
    PCG2025Account("79", "Transferts de charges", "7", "C", True),
    PCG2025Account("791", "Transferts de charges d'exploitation", "7", "C"),
    PCG2025Account("796", "Transferts de charges financières", "7", "C"),
    PCG2025Account("797", "Transferts de charges exceptionnelles", "7", "C"),
]


# ============================================================================
# CLASSE 8 - COMPTES SPÉCIAUX
# ============================================================================

PCG2025_CLASSE_8 = [
    # 80 - Engagements
    PCG2025Account("80", "Engagements hors bilan", "8", "D", True),
    PCG2025Account("801", "Engagements donnés par l'entité", "8", "D", True),
    PCG2025Account("8011", "Avals, cautions, garanties", "8", "D"),
    PCG2025Account("8014", "Effets circulant sous l'endos de l'entité", "8", "D"),
    PCG2025Account("8016", "Redevances crédit-bail restant à courir", "8", "D"),
    PCG2025Account("8017", "Dettes garanties par des sûretés réelles", "8", "D"),
    PCG2025Account("8018", "Autres engagements donnés", "8", "D"),
    PCG2025Account("802", "Engagements reçus par l'entité", "8", "C", True),
    PCG2025Account("8021", "Avals, cautions, garanties reçus", "8", "C"),
    PCG2025Account("8024", "Créances escomptées ou cédées non échues", "8", "C"),
    PCG2025Account("8026", "Engagements reçus pour utilisation en crédit-bail", "8", "C"),
    PCG2025Account("8028", "Autres engagements reçus", "8", "C"),

    # 89 - Bilan
    PCG2025Account("89", "Bilan", "8", "D", True),
    PCG2025Account("890", "Bilan d'ouverture", "8", "D"),
    PCG2025Account("891", "Bilan de clôture", "8", "D"),
]


# ============================================================================
# COMPILATION COMPLÈTE PCG 2025
# ============================================================================

PCG2025_ALL_ACCOUNTS: list[PCG2025Account] = (
    PCG2025_CLASSE_1 +
    PCG2025_CLASSE_2 +
    PCG2025_CLASSE_3 +
    PCG2025_CLASSE_4 +
    PCG2025_CLASSE_5 +
    PCG2025_CLASSE_6 +
    PCG2025_CLASSE_7 +
    PCG2025_CLASSE_8
)


def get_pcg2025_account(number: str) -> PCG2025Account | None:
    """Récupérer un compte PCG 2025 par son numéro."""
    for account in PCG2025_ALL_ACCOUNTS:
        if account.number == number:
            return account
    return None


def get_pcg2025_class(pcg_class: str) -> list[PCG2025Account]:
    """Récupérer tous les comptes d'une classe PCG."""
    return [a for a in PCG2025_ALL_ACCOUNTS if a.pcg_class == pcg_class]


def get_pcg2025_summary_accounts() -> list[PCG2025Account]:
    """Récupérer les comptes de regroupement (synthétiques)."""
    return [a for a in PCG2025_ALL_ACCOUNTS if a.is_summary]


def validate_pcg_account_number(number: str) -> bool:
    """Valider un numéro de compte PCG."""
    if not number or len(number) < 2:
        return False
    if not number[0] in "12345678":
        return False
    if not number.isdigit():
        return False
    return True


def get_parent_account_number(number: str) -> str | None:
    """Récupérer le numéro du compte parent."""
    if len(number) <= 2:
        return None
    return number[:-1]
