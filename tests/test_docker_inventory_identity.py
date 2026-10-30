"""Identity comparisons ignore age, but detect replacement and scope changes."""
import pytest
from scripts.docker_inventory_identity import compare, stable_rows


def inventory(container):
    return {"containers": [container], "networks": ["net|name|project"],
            "volumes": ["volume|project"], "images": ["sha256:1|image:tag"]}


def test_status_age_does_not_invent_container_replacement():
    before = inventory("id1|gossett_backend|image|Restarting (1) 53 seconds ago||gosset")
    after = inventory("id1|gossett_backend|image|Restarting (1) 19 seconds ago||gosset")
    assert all(not diff["missing"] and not diff["added"] for diff in compare(before, after).values())


def test_new_id_and_changed_compose_owner_are_detected():
    before = inventory("id1|service|image|running|127.0.0.1:80|owner")
    after = inventory("id2|service|image|running|127.0.0.1:80|other")
    diff = compare(before, after)["containers"]
    assert len(diff["missing"]) == len(diff["added"]) == 1
    assert diff["missing"][0][0] == "id1"
    assert diff["added"][0][0] == "id2"


def test_legacy_command_output_format_and_failed_collection():
    output = {"exit_code": 0, "output": "id|service|img|running||owner\n"}
    assert stable_rows({"containers": output}, "containers") == {("id", "service", "img", "", "owner")}
    with pytest.raises(ValueError, match="failed"):
        stable_rows({"containers": {"exit_code": 1, "output": ""}}, "containers")


def test_missing_and_duplicate_entries_fail_closed():
    with pytest.raises(ValueError, match="invalid"):
        stable_rows({"containers": ["broken"]}, "containers")
    row = "id|service|image|running||owner"
    with pytest.raises(ValueError, match="duplicate"):
        stable_rows({"containers": [row, row]}, "containers")
