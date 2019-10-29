import json

import pytest

from addok.batch import process_documents
from addok.core import search, Result
from addok.ds import get_document
from addok.helpers.text import Token
from addok_france.utils import (clean_query, extract_address, flag_housenumber,
                                fold_ordinal, glue_ordinal, make_labels,
                                remove_leading_zeros, glue_words,
                                glue_initials)


@pytest.mark.parametrize("input,expected", [
    ("2 allée Jules Guesde 31068 TOULOUSE CEDEX 7",
     "2 allée Jules Guesde 31 TOULOUSE"),
    ("7, avenue Léon-Blum 31507 Toulouse Cedex 5",
     "7, avenue Léon-Blum 31 Toulouse"),
    ("159, avenue Jacques-Douzans 31604 Muret Cedex",
     "159, avenue Jacques-Douzans 31 Muret"),
    ("2 allée Jules Guesde BP 7015 31068 TOULOUSE",
     "2 allée Jules Guesde 31068 TOULOUSE"),
    ("2 allée Jules Guesde B.P. 7015 31068 TOULOUSE",
     "2 allée Jules Guesde 31068 TOULOUSE"),
    ("2 allée Jules Guesde B.P. N 7015 31068 TOULOUSE",
     "2 allée Jules Guesde 31068 TOULOUSE"),
    ("BP 80111 159, avenue Jacques-Douzans 31604 Muret",
     "159, avenue Jacques-Douzans 31604 Muret"),
    ("12, place de l'Hôtel-de-Ville BP 46 02150 Sissonne",
     "12, place de l'Hôtel-de-Ville 02150 Sissonne"),
    ("12, place de l'Hôtel-de-Ville boite postale 46 02150 Sissonne",
     "12, place de l'Hôtel-de-Ville 02150 Sissonne"),
    ("12, place de l'Hôtel-de-Ville case postale 46 02150 Sissonne",
     "12, place de l'Hôtel-de-Ville 02150 Sissonne"),
    ("12, place de l'Hôtel-de-Ville bte postale 46 02150 Sissonne",
     "12, place de l'Hôtel-de-Ville 02150 Sissonne"),
    ("6, rue Winston-Churchill CS 40055 60321 Compiègne",
     "6, rue Winston-Churchill 60321 Compiègne"),
    ("BP 80111 159, avenue Jacques-Douzans 31604 Muret Cedex",
     "159, avenue Jacques-Douzans 31 Muret"),
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
    ("32bis Rue des Vosges93290",
     "32bis Rue des Vosges 93290"),
    ("20 avenue de Ségur TSA 30719 75334 Paris Cedex 07",
     "20 avenue de Ségur 75 Paris"),
    ("20 avenue de Ségur TSA No30719 75334 Paris Cedex 07",
     "20 avenue de Ségur 75 Paris"),
    ("20 avenue de Ségur TSA N 30719 75334 Paris Cedex 07",
     "20 avenue de Ségur 75 Paris"),
    ("20 avenue de Ségur TSA N°30719 75334 Paris Cedex 07",
     "20 avenue de Ségur 75 Paris"),
    ("20 rue saint germain CIDEX 304 89110 Poilly-sur-tholon",
     "20 rue saint germain 89110 Poilly-sur-tholon"),
    ("20 rue saint germain CIDEX N°304 89110 Poilly-sur-tholon",
     "20 rue saint germain 89110 Poilly-sur-tholon"),
    ("20 rue saint germain 89110 Poilly-sur-tholon 01.23.45.67.89",
     "20 rue saint germain 89110 Poilly-sur-tholon"),
    ("32bis Rue des Vosges93290 fax: 0123456789",
     "32bis Rue des Vosges 93290"),
    ("32bis Rue des Vosges 93290 tel 01 23 45 67 89",
     "32bis Rue des Vosges 93290"),
    ("32bis Rue des Vosges 93290 telecopieur. 01/23/45/67/89",
     "32bis Rue des Vosges 93290"),
    ("32bis Rue des Vosges 93290 télécopieur, 01-23-45-67-89",
     "32bis Rue des Vosges 93290"),
    ("10 BLD DES F F I 85300 CHALLANS",
     "10 BLD DES F F I 85300 CHALLANS"), # done by glue_initials
    ("6 rue de suisse 6000 Nice",
     "6 rue de suisse 06000 Nice"),
    ("6000 rue de suisse 6000 Nice",
     "6000 rue de suisse 06000 Nice"),
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
    ("PARC D ACTIVITE DE SAUMATY 26 AV ANDRE ROUSSIN 13016 MARSEILLE 16",
     "26 AV ANDRE ROUSSIN 13016 MARSEILLE 16"),
    # Abréviations
    ("resid goelands 28  bis imp des petrels 76460 Saint-valery-en-caux",
     "28  bis imp des petrels 76460 Saint-valery-en-caux"),
    ("bla bla bl 28 r des moulins",
     "28 r des moulins"),
    ("Non matching pattern",
     "Non matching pattern"),
])
def test_extract_address(input, expected):
    assert extract_address(input) == expected


@pytest.mark.parametrize("inputs,expected", [
    (['6', 'bis'], ['6bis']),
    (['6'], ['6']),
    (['6', 'avenue'], ['6', 'avenue']),
    (['60', 'bis', 'avenue'], ['60bis', 'avenue']),
    (['600', 'ter', 'avenue'], ['600ter', 'avenue']),
    (['6', 'quinquies', 'avenue'], ['6quinquies', 'avenue']),
    (['60', 'sexies', 'avenue'], ['60sexies', 'avenue']),
    (['600', 'quater', 'avenue'], ['600quater', 'avenue']),
    (['6', 's', 'avenue'], ['6s', 'avenue']),
    (['60b', 'avenue'], ['60b', 'avenue']),
    (['600', 'b', 'avenue'], ['600b', 'avenue']),
    (['241', 'r', 'de'], ['241', 'r', 'de']),
    (['120', 'r', 'renard'], ['120', 'r', 'renard']),
    (['241', 'r', 'rue'], ['241r', 'rue']),
    (['place', 'des', 'terreaux'], ['place', 'des', 'terreaux']),
    (['rue', 'du', 'bis'], ['rue', 'du', 'bis']),
])
def test_glue_ordinal(inputs, expected):
    tokens = [Token(input_) for input_ in inputs]
    assert list(glue_ordinal(tokens)) == expected


@pytest.mark.parametrize("inputs,expected", [
    (['6b'], True),
    (['6'], True),
    (['9303'], True),
    (['93031'], False),  # postcode
    (['6', 'avenue'], True),
    (['60b', 'avenue'], True),
    (['600t', 'avenue'], True),
    (['6c', 'avenue'], True),
    (['60s', 'avenue'], True),
    (['600q', 'avenue'], True),
    (['6s', 'avenue'], True),
    (['60b', 'avenue'], True),
    (['600b', 'avenue'], True),
    (['241', 'r', 'de'], True),
    (['241r', 'rue'], True),
    (['place', 'des', 'terreaux'], False),
    (['rue', 'du', 'bis'], False),
    (['9', 'grand', 'rue'], True),
])
def test_flag_housenumber(inputs, expected):
    tokens = [Token(input_) for input_ in inputs]
    tokens = list(flag_housenumber(tokens))
    assert tokens == inputs
    assert (tokens[0].kind == 'housenumber') == expected


@pytest.mark.parametrize("input,expected", [
    ('60bis', '60b'),
    ('60BIS', '60b'),
    ('60ter', '60t'),
    ('4terre', '4terre'),
    ('60quater', '60q'),
    ('60 bis', '60 bis'),
    ('bis', 'bis'),
])
def test_fold_ordinal(input, expected):
    assert fold_ordinal(Token(input)) == expected


@pytest.mark.parametrize("input,expected", [
    ('03', '3'),
    ('00009', '9'),
    ('02230', '02230'),  # Do not affect postcodes.
    ('0', '0'),
])
def test_remove_leading_zeros(input, expected):
    assert remove_leading_zeros(input) == expected


def test_index_housenumbers_use_processors(config):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
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
    process_documents(json.dumps(doc))
    stored = get_document('d|yyyy')
    assert stored['housenumbers']['1b']['raw'] == '1 bis'


@pytest.mark.parametrize("input,expected", [
    ('rue du 8 mai troyes', False),
    ('8 rue du 8 mai troyes', '8'),
    ('3 rue du 8 mai troyes', '3'),
    ('3 bis rue du 8 mai troyes', '3 bis'),
    ('3 bis r du 8 mai troyes', '3 bis'),
    ('3bis r du 8 mai troyes', '3 bis'),
])
def test_match_housenumber(input, expected):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'street',
        'name': 'rue du 8 Mai',
        'city': 'Troyes',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '3': {
                'lat': '48.325451',
                'lon': '2.25651'
            },
            '3 bis': {
                'lat': '48.325451',
                'lon': '2.25651'
            },
            '8': {
                'lat': '48.325451',
                'lon': '2.25651'
            },
        }
    }
    process_documents(json.dumps(doc))
    result = search(input)[0]
    assert (result.type == 'housenumber') == bool(expected)
    if expected:
        assert result.housenumber == expected


def test_match_housenumber_with_multiple_tokens(config):
    config.SYNONYMS = {'18': 'dix huit'}
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'street',
        'name': 'rue du 8 Mai',
        'city': 'Troyes',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '8': {
                'lat': '48.8',
                'lon': '2.25651'
            },
            '10': {
                'lat': '48.10',
                'lon': '2.25651'
            },
            '18': {
                'lat': '48.18',
                'lon': '2.25651'
            },
        }
    }
    process_documents(json.dumps(doc))
    result = search('8 rue du 8 mai')[0]
    assert result.housenumber == '8'
    assert result.lat == '48.8'
    result = search('10 rue du 8 mai')[0]
    assert result.housenumber == '10'
    assert result.lat == '48.10'
    result = search('18 rue du 8 mai')[0]
    assert result.housenumber == '18'
    assert result.lat == '48.18'


def test_make_labels(config):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'street',
        'name': 'rue des Lilas',
        'city': 'Paris',
        'postcode': '75010',
        'lat': '49.32545',
        'lon': '4.2565',
        'housenumbers': {
            '1 bis': {
                'lat': '48.325451',
                'lon': '2.25651'
            }
        }
    }
    process_documents(json.dumps(doc))
    result = Result(get_document('d|yyyy'))
    result.housenumber = '1 bis'  # Simulate match_housenumber
    make_labels(None, result)
    assert result.labels == [
        '1 bis rue des Lilas 75010 Paris',
        'rue des Lilas 75010 Paris',
        '1 bis rue des Lilas 75010',
        'rue des Lilas 75010',
        '1 bis rue des Lilas Paris',
        'rue des Lilas Paris',
        '1 bis rue des Lilas',
        'rue des Lilas'
    ]


def test_make_municipality_labels(config):
    doc = {
        'id': 'xxxx',
        '_id': 'yyyy',
        'type': 'municipality',
        'name': 'Lille',
        'city': 'Lille',
        'postcode': '59000',
        'lat': '49.32545',
        'lon': '4.2565',
    }
    process_documents(json.dumps(doc))
    result = Result(get_document('d|yyyy'))
    make_labels(None, result)
    assert result.labels == [
        'Lille',
        '59000 Lille',
        'Lille 59000',
    ]


@pytest.mark.parametrize("inputs,expected", [
    (['mont', 'griffon'], ['mont', 'montgriffon', 'griffon']),
    (['champ', 'vallon'], ['champ', 'champvallon', 'vallon']),
    (['val', 'suzon'], ['val', 'valsuzon', 'suzon']),
    (['l', 'a', 'peu', 'pres'], ['l', 'a', 'peu', 'pres']),
    (['l', 'un', 'des'], ['l', 'un', 'des']),
])
def test_glue_ordinal(inputs, expected):
    tokens = [Token(input_) for input_ in inputs]
    assert list(glue_words(tokens)) == expected


@pytest.mark.parametrize("inputs,expected", [
    (['allee', 'a', 'b', 'c', 'toto'],
     ['allee', 'abc', 'toto']),
    (['allee', 'a', 'b', 'c', 'toto', 'd', 'e', 'f'],
     ['allee', 'abc', 'toto', 'def']),
    (['allee', 'a', '2', 'c', 'toto'],
     ['allee', 'a', '2', 'c', 'toto']),
    (['allee', 'a', 'b', 'c'],
     ['allee', 'abc']),
    (['allee', 'a', 'b', 'c', 'd'],
     ['allee', 'abcd']),
    (['allee', 'a', 'b', 'c', 'd', 'e'],
     ['allee', 'abcde']),
])
def test_glue_initials(inputs, expected):
    tokens = [Token(input_) for input_ in inputs]
    assert list(glue_initials(tokens)) == expected
