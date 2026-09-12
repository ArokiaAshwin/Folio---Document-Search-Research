import unittest
from fastapi.testclient import TestClient
from backend.main import app

class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_guest_auth(self):
        response = self.client.post("/api/auth/guest")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertTrue(data["user"]["is_guest"])

    def test_documents_list(self):
        # Authenticate as guest
        auth_resp = self.client.post("/api/auth/guest")
        token = auth_resp.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/documents", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("documents", data)
        self.assertIn("stats", data)

    def test_settings(self):
        response = self.client.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("provider", data)
        self.assertIn("model", data)

if __name__ == "__main__":
    unittest.main()
