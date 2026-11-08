from unittest.mock import patch

import abstract_write_method_test


class Test(abstract_write_method_test.AbstractWriteMethodTest):
    @patch('sys.platform', new='linux')
    def test_list(self):
        method, output = self.call_find(True, True, True, 'list', 'auto')
        self.assertIn("Available write methods:", output)
        self.assertIn("'auto'", output)
        self.assertIn("'hidapi'", output)
        self.assertIn("'libusb'", output)
        self.assertIn("'pyserial'", output)

        method, output = self.call_find(True, True, True, 'hidapi', 'list')
        self.assertIn("Known device ids with method 'hidapi' are:", output)
        self.assertIn("'3-4:5-6': HidApi Test", output)

        method, output = self.call_find(True, True, True, 'libusb', 'list')
        self.assertIn("Known device ids with method 'libusb' are:", output)
        self.assertIn("'3:4:2': LibUsb Test", output)

    @patch('sys.platform', new='linux')
    def test_unknown(self):
        method, output = self.call_find(True, True, True, 'hello', 'auto')
        self.assertIn("Unknown write method 'hello'", output)
        self.assertIn("Available write methods:", output)

    @patch('sys.platform', new='linux')
    def test_all_in_linux_positive(self):
        method, output = self.call_find(True, True, True, 'auto', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

        method, output = self.call_find(True, True, True, 'libusb', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

        method, output = self.call_find(True, True, True, 'hidapi', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

    @patch('sys.platform', new='linux')
    def test_only_one_lib_linux_positive(self):
        method, output = self.call_find(False, True, True, 'auto', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

        method, output = self.call_find(False, True, True, 'hidapi', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

        method, output = self.call_find(True, False, True, 'auto', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

        method, output = self.call_find(True, False, True, 'libusb', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

    @patch('sys.platform', new='windows')
    def test_windows_positive(self):
        method, output = self.call_find(True, False, True, 'auto', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

        method, output = self.call_find(True, False, True, 'libusb', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

    @patch('sys.platform', new='darwin')
    def test_macos_positive(self):
        method, output = self.call_find(False, True, True, 'auto', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

        method, output = self.call_find(False, True, True, 'hidapi', 'auto')
        self.assertIn('device initialized', output)
        self.assertIsNotNone(method)

    @patch('sys.version_info', new=[2])
    def test_python2_positive(self):
        method, output = self.call_find(True, True, True, 'auto', 'auto')
        self.assertIn('device initialized', output)
        self.assertIn('Preferring method libusb', output)
        self.assertIsNotNone(method)


    # -------------------------------------------------------------------------


    @patch('sys.platform', new='linux')
    def test_all_in_linux_negative(self):
        method, output = self.call_find(True, True, False, 'auto', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('device is not available', output)
        self.assertIsNone(method)

        method, output = self.call_find(True, True, False, 'libusb', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('device is not available', output)
        self.assertIsNone(method)

        method, output = self.call_find(True, True, False, 'hidapi', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('device is not available', output)
        self.assertIsNone(method)

    @patch('sys.platform', new='linux')
    def test_all_out_linux_negative(self):
        method, output = self.call_find(False, False, False, 'auto', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('One of the python packages', output)
        self.assertIsNone(method)

        method, output = self.call_find(False, False, False, 'libusb', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('is not possible to be used', output)
        self.assertIsNone(method)

        method, output = self.call_find(False, False, False, 'hidapi', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('is not possible to be used', output)
        self.assertIsNone(method)

    @patch('sys.platform', new='windows')
    def test_windows_negative(self):
        method, output = self.call_find(True, False, True, 'hidapi', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('is not possible to be used', output)
        self.assertIsNone(method)

        method, output = self.call_find(True, True, False, 'hidapi', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('If not working, please use', output)
        self.assertIsNone(method)

    @patch('sys.platform', new='darwin')
    def test_macos_negative(self):
        method, output = self.call_find(False, True, True, 'libusb', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('please use method', output)
        self.assertIsNone(method)

    @patch('sys.version_info', new=[2])
    def test_python2_negative(self):
        method, output = self.call_find(True, True, True, 'hidapi', 'auto')
        self.assertNotIn('device initialized', output)
        self.assertIn('Please use method', output)
        self.assertIsNone(method)


    # -------------------------------------------------------------------------


    def call_find(self, pyusb_available, pyhidapi_available, device_available, method, device_id):
        self.print_test_conditions(pyusb_available, pyhidapi_available, device_available, method, device_id)
        method_obj, output, _ = self.prepare_modules(pyusb_available, pyhidapi_available, device_available,
                                                  lambda m: m._find_write_method(method, device_id))
        self.assertEqual(pyusb_available, 'usb.core detected' in output)
        self.assertEqual(pyhidapi_available, 'pyhidapi detected' in output)
        return method_obj, output

