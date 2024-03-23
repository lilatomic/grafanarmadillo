from grafanarmadillo.util import PathCodec


def test_encode_decode():
    segments = ["folder", "subfolder", "file with / in name"]
    encoded_path = PathCodec.encode(segments)
    decoded_segments = PathCodec.decode(encoded_path)
    assert decoded_segments == segments


def test_encode_decode_special_characters():
    segments = ["&", "?", "!"]
    encoded_path = PathCodec.encode(segments)
    decoded_segments = PathCodec.decode(encoded_path)
    assert decoded_segments == segments


def test_encode_decode_unicode_characters():
    segments = ["😀", "🚀", "🌟"]
    encoded_path = PathCodec.encode(segments)
    decoded_segments = PathCodec.decode(encoded_path)
    assert decoded_segments == segments


def test_encode_decode_numbers():
    segments = ["123", "456", "789"]
    encoded_path = PathCodec.encode(segments)
    decoded_segments = PathCodec.decode(encoded_path)
    assert decoded_segments == segments


def test_encode_decode_path_with_space():
    segments = ["path with space"]
    encoded_path = PathCodec.encode(segments)
    decoded_segments = PathCodec.decode(encoded_path)
    assert decoded_segments == segments


def test_encode_decode_path_with_special_characters():
    segments = ["$path^with!special&characters"]
    encoded_path = PathCodec.encode(segments)
    decoded_segments = PathCodec.decode(encoded_path)
    assert decoded_segments == segments
