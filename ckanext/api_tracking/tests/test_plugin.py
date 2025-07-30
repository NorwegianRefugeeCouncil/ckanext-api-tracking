import pytest
from ckan import plugins


@pytest.mark.ckan_config("ckan.plugins", "api_tracking")
@pytest.mark.usefixtures("with_plugins")
def test_plugin():
    assert plugins.plugin_loaded("api_tracking")
