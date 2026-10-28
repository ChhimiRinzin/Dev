import unittest
from devsentinel.analyzer import analyze, redact, export_report
from devsentinel.knowledge import search_docs

class AnalyzerTests(unittest.TestCase):
    def test_missing_module(self):
        items = analyze("ModuleNotFoundError: No module named 'pandas'")
        self.assertEqual(items[0].category, 'dependency')
    def test_pyarrow_build(self):
        items = analyze('ERROR: Failed building wheel for pyarrow')
        self.assertEqual(items[0].title, 'Python package build failure')
    def test_database(self):
        self.assertEqual(analyze('ECONNREFUSED 127.0.0.1:5432')[0].category, 'database')
    def test_empty(self):
        self.assertEqual(analyze('Everything worked'), [])
    def test_redaction(self):
        self.assertNotIn('supersecret', redact('api_key=supersecret'))
    def test_report_redaction(self):
        report = export_report(analyze('403 Forbidden'), 'token=abcdefghi')
        self.assertNotIn('abcdefghi', report)
    def test_knowledge(self):
        self.assertTrue(search_docs('python virtual environment packages'))

if __name__ == '__main__':
    unittest.main()
