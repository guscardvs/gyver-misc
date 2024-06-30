from gyver.misc import exc


def test_scream():
    assert exc.scream(ValueError, "foo").args[0] == "foo!"


def test_sentence():
    assert exc.sentence(ValueError, "foo").args[0] == "foo."
