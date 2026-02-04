import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from local_model import query_local


@pytest.fixture
def mock_model():
    model = MagicMock()
    model.generate = MagicMock(return_value=[[1, 2, 3, 4, 5]])
    return model


@pytest.fixture
def mock_processor():
    processor = MagicMock()
    processor.apply_chat_template = MagicMock(return_value="formatted_text")
    processor.return_value = MagicMock(
        input_ids=[[1, 2, 3]],
        to=MagicMock(return_value=MagicMock(input_ids=[[1, 2, 3]])),
    )
    processor.batch_decode = MagicMock(return_value=["The answer is 42."])
    return processor


@pytest.fixture
def sample_image():
    return Image.new("RGB", (10, 10), color="blue")


class TestQueryLocal:
    @patch("local_model.process_vision_info")
    def test_query_local_success(
        self, mock_vision_info, mock_model, mock_processor, sample_image
    ):
        mock_vision_info.return_value = ([sample_image], None)

        result = query_local(
            model=mock_model,
            processor=mock_processor,
            device="cpu",
            image=sample_image,
            question="What is 2+2?",
        )

        assert result == "The answer is 42."
        assert mock_processor.apply_chat_template.called
        assert mock_model.generate.called
        assert mock_processor.batch_decode.called

    def test_query_local_missing_image(self, mock_model, mock_processor):
        with pytest.raises(ValueError, match="Missing image"):
            query_local(
                model=mock_model,
                processor=mock_processor,
                device="cpu",
                image=None,
                question="What is this?",
            )

    @patch("local_model.process_vision_info")
    def test_query_local_math_tutor_prompt(
        self, mock_vision_info, mock_model, mock_processor, sample_image
    ):
        mock_vision_info.return_value = ([sample_image], None)

        query_local(
            model=mock_model,
            processor=mock_processor,
            device="cpu",
            image=sample_image,
            question="Solve this equation",
        )
        call_args = mock_processor.apply_chat_template.call_args
        messages = call_args[0][0]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert "type" in messages[0]["content"][1]
        assert "text" in messages[0]["content"][1]

        text_content = messages[0]["content"][1]["text"]
        assert "math tutor" in text_content.lower()
        assert "Solve this equation" in text_content

    @patch("local_model.process_vision_info")
    def test_query_local_max_tokens(
        self, mock_vision_info, mock_model, mock_processor, sample_image
    ):
        mock_vision_info.return_value = ([sample_image], None)

        query_local(
            model=mock_model,
            processor=mock_processor,
            device="cpu",
            image=sample_image,
            question="Test question",
        )

        call_kwargs = mock_model.generate.call_args[1]
        assert "max_new_tokens" in call_kwargs
        assert call_kwargs["max_new_tokens"] == 512

    @patch("local_model.process_vision_info")
    def test_query_local_device_handling(
        self, mock_vision_info, mock_model, mock_processor, sample_image
    ):
        mock_vision_info.return_value = ([sample_image], None)

        mock_inputs = MagicMock()
        mock_processor.return_value = mock_inputs

        query_local(
            model=mock_model,
            processor=mock_processor,
            device="cuda",
            image=sample_image,
            question="Test",
        )

        mock_inputs.to.assert_called_with("cuda")

    @patch("local_model.process_vision_info")
    def test_query_local_with_different_questions(
        self, mock_vision_info, mock_model, mock_processor, sample_image
    ):
        mock_vision_info.return_value = ([sample_image], None)

        questions = [
            "What is the derivative of x^2?",
            "Solve for x: 2x + 5 = 15",
            "Explain the Pythagorean theorem",
            "What is calculus?",
        ]

        for question in questions:
            result = query_local(
                model=mock_model,
                processor=mock_processor,
                device="cpu",
                image=sample_image,
                question=question,
            )

            assert isinstance(result, str)
            assert len(result) > 0

    @patch("local_model.process_vision_info")
    def test_query_local_tokenization(
        self, mock_vision_info, mock_model, mock_processor, sample_image
    ):
        mock_vision_info.return_value = ([sample_image], None)

        query_local(
            model=mock_model,
            processor=mock_processor,
            device="cpu",
            image=sample_image,
            question="Test",
        )

        call_kwargs = mock_processor.apply_chat_template.call_args[1]
        assert call_kwargs.get("tokenize") is False
        assert call_kwargs.get("add_generation_prompt") is True

    @patch("local_model.process_vision_info")
    def test_query_local_batch_decode_params(
        self, mock_vision_info, mock_model, mock_processor, sample_image
    ):
        mock_vision_info.return_value = ([sample_image], None)

        query_local(
            model=mock_model,
            processor=mock_processor,
            device="cpu",
            image=sample_image,
            question="Test",
        )

        call_kwargs = mock_processor.batch_decode.call_args[1]
        assert call_kwargs.get("skip_special_tokens") is True
        assert call_kwargs.get("clean_up_tokenization_spaces") is False
