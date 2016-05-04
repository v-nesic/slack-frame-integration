import json
from urlparse import urlparse
import urllib2

from mock import patch, Mock
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, resolve, Resolver404
from django.test import Client, TestCase

import slacktoframe.views

from crypto import FrameCypher
from slackcmd import SlackCmdFrame
from usersettings import UserSettings


class SlackCmdTest(TestCase):
    test_username = 'test.username'
    test_user_settings = {
        'token': 'test.token',
        'mapping': {
            'text': 'text_mapping',
            'image': 'image_mapping'
        }
    }
    test_url_template = '/slack/{}/slash-cmd'
    test_url = reverse('slack-slash-cmd', args=[test_username])
    test_command = {
        'token': 'test.token',
        'team_id': 'T10V1PSR4',
        'team_domain': 'neske-pilot-project',
        'channel_id': 'C2147483705',
        'channel_name': 'test',
        'user_id': 'U2147483697',
        'user_name': 'v.nesic',
        'command': '/frame',
        'text': '',
        'response_url': 'https://localhost:5000/slackcmdresponse'
    }
    test_txt_url = 'http://www.google.com'
    test_img_url = 'https://www.google.rs/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'
    test_no_scheme_url = 'google.com'

    @staticmethod
    def get_slack_cmd_url(username):
        return reverse('slack-slash-cmd', args=[username])

    @classmethod
    def get_slack_cmd_context(cls, text='', use_fields=test_command.keys(), omit_fields=None):
        if omit_fields is None:
            omit_fields = []
        context = dict()
        for key in use_fields:
            if key not in omit_fields:
                context[key] = cls.test_command[key] if key != 'text' else text
        return context

    @classmethod
    def setUpClass(cls):
        UserSettings.add(cls.test_username, cls.test_user_settings)

    @classmethod
    def tearDownClass(cls):
        UserSettings.delete(cls.test_username)

    def test_slack_cmd_path_resolves_to_slack_cmd_with_username_arg(self):
        valid_usernames = ['abcd12', 'ab-cd-12', '_ab_cd_12', 'ab.cd.12']

        for username in valid_usernames:
            found = resolve(self.test_url_template.format(username))

            self.assertEqual(found.func, slacktoframe.views.slack_slash_cmd_request)
            self.assertEqual(found.args[0], username,
                             'Parsed username does not match expected value {}'.format(username))

    def test_slack_cmd_path_resolves_to_error_for_invalid_username(self):
        invalid_usernames = ['abcd?', '-abc', '.abc', '0abc', 'ab cd']

        for username in invalid_usernames:
            try:
                found = resolve(self.test_url_template.format(username))
                self.assertTrue(found is None, 'Invalid username {} accepted'.format(username))
            except Resolver404:
                pass

    def test_post_no_args_v1(self):
        response = Client().get(self.test_url)
        self.assertEqual(400, response.status_code)

    def test_post_no_args_v2(self):
        response = Client().post(self.test_url, {})
        self.assertEqual(400, response.status_code)

    def test_post_with_missing_args(self):
        for arg in self.test_command.keys():
            response = Client().post(self.test_url, self.get_slack_cmd_context('text', omit_fields=[arg]))
            self.assertEqual(400, response.status_code,
                             'Unexpected status code ({} instead of 400) when missing {} arg'.format(
                                 response.status_code, arg
                             ))

    def test_unsupported_cmd(self):
        context = self.get_slack_cmd_context()
        context['command'] = 'frame'  # Mandatory slash (/) missing at the beginning

        response = Client().post(self.test_url, context)
        self.assertEqual(400, response.status_code)

    def test_unknown_username(self):
        response = Client().post(SlackCmdTest.get_slack_cmd_url('ABCDABCDABCDABCDABCDABCD'),
                                 self.get_slack_cmd_context())
        self.assertEqual(403, response.status_code, '{} {}'.format(response.status_code, response.content))

    def test_wrong_token(self):
        context = self.get_slack_cmd_context()
        context['token'] = 'ABCDABCDABCDABCDABCDABCD'

        response = Client().post(self.test_url, context)
        self.assertEqual(403, response.status_code, '{} {}'.format(response.status_code, response.content))

    def test_frame_cdm_help(self):
        response = Client().post(self.test_url, self.get_slack_cmd_context('help'))

        self.assertEqual(200, response.status_code, str(response.status_code) + response.content)
        self.assertEqual('application/json', response['Content-Type'])
        self.assertEqual(json.loads(response.content)['text'], SlackCmdFrame.help_response_text)

    @patch('urllib2.urlopen')
    def test_frame_cmd_with_text_file(self, urlopen_mock):
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response_info = Mock()
        mock_response_info.getheader.return_value = 'text/html'
        mock_response.info.return_value = mock_response_info
        urlopen_mock.return_value = mock_response

        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_txt_url))
        self.assertTrue(urlopen_mock.has_been_called())  # Detect breaking changes in implementation
        self.assertEqual(200, response.status_code, '{} {}'.format(response.status_code, response.content))

        found = resolve(urlparse(json.loads(response.content)['text']).path)
        self.assertEqual(found.func, slacktoframe.views.frame_instance_request)
        self.assertEqual(FrameCypher().decrypt(found.args[0]), ('text_mapping', self.test_txt_url))

    @patch('urllib2.urlopen')
    def test_frame_cmd_with_image_file(self, urlopen_mock):
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response_info = Mock()
        mock_response_info.getheader.return_value = 'image/png'
        mock_response.info.return_value = mock_response_info
        urlopen_mock.return_value = mock_response

        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_img_url))
        self.assertTrue(urlopen_mock.has_been_called())  # Detect breaking changes in implementation
        self.assertEqual(200, response.status_code, '{} {}'.format(response.status_code, response.content))

        found = resolve(urlparse(json.loads(response.content)['text']).path)
        self.assertEqual(found.func, slacktoframe.views.frame_instance_request)
        self.assertEqual(FrameCypher().decrypt(found.args[0]), ('image_mapping', self.test_img_url))

    @patch('urllib2.urlopen')
    def test_frame_cmd_with_url_without_scheme(self, urlopen_mock):
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response_info = Mock()
        mock_response_info.getheader.return_value = 'text/html'
        mock_response.info.return_value = mock_response_info
        urlopen_mock.return_value = mock_response

        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_no_scheme_url))
        self.assertTrue(urlopen_mock.has_been_called())  # Detect breaking changes in implementation
        self.assertEqual(200, response.status_code, '{} {}'.format(response.status_code, response.content))

        found = resolve(urlparse(json.loads(response.content)['text']).path)
        self.assertEqual(found.func, slacktoframe.views.frame_instance_request)
        self.assertEqual(FrameCypher().decrypt(found.args[0]), ('text_mapping', 'http://' + self.test_no_scheme_url))

    @patch('urllib2.urlopen')
    def test_frame_cmd_with_unsupported_file_type(self, urlopen_mock):
        mock_response = Mock()
        mock_response.getcode.return_value = 200
        mock_response_info = Mock()
        mock_response_info.getheader.return_value = 'application/json'
        mock_response.info.return_value = mock_response_info
        urlopen_mock.return_value = mock_response

        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_txt_url))

        self.assertTrue(urlopen_mock.has_been_called())  # Detect breaking changes in implementation
        self.assertEqual(400, response.status_code, '{} {}'.format(response.status_code, response.content))

    @patch('django.core.validators.URLValidator.__call__')
    def test_frame_cmd_invalid_url_format(self, url_validator_mock):
        url_validator_mock.side_effect = ValidationError('')

        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_txt_url))

        self.assertEqual(400, response.status_code, '{} {}'.format(response.status_code, response.content))
        url_validator_mock.assert_called_with(self.test_txt_url)  # Detect breaking changes in implementation

    @patch('urllib2.urlopen')
    def test_frame_cmd_unreachable_file_url(self, urlopen_mock):
        urlopen_mock.side_effect = urllib2.HTTPError(self.test_txt_url, 400, '', '', None)

        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_txt_url))

        self.assertEqual(400, response.status_code, '{} {}'.format(response.status_code, response.content))
        self.assertTrue(urlopen_mock.has_been_called())  # Detect breaking changes in implementation

    @patch('urllib2.urlopen')
    def test_frame_cmd_file_url_status_not_200(self, urlopen_mock):
        mock_response = Mock()
        mock_response.getcode.return_value = 404
        urlopen_mock.return_value = mock_response

        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_txt_url))

        self.assertEqual(400, response.status_code, '{} {}'.format(response.status_code, response.content))
        self.assertTrue(urlopen_mock.has_been_called())  # Detect breaking changes in implementation

    def disabled_test_frame_cmd_with_text_file_unmocked(self):
        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_txt_url))
        self.assertEqual(200, response.status_code, '{} {}'.format(response.status_code, response.content))

        found = resolve(urlparse(json.loads(response.content)['text']).path)
        self.assertEqual(found.func, slacktoframe.views.frame_instance_request)
        self.assertEqual(FrameCypher().decrypt(found.args[0]), ('text_mapping', self.test_txt_url))

    def disabled_test_frame_cmd_with_image_file_unmocked(self):
        response = Client().post(self.test_url, self.get_slack_cmd_context(self.test_img_url))
        self.assertEqual(200, response.status_code, '{} {}'.format(response.status_code, response.content))

        found = resolve(urlparse(json.loads(response.content)['text']).path)
        self.assertEqual(found.func, slacktoframe.views.frame_instance_request)
        self.assertEqual(FrameCypher().decrypt(found.args[0]), ('image_mapping', self.test_img_url))
