def test_streamlit_login_page_renders():
    from pathlib import Path
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(Path(__file__).resolve().parents[2]/"app.py").run(timeout=30)
    assert not app.exception
    assert any("SalesOps AI" in x.value for x in app.markdown)


def test_login_page_includes_all_demo_credentials():
    from pathlib import Path

    source=(Path(__file__).resolve().parents[2]/"ui/auth/login_page.py").read_text()
    assert "View demo accounts" in source
    for username in ("admin","manager","builder"):
        assert username in source
    assert "salesops-demo" in source
    assert "Go to CRM" in source
    assert "CRM_WEB_URL" in source


def test_login_accepts_workspace_email_alias_and_uses_argon2():
    from core.auth import authenticate
    from core.database import query

    assert authenticate("manager@salesops.local","salesops-demo")["role"]=="Sales Manager"
    stored=query("SELECT password_hash FROM users WHERE username='manager'")[0]["password_hash"]
    assert stored.startswith("$argon2id$")


def test_power_platform_blueprint_is_registered():
    from pathlib import Path

    root=Path(__file__).resolve().parents[2]
    assert "Power Platform Blueprint" in (root/"app.py").read_text()
    source=(root/"pages/Power_Platform_Blueprint.py").read_text()
    for capability in ("Power Apps","Power Automate","Dataverse","Copilot Studio","DLP policies","CoE"):
        assert capability in source
