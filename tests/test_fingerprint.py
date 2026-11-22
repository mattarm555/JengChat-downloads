"""python -m unittest discover -s tests"""
import hashlib
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import publish_delivery  # noqa: E402

PAGE = ('<link rel="stylesheet" href="style.css">\n'
        '<link rel="preload" href="fonts/f.woff2" as="font">\n'
        '<img src="img/a.webp" alt="">\n'
        '<a href="#download">Get it</a> <a href="https://github.com/x">x</a>\n'
        '<img src="img/missing.webp" alt="">\n'
        '<script src="app.js"></script>\n')


def site(folder):
    (folder / "img").mkdir()
    (folder / "index.html").write_text(PAGE, encoding="utf-8")
    (folder / "style.css").write_bytes(b"body{}")
    (folder / "app.js").write_bytes(b"'use strict';")
    (folder / "img/a.webp").write_bytes(b"image")


def tag(data):
    return hashlib.sha256(data).hexdigest()[:10]


class FingerprintTests(unittest.TestCase):
    def test_local_files_get_a_content_fingerprint(self):
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            site(folder)
            publish_delivery.fingerprint(folder)
            page = (folder / "index.html").read_text(encoding="utf-8")
            self.assertIn(f'href="style.css?v={tag(b"body{}")}"', page)
            self.assertIn(f'src="app.js?v={tag(b"\'use strict\';")}"', page)
            self.assertIn(f'src="img/a.webp?v={tag(b"image")}"', page)

    def test_anchors_external_links_and_unknown_files_are_left_alone(self):
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            site(folder)
            publish_delivery.fingerprint(folder)
            page = (folder / "index.html").read_text(encoding="utf-8")
            self.assertIn('href="#download"', page)
            self.assertIn('href="https://github.com/x"', page)
            self.assertIn('src="img/missing.webp"', page)

    def test_font_preloads_keep_the_url_the_stylesheet_uses(self):
        # style.css loads fonts/f.woff2 without ?v; a different preload URL would download it twice.
        with tempfile.TemporaryDirectory() as d:
            folder = pathlib.Path(d)
            site(folder)
            (folder / "fonts").mkdir()
            (folder / "fonts/f.woff2").write_bytes(b"font")
            publish_delivery.fingerprint(folder)
            self.assertIn('href="fonts/f.woff2"', (folder / "index.html").read_text(encoding="utf-8"))

    def test_a_changed_stylesheet_gets_a_new_link(self):
        links = []
        for css in (b"body{}", b"body{color:red}"):
            with tempfile.TemporaryDirectory() as d:
                folder = pathlib.Path(d)
                site(folder)
                (folder / "style.css").write_bytes(css)
                publish_delivery.fingerprint(folder)
                links.append((folder / "index.html").read_text(encoding="utf-8").splitlines()[0])
        self.assertNotEqual(links[0], links[1])


if __name__ == "__main__":
    unittest.main()
