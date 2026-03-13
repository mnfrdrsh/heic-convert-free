import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app.conversion import convert_images, get_available_output_path


def create_image(path: Path, mode: str = "RGBA", color=(255, 0, 0, 255)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new(mode, (16, 16), color).save(path)


class GetAvailableOutputPathTests(unittest.TestCase):
    def test_appends_suffix_when_target_exists(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            existing = tmp_path / "sample.png"
            existing.write_bytes(b"existing file")

            output_path = get_available_output_path(tmp_dir, "sample", "PNG")

            self.assertEqual(output_path, str(tmp_path / "sample (1).png"))


class ConvertImagesTests(unittest.TestCase):
    def test_converts_duplicate_basenames_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            first_source = tmp_path / "first" / "photo.png"
            second_source = tmp_path / "second" / "photo.png"
            output_dir = tmp_path / "out"

            create_image(first_source)
            create_image(second_source, color=(0, 255, 0, 255))

            success_count, error_count = convert_images(
                [str(first_source), str(second_source)],
                "JPEG",
                str(output_dir),
            )

            self.assertEqual((success_count, error_count), (2, 0))
            self.assertTrue((output_dir / "photo.jpeg").exists())
            self.assertTrue((output_dir / "photo (1).jpeg").exists())

    def test_same_format_in_place_creates_numbered_copy(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            source = tmp_path / "photo.png"
            create_image(source)
            messages = []

            success_count, error_count = convert_images(
                [str(source)],
                "PNG",
                str(tmp_path),
                messages.append,
            )

            self.assertEqual((success_count, error_count), (1, 0))
            self.assertTrue((tmp_path / "photo.png").exists())
            self.assertTrue((tmp_path / "photo (1).png").exists())
            self.assertIn("photo.png -> photo (1).png", messages[0])


if __name__ == "__main__":
    unittest.main()
