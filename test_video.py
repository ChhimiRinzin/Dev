import unittest
from unittest.mock import patch
from devsentinel.video import sample_video, MAX_BYTES

class TestVideo(unittest.TestCase):
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            sample_video(b'')
    def test_large_rejected(self):
        with self.assertRaises(ValueError):
            sample_video(b'a' * (MAX_BYTES + 1))
    def test_frame_count_rejected(self):
        with self.assertRaises(ValueError):
            sample_video(b'file', frame_count=9)
    def test_missing_ffmpeg(self):
        with patch('devsentinel.video.shutil.which', return_value=None):
            with self.assertRaises(RuntimeError):
                sample_video(b'file')

if __name__ == '__main__':
    unittest.main()
