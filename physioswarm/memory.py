from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .embeddings import cosine_similarity, embed_text
from .types import ExecutionArtifact, TaskSignal, clamp


class MemoryGraph:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                task_id TEXT PRIMARY KEY,
                objective TEXT NOT NULL,
                summary TEXT NOT NULL,
                region TEXT NOT NULL,
                cell_id TEXT NOT NULL,
                route TEXT NOT NULL,
                status TEXT NOT NULL,
                tags TEXT NOT NULL,
                embedding TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS trust_scores (
                cell_id TEXT PRIMARY KEY,
                score REAL NOT NULL,
                streak INTEGER NOT NULL,
                last_status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS immune_memory (
                pattern_key TEXT PRIMARY KEY,
                region TEXT NOT NULL,
                pattern TEXT NOT NULL,
                weight REAL NOT NULL,
                embedding TEXT NOT NULL
            );
            """
        )
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(interactions)").fetchall()
        }
        if "region" not in columns:
            self.connection.execute("ALTER TABLE interactions ADD COLUMN region TEXT NOT NULL DEFAULT 'core'")
        self.connection.commit()

    def store_interaction(self, task: TaskSignal, artifact: ExecutionArtifact) -> None:
        summary = " ".join([task.objective, *artifact.notes]).strip()
        embedding = json.dumps(embed_text(summary))
        self.connection.execute(
            """
            INSERT OR REPLACE INTO interactions
            (task_id, objective, summary, region, cell_id, route, status, tags, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task.task_id,
                task.objective,
                summary,
                task.region,
                artifact.cell_id,
                artifact.route,
                artifact.status,
                json.dumps(list(task.tags)),
                embedding,
            ),
        )
        self.connection.commit()

    def recall(self, query: str, limit: int = 3) -> list[dict[str, object]]:
        rows = self.connection.execute(
            """
            SELECT task_id, objective, summary, region, cell_id, route, status, tags, embedding
            FROM interactions
            """
        ).fetchall()
        query_vector = embed_text(query)
        scored: list[dict[str, object]] = []
        for row in rows:
            score = cosine_similarity(query_vector, json.loads(row["embedding"]))
            scored.append(
                {
                    "task_id": row["task_id"],
                    "objective": row["objective"],
                    "summary": row["summary"],
                    "region": row["region"],
                    "cell_id": row["cell_id"],
                    "route": row["route"],
                    "status": row["status"],
                    "tags": tuple(json.loads(row["tags"])),
                    "score": score,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:limit]

    def record_outcome(self, cell_id: str, status: str, task: TaskSignal | None = None) -> None:
        row = self.connection.execute(
            "SELECT score, streak, last_status FROM trust_scores WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()
        if row is None:
            score = 0.6
            streak = 0
        else:
            score = float(row["score"])
            streak = int(row["streak"])
        if status == "executed":
            streak = max(0, streak) + 1
            score = clamp(score + 0.06 + min(streak, 4) * 0.01, 0.05, 0.98)
        else:
            streak = min(0, streak) - 1
            score = clamp(score - 0.14 - min(abs(streak), 4) * 0.02, 0.05, 0.98)
        self.connection.execute(
            """
            INSERT INTO trust_scores (cell_id, score, streak, last_status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cell_id) DO UPDATE SET
                score = excluded.score,
                streak = excluded.streak,
                last_status = excluded.last_status
            """,
            (cell_id, score, streak, status),
        )
        if task is not None and status != "executed":
            pattern_key = f"{task.region}:{task.objective}"
            existing = self.connection.execute(
                "SELECT weight FROM immune_memory WHERE pattern_key = ?",
                (pattern_key,),
            ).fetchone()
            weight = clamp((float(existing["weight"]) if existing is not None else 0.0) + 0.2, 0.0, 1.0)
            self.connection.execute(
                """
                INSERT INTO immune_memory (pattern_key, region, pattern, weight, embedding)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(pattern_key) DO UPDATE SET
                    weight = excluded.weight,
                    embedding = excluded.embedding
                """,
                (
                    pattern_key,
                    task.region,
                    task.objective,
                    weight,
                    json.dumps(embed_text(task.objective)),
                ),
            )
        self.connection.commit()

    def trust_score(self, cell_id: str) -> float:
        row = self.connection.execute(
            "SELECT score FROM trust_scores WHERE cell_id = ?",
            (cell_id,),
        ).fetchone()
        return float(row["score"]) if row is not None else 0.6

    def snapshot(self) -> dict[str, object]:
        interactions = self.connection.execute("SELECT COUNT(*) AS count FROM interactions").fetchone()
        trusts = self.connection.execute("SELECT COUNT(*) AS count FROM trust_scores").fetchone()
        hazards = self.connection.execute("SELECT COUNT(*) AS count FROM immune_memory").fetchone()
        return {
            "interactions": int(interactions["count"]),
            "trust_profiles": int(trusts["count"]),
            "immune_patterns": int(hazards["count"]),
        }

    def hazard_level(self, query: str, region: str) -> float:
        rows = self.connection.execute(
            "SELECT weight, embedding FROM immune_memory WHERE region = ?",
            (region,),
        ).fetchall()
        if not rows:
            return 0.0
        query_vector = embed_text(query)
        scores = [
            float(row["weight"]) * cosine_similarity(query_vector, json.loads(row["embedding"]))
            for row in rows
        ]
        return max(scores, default=0.0)

    def close(self) -> None:
        self.connection.close()
