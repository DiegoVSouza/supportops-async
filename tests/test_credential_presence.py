"""Credential discovery reports booleans without returning secret values."""
from scripts.credential_presence import presence


def test_root_env_and_process_are_reported_separately_without_values(tmp_path):
    (tmp_path / ".env").write_text("GROQ_API_KEY=example-secret\nexport GROQ_API_KEY_1='other-secret'\n", encoding="utf-8")
    result = presence(tmp_path, {"GROQ_API_KEY_2": "process-secret"})
    assert result["GROQ_API_KEY"] == {"process": False, "root_env": True}
    assert result["GROQ_API_KEY_1"]["root_env"] is True
    assert result["GROQ_API_KEY_2"] == {"process": True, "root_env": False}
    assert "secret" not in repr(result)


def test_missing_file_and_empty_values_do_not_claim_credentials(tmp_path):
    assert not any(v["root_env"] for v in presence(tmp_path, {}).values())
    (tmp_path / ".env").write_text("GROQ_API_KEY=''\n", encoding="utf-8")
    assert presence(tmp_path, {})["GROQ_API_KEY"]["root_env"] is False
