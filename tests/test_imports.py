"""Smoke test for project imports."""


def test_import_myagent():
    import myagent

    assert myagent.__version__ == "0.1.0"


def test_import_engine():
    from myagent import engine

    assert engine is not None


def test_import_tools():
    from myagent import tools

    assert tools is not None


def test_import_agents():
    from myagent import agents

    assert agents is not None


def test_import_memory():
    from myagent import memory

    assert memory is not None


def test_import_config():
    from myagent import config

    assert config is not None
