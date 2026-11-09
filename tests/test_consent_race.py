import ast
import unittest
from pathlib import Path


class ConsentRaceTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        source = (
            Path(__file__).resolve().parents[1]
            / "app" / "main.py"
        ).read_text()
        tree = ast.parse(source)

        approval = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef)
            and n.name == "request_engine_approval"
        )

        poll = next(
            n for n in ast.walk(approval)
            if isinstance(n, ast.FunctionDef)
            and n.name == "poll"
        )

        assignment = next(
            n for n in ast.walk(poll)
            if isinstance(n, ast.Assign)
            and any(
                isinstance(t, ast.Name)
                and t.id == "engine_security_approved"
                for t in n.targets
            )
        )

        cls.condition = compile(
            ast.Expression(body=assignment.value),
            "<approval-condition>",
            "eval"
        )

    def check(self, result, started, current, xmrig, sadaqah):
        class Consent:
            def __init__(self, value):
                self.value = value

            def get(self):
                return self.value

        return eval(
            self.condition,
            {"__builtins__": {}},
            {
                "result": result,
                "scan_revision": started,
                "consent_revision": current,
                "xmrig_install_consent": Consent(xmrig),
                "sadaqah_consent": Consent(sadaqah),
            }
        )

    def test_old_scan_cannot_approve(self):
        self.assertFalse(
            self.check("scan_completed", 1, 2, True, True)
        )

    def test_withdrawn_consent_cannot_approve(self):
        self.assertFalse(
            self.check("scan_completed", 2, 2, True, False)
        )

    def test_valid_current_scan_condition(self):
        self.assertTrue(
            self.check("scan_completed", 2, 2, True, True)
        )


if __name__ == "__main__":
    unittest.main()
