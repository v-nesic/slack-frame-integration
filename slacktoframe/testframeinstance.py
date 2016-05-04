import json

from django.core.urlresolvers import reverse, resolve, Resolver404
from django.test import Client, TestCase

import slacktoframe.views

from crypto import FrameCypher
from slackcmd import UserSettings as TestSettings


class FrameInstanceTest(TestCase):
    test_url_template = '/frame/instance/{}/'
    test_txt_url = 'http://www.google.com'
    test_img_url = 'https://www.google.rs/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'
    test_app_id = 'abcdef'
    test_pool_id = 123456

    @classmethod
    def get_frame_instance_path(cls, token):
        return reverse('frame-instance', args=[token])

    def test_frame_instance_path_resolves_to_frame_instance_with_token_arg(self):
        valid_chars_token = 'abcdefghijklmopqrstuvwxyzABCDEFGHIJKLMNOPQURSTUVWXYZ0123456789_-'

        found = resolve(self.test_url_template.format(valid_chars_token))

        self.assertEqual(found.func, slacktoframe.views.frame_instance_request)
        self.assertEqual(found.args[0], valid_chars_token,
                         'Parsed token does not match expected value {}'.format(valid_chars_token))

    def test_frame_instance_path_resolves_to_error_for_invalid_token_with_invalid_char(self):
        valid_chars_tokens = ['a?', '.abc', 'abc!', '0+ab', 'ab c']

        for token in valid_chars_tokens:
            try:
                found = resolve(self.test_url_template.format(token))
                self.assertTrue(found is None, 'Invalid token {} accepted'.format(token))
            except Resolver404:
                pass

    def test_invalid_length_token(self):
        short_tokens = ['a', 'abcde', 'abcdefghj']
        for token in short_tokens:
            response = Client().get(FrameInstanceTest.get_frame_instance_path(token))
            self.assertEqual(400, response.status_code, 'Short token {} accepted'.format(token))
            self.assertTemplateNotUsed(response, 'frame-instance.html')

    def test_too_short_token(self):
        short_tokens = ['ab', 'abc', 'abcd', 'abcdef', 'abcdefg']
        for token in short_tokens:
            response = Client().get(FrameInstanceTest.get_frame_instance_path(token))
            self.assertEqual(400, response.status_code, 'Short token {} accepted'.format(token))
            self.assertTemplateNotUsed(response, 'frame-instance.html')

    def test_invalid_token(self):
        token = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'
        response = Client().get(FrameInstanceTest.get_frame_instance_path(token))
        self.assertEqual(400, response.status_code, 'Invalid token {} accepted'.format(token))
        self.assertTemplateNotUsed(response, 'frame-instance.html')

    def test_valid_txt_url_token(self):
        data = FrameCypher().encrypt({
            'file_url': self.test_txt_url,
            'application_id': self.test_app_id,
            'pool_id': self.test_pool_id
        })

        response = Client().get(FrameInstanceTest.get_frame_instance_path(data))

        self.assertEqual(200, response.status_code, '{} {}'.format(response.status_code, response.content))
        self.assertTemplateUsed(response, 'frame-instance.html')
        self.assertContains(response, "hash: '{}',".format(self.test_app_id))
        self.assertContains(response, "fileName: '{}',".format(self.test_txt_url))
        self.assertContains(response, "poolId: {},".format(self.test_pool_id))
        self.assertNotContains(response, '// poolId: ID of a desired pool // optional')


    def test_valid_txt_url_token_without_pool_id(self):
        data = FrameCypher().encrypt({
            'file_url': self.test_txt_url,
            'application_id': self.test_app_id,
            'pool_id': None
        })

        response = Client().get(FrameInstanceTest.get_frame_instance_path(data))

        self.assertEqual(200, response.status_code, "{} {}".format(response.status_code, response.content))
        self.assertTemplateUsed(response, "frame-instance.html")
        self.assertContains(response, "hash: '{}',".format(self.test_app_id))
        self.assertContains(response, "fileName: '{}',".format(self.test_txt_url))
        self.assertContains(response, "// poolId: ID of a desired pool // optional")
        self.assertNotContains(response, "	poolId:")
        self.assertNotContains(response, "// ID of a desired pool // optional")
