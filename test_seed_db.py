"""核对关系型原始资料在本地能够实际载入和使用。"""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from seed_db import seed


class SeedDatabaseTest(unittest.TestCase):
    def test_cases_and_read_snapshots(self):
        cases = sorted((Path(__file__).parent / "fixtures").iterdir())
        self.assertGreaterEqual(len(cases), 2)
        with tempfile.TemporaryDirectory() as temp:
            for i, case in enumerate(cases):
                with self.subTest(case=case.name):
                    self.check_case(case, Path(temp), i)

    def check_case(self, case, temp, number):
        manifest = json.loads((case / "manifest.json").read_bytes())
        timeline = json.loads((case / "timeline.json").read_bytes())
        self.assertEqual(len(timeline), manifest["events"])
        self.assertEqual([row["pos"] for row in timeline], sorted(row["pos"] for row in timeline))
        self.assertTrue(all(row["kind"] for row in timeline))
        for role, database in manifest["databases"].items():
            target = temp / f"{number}-{role}.db"
            self.assertEqual(seed(case, target, role), database["rows"])
            with self.assertRaises(FileExistsError):
                seed(case, target, role)
            with closing(sqlite3.connect(target)) as writer, closing(sqlite3.connect(target)) as observer:
                self.assertEqual(writer.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
                names = writer.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name").fetchall()
                self.assertEqual([name for name, in names], sorted(database["rows"]))
                for name, count in database["rows"].items():
                    self.assertEqual(observer.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0], count)
                writer.execute("CREATE TEMP TABLE local_probe(id INTEGER)")
                self.assertEqual(observer.execute(
                    "SELECT count(*) FROM sqlite_temp_schema WHERE name='local_probe'").fetchone()[0], 0)
        for name in manifest["documents"]:
            self.assertTrue(json.loads((case / name).read_bytes()))


if __name__ == "__main__":
    unittest.main()
