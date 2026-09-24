from wikipedia_interest.titles import split_title_fragment, wikipedia_article_url


def test_split_title_fragment():
    assert split_title_fragment("Netbook#Nettop") == ("Netbook", "Nettop")


def test_plain_article_has_no_fragment():
    assert split_title_fragment("Mini PC") == ("Mini PC", None)


def test_empty_fragment_and_percent_encoded_text_are_preserved():
    assert split_title_fragment("Article#") == ("Article", None)
    assert split_title_fragment("C%23 article#Überblick") == ("C%23 article", "Überblick")


def test_wikipedia_url_encodes_page_and_fragment_separately():
    assert wikipedia_article_url("de", "Netbook#Nettop") == "https://de.wikipedia.org/wiki/Netbook#Nettop"
    assert wikipedia_article_url("de", "Café#Überblick") == (
        "https://de.wikipedia.org/wiki/Caf%C3%A9#%C3%9Cberblick"
    )
