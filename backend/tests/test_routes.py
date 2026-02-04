import pytest
import uuid
import io
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture(scope="module")
def client():
    with (
        patch("routes.Qwen2VLForConditionalGeneration.from_pretrained") as mock_model,
        patch("routes.AutoProcessor.from_pretrained") as mock_processor,
    ):
        mock_model.return_value = MagicMock()
        mock_processor.return_value = MagicMock()

        from routes import app

        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def sample_user_data():
    return {"uuid": str(uuid.uuid4()), "email": "test@example.com"}


@pytest.fixture
def mock_image_file():
    img = Image.new("RGB", (10, 10), color="red")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    return img_byte_arr


class TestDeviceEndpoint:
    def test_get_device(self, client):
        response = client.get("/device")
        assert response.status_code == 200
        data = response.json()
        assert "device" in data
        assert data["device"] in ["cuda", "cpu", None]


class TestUserEndpoints:

    def test_create_user_success(self, client):
        response = client.post("/users", data={"email": "newuser@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert "uuid" in data
        assert data["email"] == "newuser@example.com"

    def test_create_user_duplicate_email(self, client):
        email = "duplicate@example.com"

        response1 = client.post("/users", data={"email": email})
        assert response1.status_code == 200

        response2 = client.post("/users", data={"email": email})
        assert response2.status_code == 200
        data = response2.json()
        assert "error" in data or "uuid" in data

    def test_create_user_missing_email(self, client):
        response = client.post("/users", data={})
        assert response.status_code == 422


class TestHistoryEndpoints:
    def test_get_history_empty(self, client):
        user_response = client.post("/users", data={"email": "history@example.com"})
        user_uuid = user_response.json()["uuid"]

        response = client.get(f"/history/{user_uuid}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_history_nonexistent_user(self, client):
        fake_uuid = str(uuid.uuid4())
        response = client.get(f"/history/{fake_uuid}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0


class TestInferenceEndpoint:
    @patch("routes.query_local")
    def test_inference_success(self, mock_query_local, client, mock_image_file):
        user_response = client.post("/users", data={"email": "inference@example.com"})
        user_uuid = user_response.json()["uuid"]
        mock_query_local.return_value = "The answer is 4."
        response = client.post(
            "/inference",
            data={"question": "What is 2+2?", "user_uuid": user_uuid},
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["response"] == "The answer is 4."
        history_response = client.get(f"/history/{user_uuid}")
        history = history_response.json()
        assert len(history) == 1
        assert history[0]["question"] == "What is 2+2?"
        assert history[0]["response"] == "The answer is 4."

    def test_inference_missing_question(self, client, mock_image_file):
        user_uuid = str(uuid.uuid4())
        response = client.post(
            "/inference",
            data={"user_uuid": user_uuid},
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
        )

        assert response.status_code == 422  # Validation error

    def test_inference_missing_user_uuid(self, client, mock_image_file):
        response = client.post(
            "/inference",
            data={"question": "What is this?"},
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
        )

        assert response.status_code == 422

    def test_inference_missing_file(self, client):
        user_uuid = str(uuid.uuid4())

        response = client.post(
            "/inference", data={"question": "What is this?", "user_uuid": user_uuid}
        )

        assert response.status_code == 422

    @patch("routes.query_local")
    def test_inference_invalid_image(self, mock_query_local, client):
        user_uuid = str(uuid.uuid4())

        invalid_file = io.BytesIO(b"not an image")

        response = client.post(
            "/inference",
            data={"question": "What is this?", "user_uuid": user_uuid},
            files={"file": ("test.jpg", invalid_file, "image/jpeg")},
        )

        assert response.status_code in [400, 500]

    @patch("routes.query_local")
    def test_inference_model_error(self, mock_query_local, client, mock_image_file):
        user_response = client.post("/users", data={"email": "error@example.com"})
        user_uuid = user_response.json()["uuid"]

        mock_query_local.side_effect = Exception("Model inference failed")

        response = client.post(
            "/inference",
            data={"question": "What is this?", "user_uuid": user_uuid},
            files={"file": ("test.jpg", mock_image_file, "image/jpeg")},
        )

        assert response.status_code == 500


class TestIntegration:

    @patch("routes.query_local")
    def test_complete_user_workflow(self, mock_query_local, client, mock_image_file):
        user_response = client.post("/users", data={"email": "workflow@example.com"})
        assert user_response.status_code == 200
        user_uuid = user_response.json()["uuid"]
        mock_query_local.return_value = "Answer 1"
        response1 = client.post(
            "/inference",
            data={"question": "Question 1", "user_uuid": user_uuid},
            files={"file": ("test1.jpg", mock_image_file, "image/jpeg")},
        )
        assert response1.status_code == 200
        mock_image_file.seek(0)

        mock_query_local.return_value = "Answer 2"
        response2 = client.post(
            "/inference",
            data={"question": "Question 2", "user_uuid": user_uuid},
            files={"file": ("test2.jpg", mock_image_file, "image/jpeg")},
        )
        assert response2.status_code == 200
        history_response = client.get(f"/history/{user_uuid}")
        assert history_response.status_code == 200
        history = history_response.json()

        assert len(history) == 2
        assert history[0]["question"] == "Question 2"
        assert history[0]["response"] == "Answer 2"
        assert history[1]["question"] == "Question 1"
        assert history[1]["response"] == "Answer 1"
