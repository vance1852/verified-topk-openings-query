"""建立只含合成资料的本地 SQLite 库。"""

import argparse
import json
from pathlib import Path
import sqlite3
from contextlib import closing


def seed(source, target, role="main"):
    source, target = Path(source), Path(target)
    manifest = json.loads((source / "manifest.json").read_bytes())
    filename = manifest["databases"][role]["file"]
    statements = (source / filename).read_text(encoding="utf-8")
    memory = str(target) == ":memory:"
    if not memory:
        with target.open("xb"):
            pass
    with closing(sqlite3.connect(target)) as db:
        db.executescript(statements)
        check = db.execute("PRAGMA integrity_check").fetchone()[0]
        if check != "ok":
            raise ValueError(f"资料完整性检查失败：{check}")
        return {
            table: db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            for table in manifest["databases"][role]["rows"]
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="资料目录")
    parser.add_argument("target", type=Path, help="新建数据库文件")
    parser.add_argument("--role", default="main", help="资料列出的库角色")
    opts = parser.parse_args()
    print(json.dumps(seed(opts.source, opts.target, opts.role), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
