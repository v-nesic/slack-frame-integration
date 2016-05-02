from django.core.urlresolvers import resolve
from django.core.urlresolvers import Resolver404
from django.core.urlresolvers import reverse
from django.test import Client
from django.test import TestCase
from slackcmd import SlackCmd
from slackcmd import SlackCmdFrame

import hello.views

class SlackCmdTest(TestCase):
    url_template = '/slack/{0}/slash-cmd'
    test_url = url_template.format('test.username')
    cmd_template = {
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

    def getSlackCmdPath(self, username):
        return reverse('slack-slash-cmd', args=[username])

    def getSlackCmdContext(self, text='', use_fields=cmd_template.keys(), omit_fields=[]):
        context = dict()
        for key in use_fields:
            if key not in omit_fields:
                context[key] = self.cmd_template[key] if key != 'text' else text
        return context

    def testPathResolvesToSlackcmdWithUsernameArg(self):
        valid_usernames = ['abcd12', 'ab-cd-12', '_ab_cd_12', 'ab.cd.12']
        for username in valid_usernames:
            found = resolve(self.url_template.format(username))
            self.assertEqual(found.func, hello.views.slackSlashCmdRequest)
            self.assertEqual(found.args[0], username, 'Parsed username doesn\'t match expected value {0}'.format(username))

    def testPathResolvesToErrorForInvalidUsername(self):
        invalid_usernames = ['abcd?', '-abc', '.abc', '0abc', 'ab cd' ]
        for username in invalid_usernames:
            try:
                found = resolve(self.url_template.format(username))
                self.assertTrue(found is None, 'Invalid username {0} accepted'.format(username))
            except Resolver404:
                pass

    def testPostNoArgsV1(self):
        response = Client().get(self.test_url)
        self.assertEqual(400, response.status_code)

    def testPostNoArgsV2(self):
        response = Client().post(self.test_url, {})
        self.assertEqual(400, response.status_code)

    def testPostWithMissingArgs(self):
        for arg in SlackCmd().slack_cmd_post_args:
            response = Client().post(self.test_url, self.getSlackCmdContext('text', omit_fields=arg))
            self.assertEqual(400, response.status_code, 'Unexpected status code ({0} instead of 400) when missing {1} arg'.format(response.status_code, arg))

    def testUnsupportedCmd(self):
        context = self.getSlackCmdContext()
        context['command'] = 'frame' # Mandatory slash (/) missing at the beginning
        response = Client().post(self.test_url, context)
        self.assertEqual(400, response.status_code)

    def testUnknownUsername(self):
        response = Client().post(self.getSlackCmdPath('ABCDABCDABCDABCDABCDABCD'), self.getSlackCmdContext())
        self.assertEqual(403, response.status_code, '{0} {1}'.format(response.status_code, response.content))

    def testWrongToken(self):
        context = self.getSlackCmdContext()
        context['token'] = 'ABCDABCDABCDABCDABCDABCD'
        response = Client().post(self.getSlackCmdPath('ABCDABCDABCDABCDABCDABCD'), context)
        response = Client().post(self.test_url, context)
        self.assertEqual(403, response.status_code, '{0} {1}'.format(response.status_code, response.content))

    def testFrameCdmHelp(self):
        response = Client().post(self.test_url, self.getSlackCmdContext('help'))
        self.assertEqual(200, response.status_code, str(response.status_code) + response.content)
        self.assertEqual('text/', response['Content-Type'][:5])