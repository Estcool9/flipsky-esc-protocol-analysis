import tempfile
import unittest
from pathlib import Path

from scripts.ftesc_profiles import ProfileError, build_profile_catalog, classify_family, parse_profile


class ProfileOrderTests(unittest.TestCase):
    def write_xml(self, directory, text):
        path = Path(directory) / "resource_01_test.xml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_classifies_control_setup_family(self):
        self.assertEqual(classify_family({"a": {"valName": "Input Signal Type"}}), "control_setup")

    def test_classifies_motor_setup_family(self):
        self.assertEqual(classify_family({"a": {"valName": "Motor Current(A)"}}), "motor_setup")

    def test_classifies_motor_signal_setup_family(self):
        self.assertEqual(classify_family({"a": {"valName": "FOC Current Kp"}}), "motor_signal_setup")

    def test_classifies_encoder_setup_family(self):
        self.assertEqual(classify_family({"a": {"valName": "Encoder Zero Position(rad)"}}), "encoder_setup")

    def test_value_sequence_controls_order_not_values_order(self):
        xml = """<ValueSetups>
          <Values>
            <alpha><valName>Alpha</valName><valType>2</valType><value_int>1</value_int><valueTET>1</valueTET></alpha>
            <beta><valName>Beta</valName><valType>2</valType><value_int>2</value_int><valueTET>1</valueTET></beta>
          </Values>
          <ValueSeque><seque>beta</seque><seque>alpha</seque></ValueSeque>
        </ValueSetups>"""
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_xml(directory, xml)
            profile = parse_profile(path)
        self.assertEqual([x["xml_id"] for x in profile["ordered_parameters"]], ["beta", "alpha"])
        self.assertEqual(profile["ordered_parameters"][0]["sequence_index"], 0)

    def test_values_not_in_sequence_are_recorded_as_omitted(self):
        xml = """<ValueSetups>
          <Values>
            <sent><valName>Sent</valName></sent>
            <display_only><valName>Display only</valName></display_only>
          </Values>
          <ValueSeque><seque>sent</seque></ValueSeque>
        </ValueSetups>"""
        with tempfile.TemporaryDirectory() as directory:
            profile = parse_profile(self.write_xml(directory, xml))
        self.assertEqual(profile["omitted_count"], 1)
        self.assertEqual(profile["omitted_parameters"][0]["xml_id"], "display_only")

    def test_unknown_sequence_id_is_rejected(self):
        xml = """<ValueSetups><Values><a><valName>A</valName></a></Values>
          <ValueSeque><seque>missing</seque></ValueSeque></ValueSetups>"""
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ProfileError):
                parse_profile(self.write_xml(directory, xml))

    def test_duplicate_sequence_id_is_rejected(self):
        xml = """<ValueSetups><Values><a><valName>A</valName></a></Values>
          <ValueSeque><seque>a</seque><seque>a</seque></ValueSeque></ValueSetups>"""
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ProfileError):
                parse_profile(self.write_xml(directory, xml))


if __name__ == "__main__":
    unittest.main()
