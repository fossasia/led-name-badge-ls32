import sys
from array import array
from unittest.mock import patch

import abstract_write_method_test


class Test(abstract_write_method_test.AbstractWriteMethodTest):
    def test_get_methods(self):
        # Make the pyserial method deterministically not ready in this test,
        # independent of the test environment: 'serial' cannot be imported.
        with patch.dict('sys.modules', {'serial': None}):
            methods, output = self.call_info_methods()
        self.assertDictEqual({
            'hidapi': ('Program a device connected via USB using the pyhidapi package and libhidapi.', True),
            'libusb': ('Program a device connected via USB using the pyusb package and libusb.', True),
            'pyserial': ('Program a device with the open-source firmware, connected via USB, using the pyserial package.', False),
            'hidapi-custom': ('Program a badge with the custom protocol (vendorID 0x204c, productID 0x4359) connected via USB using the pyhidapi package and libhidapi.', True),
            'libusb-custom': ('Program a badge with the custom protocol (vendorID 0x204c, productID 0x4359) connected via USB using the pyusb package and libusb.', True)},
            methods)

    def test_get_device_ids(self):
        device_ids, output = self.call_info_ids('libusb')
        self.assertDictEqual({
            '3:4:2': 'LibUsb Test Manufacturer - LibUsb Test Product (bus=3 dev=4 endpoint=2)'},
            device_ids)

        device_ids, output = self.call_info_ids('hidapi')
        self.assertDictEqual({
            '3-4:5-6': 'HidApi Test Manufacturer - HidApi Test Product (if=0)'},
            device_ids)

        device_ids, output = self.call_info_ids('libusb-custom')
        self.assertDictEqual({
            '3:4:2': 'LibUsb Test Manufacturer - LibUsb Test Product (bus=3 dev=4 endpoint=2)'},
            device_ids)

        device_ids, output = self.call_info_ids('hidapi-custom')
        self.assertDictEqual({
            '3-4:5-6': 'HidApi Test Manufacturer - HidApi Test Product (if=0)'},
            device_ids)


    def test_write(self):
        device_ids, output, mocks = self.call_write('auto')
        mocks['pyhidapi'].hid_write.assert_called_once()

        device_ids, output, mocks = self.call_write('hidapi')
        mocks['pyhidapi'].hid_write.assert_called_once()

        device_ids, output, mocks = self.call_write('libusb')
        mocks['usb'].util.find_descriptor.assert_called_once()
        mocks['usb'].util.find_descriptor.return_value[0].write.assert_called_once()


    # -------------------------------------------------------------------------


    def call_info_methods(self):
        self.print_test_conditions(True, True, True, '-', '-')
        method_obj, output, _ = self.prepare_modules(True, True, True,
                                                     lambda m: m.get_available_methods())
        return method_obj, output

    def call_info_ids(self, method):
        self.print_test_conditions(True, True, True, '-', '-')
        method_obj, output, _ = self.prepare_modules(True, True, True,
                                                     lambda m: m.get_available_device_ids(method))
        return method_obj, output

    def call_write(self, method):
        self.print_test_conditions(True, True, True, 'auto', 'auto')
        return self.prepare_modules(True, True, True,
                                    lambda m: m.write(array('B', [1, 2, 3]), method))
