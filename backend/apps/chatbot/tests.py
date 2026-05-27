from rest_framework import status
from rest_framework.test import APITestCase


class ChatAPITest(APITestCase):
    def test_chat_endpoint(self):
        data = {
            "message": "Hello"
        }

        response = self.client.post("/api/chat/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("session_id", response.data)
        self.assertIn("reply", response.data)

# Create your tests here.
