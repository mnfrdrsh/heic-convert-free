import tempfile
import unittest
from pathlib import Path

from create_icon import create_app_icon


class CreateIconTests(unittest.TestCase):
    def test_writes_standard_icon_filenames(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            create_app_icon(output_dir=tmp_path)

            self.assertTrue((tmp_path / "app_icon.png").exists())
            self.assertTrue((tmp_path / "app_icon.ico").exists())


if __name__ == "__main__":
    unittest.main()
