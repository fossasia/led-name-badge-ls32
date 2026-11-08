import datetime
from array import array
from unittest import TestCase
from unittest.mock import patch

import abstract_write_method_test
from lednamebadge import LedNameBadge, Ls32HeaderGenerator, CustomHeaderGenerator
from lednamebadge import WriteUsbHidApi, WriteLibUsb, WriteSerial, WriteUsbHidApiCustom, WriteLibUsbCustom


class Test(TestCase):
    def setUp(self):
        self.test_date = datetime.datetime(2022, 11, 13, 17, 38, 24)
        # One byte-column (8 pixels wide, 11 rows), all pixels off / all pixels on
        self.blank = [(array('B', [0x00] * 11), 1)]
        self.full = [(array('B', [0xff] * 11), 1)]

    def test_header_generator_binding(self):
        self.assertIsInstance(WriteUsbHidApi().header_generator, Ls32HeaderGenerator)
        self.assertIsInstance(WriteLibUsb().header_generator, Ls32HeaderGenerator)
        self.assertIsInstance(WriteSerial().header_generator, Ls32HeaderGenerator)
        self.assertEqual((WriteUsbHidApi().vendor_id, WriteUsbHidApi().product_id), (0x0416, 0x5020))
        self.assertEqual((WriteLibUsb().vendor_id, WriteLibUsb().product_id), (0x0416, 0x5020))

        self.assertIsInstance(WriteUsbHidApiCustom().header_generator, CustomHeaderGenerator)
        self.assertIsInstance(WriteLibUsbCustom().header_generator, CustomHeaderGenerator)
        self.assertEqual((WriteUsbHidApiCustom().vendor_id, WriteUsbHidApiCustom().product_id), (0x204c, 0x4359))
        self.assertEqual((WriteLibUsbCustom().vendor_id, WriteLibUsbCustom().product_id), (0x204c, 0x4359))

    def test_ls32_create_buffers(self):
        buffers = Ls32HeaderGenerator().create_buffers(self.full, (4,), (0,), (0,), (0,), 100)
        self.assertEqual(1, len(buffers))
        buf = buffers[0]
        # The single buffer is the 64 byte LS32 header, followed by the bitmap data.
        # header() writes the current date into bytes 38..43, so compare the rest
        # against a header built with a fixed date.
        expected_header = LedNameBadge.header((1,), (4,), (0,), (0,), (0,), 100, self.test_date)
        self.assertEqual(64 + 11, len(buf))
        self.assertEqual(expected_header[0:38], list(buf[0:38]))
        self.assertEqual(expected_header[44:], list(buf[44:64]))
        self.assertEqual(list(self.full[0][0]), list(buf[64:]))

    def test_custom_create_buffers_structure(self):
        buffers = CustomHeaderGenerator().create_buffers(self.blank, (4,), (0,), (0,), (0,), 100)
        self.assertEqual(8, len(buffers))
        # Five header packets, all 64 bytes
        for packet in buffers[0:5]:
            self.assertEqual(64, len(packet))
        self.assertEqual([0x4c, 0x43, 0x59, 0xf2], list(buffers[0][0:4]))
        self.assertEqual([0x4c, 0x43, 0x59, 0xdd], list(buffers[1][0:4]))
        self.assertEqual([0xff] * 64, list(buffers[3]))
        self.assertEqual([0xff] * 64, list(buffers[4]))
        # Payload: 8 x 0xff, one 0x00, then the encoded bitmap (blank here)
        self.assertEqual([0xff] * 8 + [0x00] + [0x00] * 12, list(buffers[5]))
        # Two footer packets
        self.assertEqual([0x00] * 64, list(buffers[6]))
        self.assertEqual([0x4c, 0x43, 0x59, 0x99], list(buffers[7][0:4]))
        self.assertEqual(64, len(buffers[7]))

    def test_custom_create_buffers_encoding(self):
        buffers = CustomHeaderGenerator().create_buffers(self.full, (4,), (0,), (0,), (0,), 100)
        # All pixels on: each 2-column chunk is 22 set bits + 2 discard bits = 0xff, 0xff, 0xfc.
        # The bitmap is 8 pixels wide, so there are 4 chunks = 12 bytes.
        self.assertEqual([0xff] * 8 + [0x00] + [0xff, 0xff, 0xfc] * 4, list(buffers[5]))

    def test_custom_packets_are_copies(self):
        gen = CustomHeaderGenerator()
        buffers = gen.create_buffers(self.blank, (4,), (0,), (0,), (0,), 100)
        buffers[0].extend([0x00] * 64)  # write methods pad the buffers they get
        buffers2 = gen.create_buffers(self.blank, (4,), (0,), (0,), (0,), 100)
        self.assertEqual(64, len(buffers2[0]))

    def test_transport_binding(self):
        self.assertEqual('hidapi', WriteUsbHidApi.transport)
        self.assertEqual('libusb', WriteLibUsb.transport)
        self.assertEqual('pyserial', WriteSerial.transport)
        # The custom write methods use the same transports as their base methods
        self.assertEqual('hidapi', WriteUsbHidApiCustom.transport)
        self.assertEqual('libusb', WriteLibUsbCustom.transport)
        self.assertEqual(0, WriteUsbHidApi.chunk_delay)
        self.assertEqual(0.1, WriteUsbHidApiCustom.chunk_delay)

    def test_custom_rejects_12row_bitmaps(self):
        bitmap12 = [(array('B', [0x00] * 12), 1)]  # one byte-column of a 12x48 badge
        with self.assertRaises(ValueError):
            CustomHeaderGenerator().create_buffers(bitmap12, (4,), (0,), (0,), (0,), 100)

    def test_write_refuses_custom_method(self):
        # LedNameBadge.write() writes an LS32 buffer; it must not send it to the custom device
        custom_method = WriteUsbHidApiCustom()
        with patch.object(LedNameBadge, '_find_write_method', return_value=custom_method):
            with patch.object(custom_method, 'write') as write_mock:
                with patch.object(custom_method, 'close'):
                    with self.assertRaises(SystemExit):
                        LedNameBadge.write(array('B', [1, 2, 3]), 'hidapi-custom')
        write_mock.assert_not_called()

    def test_write_bitmaps_uses_bound_generator(self):
        written = []

        class FakeMethod:
            header_generator = CustomHeaderGenerator()

            def write(self, buf):
                written.append(list(buf))

            def close(self):
                pass

        with patch.object(LedNameBadge, '_find_write_method', return_value=FakeMethod()):
            LedNameBadge.write_bitmaps(self.blank, (4,), (0,), (0,), (0,), 100)
        # All 8 buffers of the custom protocol are written in one single write,
        # each padded to 64 bytes: 8 * 64 = 512 bytes in protocol order.
        self.assertEqual(1, len(written))
        buf = written[0]
        self.assertEqual(8 * 64, len(buf))
        self.assertEqual([0x4c, 0x43, 0x59, 0xf2], buf[0:4])
        self.assertEqual([0xff] * 8 + [0x00] + [0x00] * 12, buf[5 * 64:5 * 64 + 21])
        self.assertEqual([0x4c, 0x43, 0x59, 0x99], buf[7 * 64:7 * 64 + 4])


class TestAutoNarrowing(abstract_write_method_test.AbstractWriteMethodTest):
    @patch('sys.platform', new='darwin')
    def test_auto_darwin_hidapi_not_ready_prints_install_hints(self):
        # 'auto' is narrowed to hidapi on macOS; the readiness check must still run
        method_obj, output, _ = self.prepare_modules(True, False, True,
                                                     lambda m: m._find_write_method('auto', 'auto'))
        self.assertIsNone(method_obj)
        self.assertIn('is not possible to be used', output)
        self.assertIn('pyhidapi', output)

    @patch('sys.platform', new='windows')
    def test_auto_windows_libusb_not_ready_prints_install_hints(self):
        # 'auto' is narrowed to libusb on Windows; the readiness check must still run
        method_obj, output, _ = self.prepare_modules(False, True, True,
                                                     lambda m: m._find_write_method('auto', 'auto'))
        self.assertIsNone(method_obj)
        self.assertIn('is not possible to be used', output)
        self.assertIn('pyusb', output)

    @patch('sys.platform', new='linux')
    def test_auto_list_shows_hidapi_methods_only(self):
        # Listing devices must not enumerate via libusb (that detaches kernel drivers),
        # but the custom badge must be discoverable via its hidapi method.
        method_obj, output, _ = self.prepare_modules(True, True, True,
                                                     lambda m: m._find_write_method('auto', 'list'))
        self.assertIn("Known device ids with method 'hidapi' are:", output)
        self.assertIn("Known device ids with method 'hidapi-custom' are:", output)
        self.assertNotIn("Known device ids with method 'libusb' are:", output)
        self.assertNotIn("Known device ids with method 'libusb-custom' are:", output)


class TestDeviceIds(abstract_write_method_test.AbstractWriteMethodTest):
    def test_device_enumeration_uses_bound_ids(self):
        # The mocked transports must be enumerated with the IDs bound to the write method
        _, _, mocks = self.prepare_modules(True, True, True,
                                           lambda m: m.get_available_device_ids('hidapi-custom'))
        mocks['pyhidapi'].hid_enumerate.assert_called_with(0x204c, 0x4359)

        _, _, mocks = self.prepare_modules(True, True, True,
                                           lambda m: m.get_available_device_ids('hidapi'))
        mocks['pyhidapi'].hid_enumerate.assert_called_with(0x0416, 0x5020)

        _, _, mocks = self.prepare_modules(True, True, True,
                                           lambda m: m.get_available_device_ids('libusb-custom'))
        mocks['usb'].core.find.assert_called_with(idVendor=0x204c, idProduct=0x4359, find_all=True)

        _, _, mocks = self.prepare_modules(True, True, True,
                                           lambda m: m.get_available_device_ids('libusb'))
        mocks['usb'].core.find.assert_called_with(idVendor=0x0416, idProduct=0x5020, find_all=True)
