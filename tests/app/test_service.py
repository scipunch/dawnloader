import pytest

from app import service


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True),
        ("https://youtu.be/dQw4w9WgXcQ", True),
        ("https://www.instagram.com/p/ABC123/", True),
        ("https://instagram.com/p/ABC123/", True),
        ("https://example.com", False),
        ("not a url", False),
        ("", False),
    ],
)
def test_is_media_url(url: service.Url, *, expected: bool) -> None:
    """Test URL validation function."""
    assert service.is_media_url_supported(url) == expected
