import unittest
from backend.main import app

class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_guest_auth(self):
        response = self.client.post("/api/auth/guest")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("access_token", data)
        self.assertTrue(data["user"]["is_guest"])

    def test_documents_list(self):
        # Authenticate as guest
        auth_resp = self.client.post("/api/auth/guest")
        token = auth_resp.get_json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/documents", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("documents", data)
        self.assertIn("stats", data)

    def test_settings(self):
        response = self.client.get("/api/settings")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("provider", data)
        self.assertIn("model", data)

    def test_email_register_and_login(self):
        import uuid
        test_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        test_password = "securePassword123!"

        # 1. Register with email and password
        reg_resp = self.client.post("/api/auth/register", json={
            "email": test_email,
            "password": test_password
        })
        self.assertEqual(reg_resp.status_code, 200)
        reg_data = reg_resp.get_json()
        self.assertIn("access_token", reg_data)
        self.assertEqual(reg_data["user"]["email"], test_email)
        self.assertFalse(reg_data["user"]["is_guest"])

        # 2. Login with email
        login_resp = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        self.assertEqual(login_resp.status_code, 200)
        login_data = login_resp.get_json()
        self.assertIn("access_token", login_data)

        # 3. Login with wrong password should fail
        bad_login = self.client.post("/api/auth/login", json={
            "email": test_email,
            "password": "wrongpassword"
        })
        self.assertEqual(bad_login.status_code, 401)

    def test_google_demo_auth(self):
        # Test Google OAuth demo token handler
        demo_resp = self.client.post("/api/auth/google", json={
            "credential": "demo_google:alex_test@gmail.com:Alex Test"
        })
        self.assertEqual(demo_resp.status_code, 200)
        demo_data = demo_resp.get_json()
        self.assertIn("access_token", demo_data)
        self.assertEqual(demo_data["user"]["email"], "alex_test@gmail.com")
        self.assertEqual(demo_data["user"]["username"], "Alex Test")

    def test_auth_config(self):
        resp = self.client.get("/api/auth/config")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("google_client_id", data)

if __name__ == "__main__":
    unittest.main()
