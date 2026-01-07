import unittest

from feriekomp.services.calculation import beregn_feriekompensasjon


class CalculationTests(unittest.TestCase):
    def test_valid_case(self):
        payload = {
            "startdato_ferie": "2025-07-01",
            "sluttdato_ferie": "2025-07-14",
            "total_reisebelop": 20000,
            "antall_personer": 2,
            "antall_dager_sengeleie": 5,
            "ekstra_dag_for_legebesok": True,
            "dato_legebesok": "2025-07-05",
        }
        result, status = beregn_feriekompensasjon(payload)
        self.assertEqual(status, 200)
        self.assertIn("total_kompensasjon", result)
        self.assertGreater(result["total_kompensasjon"], 0)

    def test_invalid_date_range(self):
        payload = {
            "startdato_ferie": "2025-07-14",
            "sluttdato_ferie": "2025-07-01",
            "total_reisebelop": 20000,
            "antall_personer": 2,
            "antall_dager_sengeleie": 5,
            "ekstra_dag_for_legebesok": False,
            "dato_legebesok": "2025-07-05",
        }
        _, status = beregn_feriekompensasjon(payload)
        self.assertEqual(status, 400)

    def test_missing_fields(self):
        payload = {
            "startdato_ferie": "2025-07-01",
            "sluttdato_ferie": "2025-07-14",
        }
        _, status = beregn_feriekompensasjon(payload)
        self.assertEqual(status, 400)


if __name__ == "__main__":
    unittest.main()
