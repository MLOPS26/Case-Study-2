import pytest
from pydantic import ValidationError
from datamodels.datamodels import ImageInput, ImageResponse, TextInput, User


class TestImageInput:
    def test_image_input_with_url(self):
        data = ImageInput(
            question="What is this?", image_url="https://example.com/image.jpg"
        )
        assert data.question == "What is this?"
        assert data.image_url == "https://example.com/image.jpg"
        assert data.image_b64 is None

    def test_image_input_with_b64(self):
        data = ImageInput(
            question="Solve this problem", image_b64="base64encodedstring"
        )
        assert data.question == "Solve this problem"
        assert data.image_b64 == "base64encodedstring"
        assert data.image_url is None

    def test_image_input_both_image_types(self):
        data = ImageInput(
            question="Test",
            image_url="https://example.com/image.jpg",
            image_b64="base64encodedstring",
        )
        assert data.image_url == "https://example.com/image.jpg"
        assert data.image_b64 == "base64encodedstring"

    def test_image_input_no_images(self):
        data = ImageInput(question="What is 2+2?")
        assert data.question == "What is 2+2?"
        assert data.image_url is None
        assert data.image_b64 is None

    def test_image_input_missing_question(self):
        """Test that ImageInput requires question field"""
        with pytest.raises(ValidationError):
            ImageInput()


class TestImageResponse:
    def test_image_response_valid(self):
        """Test ImageResponse with valid response"""
        data = ImageResponse(response="This is the answer")
        assert data.response == "This is the answer"

    def test_image_response_empty_string(self):
        data = ImageResponse(response="")
        assert data.response == ""

    def test_image_response_missing_field(self):
        with pytest.raises(ValidationError):
            ImageResponse()


class TestTextInput:
    def test_text_input_valid(self):
        data = TextInput(input_string="Hello world")
        assert data.input_string == "Hello world"

    def test_text_input_empty(self):
        data = TextInput(input_string="")
        assert data.input_string == ""

    def test_text_input_missing_field(self):
        with pytest.raises(ValidationError):
            TextInput()


class TestUser:
    def test_user_valid(self):
        data = User(
            uuid="123e4567-e89b-12d3-a456-426614174000", email="test@example.com"
        )
        assert data.uuid == "123e4567-e89b-12d3-a456-426614174000"
        assert data.email == "test@example.com"

    def test_user_missing_uuid(self):
        with pytest.raises(ValidationError):
            User(email="test@example.com")

    def test_user_missing_email(self):
        with pytest.raises(ValidationError):
            User(uuid="123e4567-e89b-12d3-a456-426614174000")

    def test_user_invalid_email_format(self):
        data = User(uuid="123e4567-e89b-12d3-a456-426614174000", email="not-an-email")
        assert data.email == "not-an-email"

    def test_user_extra_fields_ignored(self):
        data = User(
            uuid="123e4567-e89b-12d3-a456-426614174000",
            email="test@example.com",
            extra_field="ignored",
        )
        assert data.uuid == "123e4567-e89b-12d3-a456-426614174000"
        assert data.email == "test@example.com"
        assert not hasattr(data, "extra_field")
