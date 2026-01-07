import os
import unittest

from fastapi.testclient import TestClient

os.environ.setdefault("DEV_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("ENV", "test")

from feriekomp.db import init_db  # noqa: E402
from feriekomp.main import app  # noqa: E402


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "healthy")

    def test_beregn(self):
        payload = {
            "startdato_ferie": "2025-07-01",
            "sluttdato_ferie": "2025-07-14",
            "total_reisebelop": 20000,
            "antall_personer": 2,
            "antall_dager_sengeleie": 5,
            "ekstra_dag_for_legebesok": True,
            "dato_legebesok": "2025-07-05",
        }
        response = self.client.post("/beregn", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_kompensasjon", data)
        self.assertIn("gyldige_dager", data)


if __name__ == "__main__":
    unittest.main()
