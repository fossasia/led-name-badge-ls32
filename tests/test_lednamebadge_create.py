from array import array
from unittest import TestCase

from lednamebadge import SimpleTextAndIcons as testee


class Test(TestCase):
    def test_bitmap_png(self):
        creator = testee()
        buf = creator.bitmap("resources/bitpatterns.png")
        self.assertEqual((array('B',
                                [128, 64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128, 64, 32, 0, 1, 2, 3,
                                 4, 5, 15, 31, 63, 127, 255]),
                          3), buf)

    def test_bitmap_text(self):
        creator = testee()
        buf = creator.bitmap("/:HEART2:\\")
        self.assertEqual((array('B',
                                [0, 0, 2, 6, 12, 24, 48, 96, 192, 128, 0, 0, 12, 30, 63, 63, 63, 31, 15, 7, 3, 1, 0, 96,
                                 240, 248, 248, 248, 240, 224, 192, 128, 0, 0, 128, 192, 96, 48, 24, 12, 6, 2, 0, 0]),
                          4), buf)

    def test_preload(self):
        creator = testee()
        self.assertFalse(creator.are_preloaded_unused())
        creator.add_preload_img("resources/bitpatterns.png")
        self.assertTrue(creator.are_preloaded_unused())
        buf = creator.bitmap("\x01")
        self.assertFalse(creator.are_preloaded_unused())
        self.assertEqual((array('B',
                                [128, 64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128, 64, 32, 0, 1, 2, 3,
                                 4, 5, 15, 31, 63, 127, 255]),
                          3), buf)

    def test_clock_strings_with_colons(self):
        """Regression test for issue #22: colons in clock strings must not crash with IndexError."""
        creator = testee()
        clock_strings = ('23:18:35', '22:26:15', '01:02:03', '12:00:00')
        for s in clock_strings:
            buf, cols = creator.bitmap(s)
            self.assertEqual(cols, len(s), "Clock '%s' should render %d cols, got %d" % (s, len(s), cols))

    def test_text_with_colons(self):
        """Plain text with multiple colons, ratios, and unknown tokens must pass through unchanged."""
        creator = testee()
        test_cases = [
            ('Current time: 23:18:35', 22),
            ('Ratio 1:2:3', 11),
            ('Notice: test: message', 21),
            (':unknown_icon:', 14),
            (':missing.png:', 13),
        ]
        for text, expected_cols in test_cases:
            buf, cols = creator.bitmap(text)
            self.assertEqual(cols, expected_cols, "Text '%s' should render %d cols, got %d" % (text, expected_cols, cols))

    def test_preloaded_numeric_index(self):
        """Numeric index :N: only resolves when image N is actually preloaded."""
        creator = testee()
        # Without preload, :1: passes through as literal text (3 columns)
        buf, cols = creator.bitmap(":1:")
        self.assertEqual(cols, 3)

        # With preload, :1: resolves to image #1
        creator.add_preload_img("resources/bitpatterns.png")
        buf, cols = creator.bitmap(":1:")
        self.assertEqual(cols, 3)  # bitpatterns.png is 3 columns wide
        self.assertEqual(buf, array('B',
                                     [128, 64, 32, 16, 8, 4, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 128, 64, 32, 0, 1, 2, 3,
                                      4, 5, 15, 31, 63, 127, 255]))

        # Out-of-bounds numeric reference stays literal text
        buf, cols = creator.bitmap(":99:")
        self.assertEqual(cols, 4)

    def test_escaped_colons(self):
        """:: is the documented escape for a literal colon."""
        creator = testee()
        buf, cols = creator.bitmap("::")
        self.assertEqual(cols, 1)

        # 23::18::35 should produce the identical bitmap buffer and columns as 23:18:35
        buf_literal, cols_literal = creator.bitmap("23:18:35")
        buf_escaped, cols_escaped = creator.bitmap("23::18::35")
        self.assertEqual(cols_literal, cols_escaped)
        self.assertEqual(buf_literal, buf_escaped)

    def test_bitmap_char_invalid_control_char(self):
        """bitmap_char raises an actionable IndexError on unknown control characters."""
        creator = testee()
        with self.assertRaises(IndexError) as ctx:
            creator.bitmap_char(chr(18))
        self.assertIn("no preloaded image #18", str(ctx.exception))
        self.assertIn("escape colons as '::'", str(ctx.exception))
