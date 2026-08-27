import json
import re
import importlib.util
import os
import pathlib
import sys
import types
import unittest
from unittest.mock import patch


PACKAGE_NAME = "gtm_agent_test_package"
PACKAGE_PATH = pathlib.Path(__file__).parent
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ["LANGSMITH_TRACING"] = "false"
package = types.ModuleType(PACKAGE_NAME)
package.__path__ = [str(PACKAGE_PATH)]
sys.modules[PACKAGE_NAME] = package
for module_name in ("gtm_records", "data_service", "gtm_agent"):
    module_spec = importlib.util.spec_from_file_location(
        f"{PACKAGE_NAME}.{module_name}", PACKAGE_PATH / f"{module_name}.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    globals()[module_name] = module


class ProspectPrivacyTest(unittest.TestCase):
    def setUp(self):
        data_service._PROFILES.clear()
        self.prospect_id = next(
            prospect_id for prospect_id, record in data_service.PROSPECTS.items()
            if "billing_qualification" in record
        )

    def assert_no_billing_pii(self, value):
        serialized = json.dumps(value)
        self.assertNotIn("billing_qualification", serialized)
        self.assertIsNone(re.search(r"\b\d{3}-\d{2}-\d{4}\b", serialized))
        self.assertIsNone(re.search(r"\b\d{16}\b", serialized))

    def test_prospect_tools_and_scoring_payload_exclude_billing_pii(self):
        prospect = gtm_agent.get_prospect.invoke({"prospect_id": self.prospect_id})
        profile = gtm_agent.build_prospect_profile.invoke({"prospect_id": self.prospect_id})
        self.assert_no_billing_pii(prospect)
        self.assert_no_billing_pii(profile)

        offering = next(iter(data_service.OFFERINGS.values()))
        scoring_result = type("ScoringResult", (), {"model_dump": lambda self: {"score": 1}})()
        with patch.object(gtm_agent, "_scoring_llm") as scoring_llm:
            scoring_llm.invoke.return_value = scoring_result
            gtm_agent.score_prospect.invoke({
                "prospect_profile": profile["prospect_profile"],
                "offering": offering,
            })
        self.assert_no_billing_pii(scoring_llm.invoke.call_args.args[0][1]["content"])


if __name__ == "__main__":
    unittest.main()
