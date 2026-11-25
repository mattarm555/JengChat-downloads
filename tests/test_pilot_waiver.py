"""python -m unittest discover -s tests"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import publish_delivery  # noqa: E402


def draft(tag):
    # A draft is rejected right after the waiver check, so the error shows whether the waiver passed.
    return {"tag_name": tag, "draft": True, "prerelease": True, "assets": []}


def error(tag, pilot_check):
    with unittest.TestCase().assertRaises(ValueError) as caught:
        publish_delivery.generate(draft(tag), None, None, None, "waived", pilot_check)
    return str(caught.exception)


class PilotWaiverTests(unittest.TestCase):
    def test_owner_approved_waiver_for_3_0_0_beta_1(self):
        self.assertIn("published friends-testing prerelease", error("v3.0.0-beta.1", "waived"))

    def test_beta_5_waiver_still_holds(self):
        self.assertIn("published friends-testing prerelease", error("v2.1.0-beta.5", "waived"))

    def test_owner_approved_waiver_for_3_0_0_beta_2(self):
        self.assertIn("published friends-testing prerelease", error("v3.0.0-beta.2", "waived"))

    def test_no_waiver_for_other_versions(self):
        self.assertIn("Pilot waiver", error("v3.0.0-beta.3", "waived"))


if __name__ == "__main__":
    unittest.main()
