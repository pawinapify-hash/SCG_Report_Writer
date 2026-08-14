import io
import unittest
from unittest.mock import patch

from PIL import Image

from report_writer.key_thematic import chat_text
from report_writer.pptx_extractor import describe_images


class FakeResponse:
    def __init__(self, data):
        self._data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


class OpenAiPayloadTests(unittest.TestCase):
    @patch("report_writer.key_thematic.requests.post")
    def test_text_payload_has_fixed_completion_limit_without_temperature(self, post):
        post.return_value = FakeResponse({
            "choices": [{"message": {"content": "ok"}}],
            "usage": {},
        })

        chat_text(
            [{"role": "user", "content": "test"}],
            api_key="test-key",
            max_completion_tokens=4000,
        )

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["max_completion_tokens"], 4000)
        self.assertNotIn("temperature", payload)

    @patch("report_writer.pptx_extractor.requests.post")
    def test_image_payload_has_fixed_completion_limit_without_temperature(self, post):
        post.return_value = FakeResponse({
            "choices": [{"message": {"content": '[{"post": 1, "image_description": "ok"}]'}}],
            "usage": {},
        })
        image_buffer = io.BytesIO()
        Image.new("RGB", (1, 1), "white").save(image_buffer, format="PNG")
        posts = [{"image": image_buffer.getvalue(), "image_ext": "png"}]

        descriptions, _ = describe_images(
            posts,
            api_key="test-key",
            model="gpt-5.6-luna",
            base_url="https://api.openai.com/v1",
            max_completion_tokens=4000,
            retries=0,
        )

        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["max_completion_tokens"], 4000)
        self.assertNotIn("temperature", payload)
        self.assertEqual(descriptions[0], "ok")


if __name__ == "__main__":
    unittest.main()
