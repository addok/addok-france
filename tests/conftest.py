def pytest_configure():
    from addok import config
    config.PLUGINS.append('addok_france.plugin')
