from django.core.urlresolvers import resolve
from django.test import Client
from django.test import TestCase
from .views import slackcmd
from .slackcmd import slack_cmd_post_args

slackcmdtemplates = [
    {
        'token': 'Cb7u0tsogeepryhYkMZwElC5',
        'team_id': 'neske-pilot-project',
        'team_domain': 'https://neske-pilot-project.slack.com',
        'channel_id': 'C2147483705',
        'channel_name': 'test',
        'user_id': 'U2147483697',
        'user_name': 'v.nesic',
        'command': '/frame',
        'text': '',
        'response_url': 'https://localhost:5000/slackcmdresponse'
    }
]


def get_slack_cmd_context(text='', template_no=0, use_fields=None, omit_fields=None):
    context = dict()
    if use_fields == None:
        use_fields = []
        for key in slackcmdtemplates[template_no]:
            use_fields.append(key)
    for key in use_fields:
        if omit_fields is None or key not in omit_fields:
            context[key] = slackcmdtemplates[template_no][key] if key != 'text' else text
    return context


class SlackCmdTest(TestCase):
    slack_cmd_frame_url = '/slack/cmd/frame/'

    def test_slack_cmd_frame_resloves_to_slackcmd_with_arg_frame(self):
        found = resolve(self.slack_cmd_frame_url)
        self.assertEqual(found.func, slackcmd)
        self.assertEqual(found.args[0], '/frame')

    def test_slack_cmd_frame_with_no_args(self):
        response = Client().get(self.slack_cmd_frame_url)
        self.assertEqual(400, response.status_code)
        response = Client().post(self.slack_cmd_frame_url, {})
        self.assertEqual(400, response.status_code)

    def test_slack_cmd_frame_post_with_missing_args(self):
        for arg in slack_cmd_post_args:
            response = Client().post(self.slack_cmd_frame_url, get_slack_cmd_context('text', omit_fields=arg))
            self.assertEqual(400, response.status_code, 'Unexpected status code ({0} instead of 400) when missing {1} arg'.format(response.status_code, arg))

    def test_slack_cmd_frame_with_wrong_cmd_arg(self):
        context = get_slack_cmd_context()
        context['command'] = 'frame' # Mandatory slash (/) missing at the beginning
        response = Client().post(self.slack_cmd_frame_url, context)
        self.assertEqual(400, response.status_code)

    def test_slack_cmd_frame_with_wrong_teamid(self):
        context = get_slack_cmd_context()
        context['team_id'] = 'ABCDABCDABCDABCDABCDABCD'
        response = Client().post(self.slack_cmd_frame_url, context)
        self.assertEqual(403, response.status_code, response.content)

    def test_slack_cmd_frame_with_wrong_token(self):
        context = get_slack_cmd_context()
        context['token'] = 'ABCDABCDABCDABCDABCDABCD'
        response = Client().post(self.slack_cmd_frame_url, context)
        self.assertEqual(403, response.status_code, response.content)

    def test_slack_cmd_frame_help(self):
        response = Client().post(self.slack_cmd_frame_url, get_slack_cmd_context('help'))
        self.assertEqual(200, response.status_code)