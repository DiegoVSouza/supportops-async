"""Credential discovery reports booleans without returning secret values."""
from scripts.credential_presence import presence, preflight


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


def test_preflight_reports_root_only_provider_eligibility_without_secrets(tmp_path):
    (tmp_path / ".env").write_text("GROQ_API_KEY=root-secret\n", encoding="utf-8")
    report = preflight(tmp_path, {})
    assert report["status"] == "PRESENT"
    assert report["provider_root_env_slots"] == ["GROQ_API_KEY"]
    assert report["legacy_wrapper_process_precondition"] is False
    assert "root-secret" not in repr(report)


def test_process_only_does_not_claim_shared_provider_can_read_it(tmp_path):
    report = preflight(tmp_path, {"GROQ_API_KEY": "process-secret"})
    assert report["status"] == "INCOMPLETE"
    assert report["process_slots"] == ["GROQ_API_KEY"]
    assert report["provider_root_env_slots"] == []
    assert "process-secret" not in repr(report)
