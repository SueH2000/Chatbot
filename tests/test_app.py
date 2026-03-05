import ast
from pathlib import Path
import unittest


class SourceStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.src = Path('app.py').read_text(encoding='utf-8')
        cls.tree = ast.parse(cls.src)

    def test_character_cards_exist(self) -> None:
        self.assertIn('CHARACTER_CARDS', self.src)
        self.assertIn('"boyfriend"', self.src)
        self.assertIn('"girlfriend"', self.src)

    def test_chat_request_has_comfort_controls(self) -> None:
        self.assertIn('comfort_level', self.src)
        self.assertIn('response_length', self.src)
        self.assertIn('character_seed', self.src)

    def test_endpoints_are_declared(self) -> None:
        self.assertIn('@app.get("/")', self.src)
        self.assertIn('RedirectResponse(url="/chat-ui"', self.src)
        self.assertIn('@app.get("/favicon.ico")', self.src)
        self.assertIn('@app.get("/chat-ui"', self.src)
        self.assertIn('@app.get("/personas")', self.src)
        self.assertIn('@app.get("/characters")', self.src)
        self.assertIn('@app.post("/chat"', self.src)

    def test_system_prompt_builder_uses_controls(self) -> None:
        self.assertIn('build_response_rules(comfort_level, response_length)', self.src)
        self.assertIn('Tone tags:', self.src)

    def test_chat_ui_template_exists(self) -> None:
        self.assertIn('CHAT_UI_HTML_TEMPLATE', self.src)
        self.assertIn('__PERSONA_OPTIONS__', self.src)
        self.assertIn('render_chat_ui_html', self.src)
        self.assertIn('Choose mode, type message', self.src)


if __name__ == '__main__':
    unittest.main()
