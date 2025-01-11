"""
Common fixtures used by many tests.
"""

import os
import yaml
import pytest

from lute.config.app_config import AppConfig
from lute.db import db
import lute.db.management
from lute.language.service import Service
from lute.app_factory import create_app

from lute.models.language import Language


def pytest_sessionstart(session):  # pylint: disable=unused-argument
    """
    Ensure test config defines a test environment.

    Special configuration for test runs required:

    DBNAME must start with test_

    DATAPATH must be specified: this ensures that the tests don't
    accidentally write into the user_data (which could mess with prod
    data/media etc)
    """
    thisdir = os.path.dirname(os.path.realpath(__file__))
    configfile = os.path.join(thisdir, "..", "lute", "config", "config.yml")

    config = None
    with open(configfile, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    failures = []
    if "DATAPATH" not in config:
        failures.append("DATAPATH not in config file")

    ac = AppConfig(configfile)

    if not ac.is_test_db:
        failures.append("DBNAME in config.yml must start with test_")
    if len(failures) > 0:
        msg = f"Bad config.yml: {', '.join(failures)}"
        pytest.exit(msg)


@pytest.fixture(name="testconfig")
def fixture_config():
    "Config using the app config."
    ac = AppConfig(AppConfig.default_config_filename())
    yield ac


@pytest.fixture(name="app")
def fixture_app():
    """
    A clean instance of the demo database.

    I'm not a _huge_ fan of this because if the app
    is open while tests are running, the app seems to hold
    on to references to the old deleted db ...
    that said, it's much faster to do this than to do a
    "wipe and reload database" on every test run.
    """
    config_file = AppConfig.default_config_filename()
    c = AppConfig(config_file)
    if os.path.exists(c.dbfilename):
        os.unlink(c.dbfilename)
    extra_config = {"WTF_CSRF_ENABLED": False, "TESTING": True}
    app = create_app(config_file, extra_config=extra_config)
    yield app


@pytest.fixture(name="app_context")
def fixture_app_context(app):
    """
    Yields the app context so that tests using the db will work.
    """
    with app.app_context() as c:
        yield c


@pytest.fixture(name="empty_db")
def fixture_empty_db(app_context):
    """
    Wipe the db.
    """
    lute.db.management.delete_all_data(db.session)


@pytest.fixture(name="client")
def fixture_demo_client(app):
    """
    Client using demo-data-loaded application.
    """
    return app.test_client()


def _get_test_language(lang_name):
    """
    Return language from the db if it already exists,
    or create it from the file.
    """
    lang = db.session.query(Language).filter(Language.name == lang_name).first()
    if lang is not None:
        return lang
    service = Service(db.session)
    lang = service.get_language_def(lang_name).language
    db.session.add(lang)
    db.session.commit()
    return lang


@pytest.fixture(name="spanish")
def fixture_spanish(app_context):
    return _get_test_language("Spanish")


@pytest.fixture(name="english")
def fixture_english(app_context):
    return _get_test_language("English")


@pytest.fixture(name="japanese")
def fixture_japanese(app_context):
    return _get_test_language("Japanese")


@pytest.fixture(name="turkish")
def fixture_turkish(app_context):
    return _get_test_language("Turkish")


@pytest.fixture(name="classical_chinese")
def fixture_cl_chinese(app_context):
    return _get_test_language("Classical Chinese")


@pytest.fixture(name="german")
def fixture_german(app_context):
    return _get_test_language("German")


@pytest.fixture(name="hindi")
def fixture_hindi(app_context):
    return _get_test_language("Hindi")


@pytest.fixture(name="generic")
def fixture_generic(app_context):
    return _get_test_language("Generic")
