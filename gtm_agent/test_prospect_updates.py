from . import data_service
from .gtm_agent import build_prospect_profile


def test_update_persists_technology_and_rebuilds_profile():
    prospect_id = "LEAD-12853"
    technology = "Okta"
    record = data_service.get_prospect_record(prospect_id)
    original_tech_stack = list(record["tech_stack"])

    try:
        data_service._PROFILES.pop(prospect_id, None)
        result = data_service.update_prospect_info(prospect_id, technology)

        assert result["updated"] is True
        assert technology in data_service.fetch_tech_stack(prospect_id)
        profile = build_prospect_profile.invoke({"prospect_id": prospect_id})
        assert technology in profile["prospect_profile"]["tech_stack"]
    finally:
        record["tech_stack"] = original_tech_stack
        data_service._PROFILES.pop(prospect_id, None)
