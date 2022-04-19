import sys
sys.path.append('../')

import unittest
from unittest import mock
import datetime
from waterlinked_log_create_gpx_win_dommie_k import log_file_name, get_data

class TestWaterlinkLogCreate(unittest.TestCase):

    # This method will be used by the mock to replace requests.get
    def mocked_requests_get(url):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

        if url == 'https://someurl.com/api/v1/position/acoustic/filtered':
            return MockResponse({"key1": "value1"}, 200)
        elif url == 'https://someurl.com/api/v1/position/global':
            return MockResponse({"key2": "value2"}, 200)

    # This method will be used by the mock to replace requests.get
    def mocked_requests_get_error(url):
        class MockResponse:
            def __init__(self, json_data, status_code, text):
                self.json_data = json_data
                self.status_code = status_code
                self.text = text

            def json(self):
                return self.json_data

        if url == 'https://someurl.com/api/v1/position/acoustic/filtered':
            return MockResponse('', 404, "there was an error !")
        elif url == 'https://someurl.com/api/v1/position/global':
            return MockResponse('', 404,  "there was an error !")

    def test_log_file_name(self):
        extension = '.csv'
        time_now = datetime.datetime(2022,2,11,12,0,0,0)
        result = log_file_name(extension,time_now)
        self.assertEqual(result, '20220211-120000.csv')

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_get_data(self, mock_get):
        # Assert requests.get calls
        json_data = get_data('https://someurl.com/api/v1/position/acoustic/filtered')
        self.assertEqual(json_data, {"key1": "value1"})

    @mock.patch('requests.get', side_effect=mocked_requests_get_error)
    def test_get_data(self, mock_get):
        # Assert requests.get calls
        json_data = get_data('https://someurl.com/api/v1/position/acoustic/filtered')
        self.assertEqual(json_data, None)


if __name__ == '__main__':
    unittest.main() 