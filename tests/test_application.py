import pytest
import os.path

from wmmc_bot.main import WMMCBot


@pytest.fixture
def app():
    return WMMCBot()


class TestApplication(object):
    def test_nothing(self):
        assert True

    def test_versioning(self, app):
        # App version must be present
        assert len(app.version) > 1
