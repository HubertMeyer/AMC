"""Static XML wiring test only; it does not compile or validate Spotify runtime behavior."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


LITE_HOST_PROJECT = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "AccessibleMediaController.LiteHost"
    / "AccessibleMediaController.LiteHost.csproj"
)
INTEGRATION_SOURCE = r"..\AccessibleMediaController.Windows\Services\SpotifyIntegrationService.cs"
COMPLETION_SOURCE = r"..\AccessibleMediaController.Windows\Services\SpotifyCollectionCompletion.cs"
COMPLETION_LINK = r"Engine\SpotifyCollectionCompletion.cs"


class SpotifyCollectionCompletionLiteHostWiringTests(unittest.TestCase):
    def test_wiring_only_litehost_links_completion_used_by_linked_integration_service(self):
        """The actual full LiteHost project links both the caller and its helper."""
        root = ET.parse(LITE_HOST_PROJECT).getroot()
        compile_items = root.findall(".//Compile")
        includes = {item.attrib.get("Include"): item for item in compile_items}

        self.assertIn(INTEGRATION_SOURCE, includes)
        self.assertIn(COMPLETION_SOURCE, includes)
        self.assertEqual(COMPLETION_LINK, includes[COMPLETION_SOURCE].attrib.get("Link"))


if __name__ == "__main__":
    unittest.main()
