from django.core.urlresolvers import reverse, resolve, Resolver404
from django.test import Client, TestCase

import hello.views

from slackcmd import UserSettings as TestSettings


class FrameInstanceTest(TestCase):
    test_username = 'test.username'
    test_user_settings = {
        'token': 'test.token',
        'mapping': {
            'text': 'text_mapping',
            'image': 'image_mapping'
        }
    }
    test_url_template = '/frame/instance/{}/'

    @classmethod
    def setUpClass(cls):
        TestSettings.add(cls.test_username, cls.test_user_settings)

    @classmethod
    def tearDownClass(cls):
        TestSettings.delete(cls.test_username)

    def test_frame_instance_path_resolves_to_frame_instance_with_token_arg(self):
        valid_chars_token = 'abcdefghijklmopqrstuvwxyzABCDEFGHIJKLMNOPQURSTUVWXYZ0123456789_-'

        found = resolve(self.test_url_template.format(valid_chars_token))

        self.assertEqual(found.func, hello.views.frame_instance_request)
        self.assertEqual(found.args[0], valid_chars_token,
                         'Parsed token does not match expected value {}'.format(valid_chars_token))

    def test_frame_instance_path_resolves_to_error_for_invalid_token(self):
        valid_chars_tokens = ['a?', '.abc', 'abc!', '0+abc', 'ab cd']

        for token in valid_chars_tokens:
            try:
                found = resolve(self.test_url_template.format(token))
                self.assertTrue(found is None, 'Invalid token {} accepted'.format(token))
            except Resolver404:
                pass
