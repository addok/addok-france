import pytest

from addok_france.utils import (clean_query, extract_address, fold_ordinal,
                                preprocess_housenumber, remove_leading_zeros)
from addok.helpers.text import Token
from addok.ds import get_document
from addok.batch import process_documents


@pytest.mark.parametrize("input,expected", [
    ("2 allée Jules Guesde 31068 TOULOUSE CEDEX 7",
     "2 allée Jules Guesde 31068 TOULOUSE"),
    ("7, avenue Léon-Blum 31507 Toulouse Cedex 5",
     "7, avenue Léon-Blum 31507 Toulouse"),
    ("159, avenue Jacques-Douzans 31604 Muret Cedex",
     "159, avenue Jacques-Douzans 31604 Muret"),
    ("2 allée Jules Guesde BP 7015 31068 TOULOUSE",
     "2 allée Jules Guesde 31068 TOULOUSE"),
    ("BP 80111 159, avenue Jacques-Douzans 31604 Muret",
     "159, avenue Jacques-Douzans 31604 Muret"),
    ("12, place de l'Hôtel-de-Ville BP 46 02150 Sissonne",
     "12, place de l'Hôtel-de-Ville 02150 Sissonne"),
    ("6, rue Winston-Churchill CS 40055 60321 Compiègne",
     "6, rue Winston-Churchill 60321 Compiègne"),
    ("BP 80111 159, avenue Jacques-Douzans 31604 Muret Cedex",
     "159, avenue Jacques-Douzans 31604 Muret"),
    ("BP 20169 Cite administrative - 8e étage Rue Gustave-Delory 59017 Lille",
     "Cite administrative - Rue Gustave-Delory 59017 Lille"),
    ("12e étage Rue Gustave-Delory 59017 Lille",
     "Rue Gustave-Delory 59017 Lille"),
    ("12eme étage Rue Gustave-Delory 59017 Lille",
     "Rue Gustave-Delory 59017 Lille"),
    ("12ème étage Rue Gustave-Delory 59017 Lille",
     "Rue Gustave-Delory 59017 Lille"),
    ("Rue Louis des Etages", "Rue Louis des Etages"),
    ("route express", "route express"),
    ("air s/ l'adour", "air sur l'adour"),
    ("air-s/-l'adour", "air sur l'adour"),
    ("Saint Didier s/s Ecouves", "Saint Didier sous Ecouves"),
    ("La Chapelle-aux-Brocs", "La Chapelle-aux-Brocs"),
    ("Lieu-Dit Les Chênes", "Les Chênes"),
    ("Lieu Dit Les Chênes", "Les Chênes"),
    ("LieuDit Les Chênes", "Les Chênes"),
    ("Lieux-Dits Les Chênes", "Les Chênes"),
    ("Lieu-Dit", "Lieu-Dit"),
    ("rue de la rente du lieu-dit la gachère",
     "rue de la rente du lieu-dit la gachère"),
])
def test_clean_query(input, expected):
    assert clean_query(input) == expected


@pytest.mark.parametrize("input,expected", [
    ('Immeuble Plein-Centre 60, avenue du Centre 78180 Montigny-le-Bretonneux',
     '60, avenue du Centre 78180 Montigny-le-Bretonneux'),
    ('75, rue Boucicaut 92260 Fontenay-aux-Roses',
     '75, rue Boucicaut 92260 Fontenay-aux-Roses'),
    ('rue Boucicaut 92260 Fontenay-aux-Roses',
     'rue Boucicaut 92260 Fontenay-aux-Roses'),
    ("Maison de l'emploi et de la formation 13, rue de la Tuilerie 70400 Héricourt",  # noqa
     "13, rue de la Tuilerie 70400 Héricourt"),
    # ("Parc d'activités Innopole 166, rue Pierre-et-Marie-Curie 31670 Labège",
    #  "166, rue Pierre-et-Marie-Curie 31670 Labège"),
    # ("32, allée Henri-Sellier Maison des solidarités 31400 Toulouse",
    #  "32, allée Henri-Sellier 31400 Toulouse"),
    # ("Centre d'Affaires la Boursidiere - BP 160 - Bâtiment Maine 4ème étage Le Plessis Robinson 92357 France",  # noqa
    #  "Le Plessis Robinson 92357 France"),
    # ("21 Rue Clef 34 Rue Daubenton",
    # "21 Rue Clef"),
    ("Tribunal d'instance de Guebwiller 1, place Saint-Léger 68504 Guebwiller",
     "1, place Saint-Léger 68504 Guebwiller"),
    ("Centre social 3 rue du Laurier 73000 CHAMBERY",
     "3 rue du Laurier 73000 CHAMBERY"),
    ("Maison de la Médiation 72 Chaussée de l'Hôtel de Ville 59650 VILLENEUVE D ASCQ",  # noqa
     "72 Chaussée de l'Hôtel de Ville 59650 VILLENEUVE D ASCQ"),
    ("2, Grande rue 62128 Écoust-Saint-Mein",
     "2, Grande rue 62128 Écoust-Saint-Mein"),
    ("Le Haut de la Rue du Bois 77122 Monthyon",
     "Le Haut de la Rue du Bois 77122 Monthyon"),
    ("Sous la Rue du Temple 62800 Liévin",
     "Sous la Rue du Temple 62800 Liévin"),
    # Two spaces after housenumber.
    ("resid goelands 28  impasse des petrels 76460 Saint-valery-en-caux",
     "28  impasse des petrels 76460 Saint-valery-en-caux"),
    # Two spaces before bis.
    ("resid goelands 28  bis impasse des petrels 76460 Saint-valery-en-caux",
     "28  bis impasse des petrels 76460 Saint-valery-en-caux"),
    # No spaces before bis.
    ("resid goelands 28bis impasse des petrels 76460 Saint-valery-en-caux",
     "28bis impasse des petrels 76460 Saint-valery-en-caux"),
    ("boulevard jean larrieu 44000 mont de marsan",
     "boulevard jean larrieu 44000 mont de marsan"),
    ("Non matching pattern",
     "Non matching pattern"),
])
def test_extract_address(input, expected):
    assert extract_address(input) == expected


@pytest.mark.parametrize("inputs,expected", [
    (['6', 'bis'], ['6b']),
    (['6'], ['6']),
    (['6', 'avenue'], ['6', 'avenue']),
    (['60', 'bis', 'avenue'], ['60b', 'avenue']),
    (['600', 'ter', 'avenue'], ['600t', 'avenue']),
    (['6', 'quinquies', 'avenue'], ['6c', 'avenue']),
    (['60', 'sexies', 'avenue'], ['60s', 'avenue']),
    (['600', 'quater', 'avenue'], ['600q', 'avenue']),
    (['6', 's', 'avenue'], ['6s', 'avenue']),
    (['60b', 'avenue'], ['60b', 'avenue']),
    (['600', 'b', 'avenue'], ['600b', 'avenue']),
    (['241', 'r', 'de'], ['241', 'r', 'de']),
    (['241', 'r', 'rue'], ['241r', 'rue']),
    (['place', 'des', 'terreaux'], ['place', 'des', 'terreaux']),
    (['rue', 'du', 'bis'], ['rue', 'du', 'bis']),
])
def test_preprocess_housenumber(inputs, expected):
    tokens = [Token(input_) for input_ in inputs]
    assert list(preprocess_housenumber(tokens)) == expected


@pytest.mark.parametrize("input,expected", [
    ('bis', 'b'),
    ('BIS', 'b'),
    ('ter', 't'),
    ('quater', 'q'),
    ('quinquies', 'c'),
])
def test_fold_ordinal(input, expected):
    assert fold_ordinal(Token(input)) == expected


@pytest.mark.parametrize("input,expected", [
    ('03', '3'),
    ('00009', '9'),
    ('0', '0'),
])
def test_remove_leading_zeros(input, expected):
    assert remove_leading_zeros(input) == expected


def test_index_housenumbers_use_processors(config):
    doc = {
        'id': 'xxxx',
        'type': 'street',
        'name': 'rue des Lilas',
        'city': 'Paris',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '1 bis': {
                'lat': '48.325451',
                'lon': '2.25651'
            }
        }
    }
    process_documents(doc)
    stored = get_document('d|xxxx')
    assert stored['housenumbers']['1b']['raw'] == '1 bis'
