# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import unittest
import webtest

from core.domain import config_domain
from core.platform import models
(base_models, exp_models, file_models, stats_models, user_models) = (
    models.Registry.import_models([
        models.NAMES.base_model,
        models.NAMES.exploration, models.NAMES.file, models.NAMES.statistics,
        models.NAMES.user
    ])
)
current_user_services = models.Registry.import_current_user_services()
import feconf
import main

import json


CSRF_REGEX = (
    r'csrf_token: JSON\.parse\(\'\\\"([A-Za-z0-9/=_-]+)\\\"\'\)')


def empty_environ():
    os.environ['AUTH_DOMAIN'] = 'example.com'
    os.environ['SERVER_NAME'] = 'localhost'
    os.environ['HTTP_HOST'] = 'localhost'
    os.environ['SERVER_PORT'] = '8080'
    os.environ['USER_EMAIL'] = ''
    os.environ['USER_ID'] = ''
    os.environ['USER_IS_ADMIN'] = '0'


class TestTags(object):
    """Tags for labelling particular tests."""

    # Tag that is used to flag tests which take a long time to run, so that
    # they can be excluded via a command-line argument.
    SLOW_TEST = 1


class TestBase(unittest.TestCase):
    """Base class for all tests."""

    maxDiff = 2500

    TAGS = []

    DEFAULT_USERNAME = 'defaultusername'

    def _delete_all_models(self):
        versioned_model_classes = frozenset([
            exp_models.ExplorationModel,
            exp_models.ExplorationRightsModel,
            file_models.FileMetadataModel,
            file_models.FileModel,
        ])

        unversioned_model_classes = frozenset([
            exp_models.ExplorationSnapshotMetadataModel,
            exp_models.ExplorationSnapshotContentModel,
            exp_models.ExplorationRightsSnapshotMetadataModel,
            exp_models.ExplorationRightsSnapshotContentModel,
            file_models.FileMetadataSnapshotMetadataModel,
            file_models.FileMetadataSnapshotContentModel,
            file_models.FileSnapshotMetadataModel,
            file_models.FileSnapshotContentModel,
            stats_models.StateCounterModel,
            stats_models.StateRuleAnswerLogModel,
            stats_models.FeedbackItemModel,
            user_models.UserSettingsModel,
        ])

        for clazz in versioned_model_classes:
            for entity in clazz.get_all(include_deleted_entities=True):
                entity.delete(
                    feconf.ADMIN_COMMITTER_ID, '', force_deletion=True)

        for clazz in unversioned_model_classes:
            for entity in clazz.get_all(include_deleted_entities=True):
                entity.delete()

    def setUp(self):
        self.testapp = webtest.TestApp(main.app)

    def tearDown(self):  # pylint: disable-msg=g-bad-name
        self._delete_all_models()

    def shortDescription(self):
        """Additional information logged during unit test invocation."""
        # Suppress default logging of docstrings.
        return None

    def get_expected_login_url(self, slug):
        """Returns the expected login URL."""
        return current_user_services.create_login_url(slug)

    def get_expected_logout_url(self, slug):
        """Returns the expected logout URL."""
        return current_user_services.create_logout_url(slug)

    def _parse_json_response(self, json_response, expect_errors=False):
        """Convert a JSON server response to an object (such as a dict)."""
        if not expect_errors:
            self.assertEqual(json_response.status_int, 200)

        self.assertEqual(
            json_response.content_type, 'application/javascript')
        self.assertTrue(json_response.body.startswith(feconf.XSSI_PREFIX))

        return json.loads(json_response.body[len(feconf.XSSI_PREFIX):])

    def get_json(self, url):
        """Get a JSON response, transformed to a Python object."""
        json_response = self.testapp.get(url)
        self.assertEqual(json_response.status_int, 200)
        return self._parse_json_response(json_response, expect_errors=False)

    def post_json(self, url, payload, csrf_token=None, expect_errors=False,
                  expected_status_int=200, upload_files=None):
        """Post an object to the server by JSON; return the received object."""
        data = {'payload': json.dumps(payload)}
        if csrf_token:
            data['csrf_token'] = csrf_token

        json_response = self.testapp.post(
            str(url), data, expect_errors=expect_errors,
            upload_files=upload_files)

        self.assertEqual(json_response.status_int, expected_status_int)
        return self._parse_json_response(
            json_response, expect_errors=expect_errors)

    def put_json(self, url, payload, csrf_token=None, expect_errors=False,
                 expected_status_int=200):
        """Put an object to the server by JSON; return the received object."""
        data = {'payload': json.dumps(payload)}
        if csrf_token:
            data['csrf_token'] = csrf_token

        json_response = self.testapp.put(
            str(url), data, expect_errors=expect_errors)

        self.assertEqual(json_response.status_int, expected_status_int)
        return self._parse_json_response(
            json_response, expect_errors=expect_errors)

    def get_csrf_token_from_response(self, response):
        """Retrieve the CSRF token from a GET response."""
        return re.search(CSRF_REGEX, response.body).group(1)

    def register_editor(self, email, username=None):
        """Register a user with the given username as an editor."""
        if username is None:
            username = self.DEFAULT_USERNAME

        self.login(email)

        response = self.testapp.get(feconf.EDITOR_PREREQUISITES_URL)
        csrf_token = self.get_csrf_token_from_response(response)

        response = self.testapp.post(feconf.EDITOR_PREREQUISITES_DATA_URL, {
            'csrf_token': csrf_token,
            'payload': json.dumps({
                'username': username,
                'agreed_to_terms': True
            })
        })
        self.assertEqual(response.status_int, 200)

        self.logout()

    def set_admins(self, admin_emails):
        """Set the ADMIN_EMAILS property."""
        self.login('superadmin@example.com', is_super_admin=True)
        response = self.testapp.get('/admin')
        csrf_token = self.get_csrf_token_from_response(response)
        self.post_json('/adminhandler', {
            'action': 'save_config_properties',
            'new_config_property_values': {
                config_domain.ADMIN_EMAILS.name: admin_emails,
            }
        }, csrf_token)
        self.logout()

    def set_moderators(self, moderator_emails):
        """Set the MODERATOR_EMAILS property."""
        self.login('superadmin@example.com', is_super_admin=True)
        response = self.testapp.get('/admin')
        csrf_token = self.get_csrf_token_from_response(response)
        self.post_json('/adminhandler', {
            'action': 'save_config_properties',
            'new_config_property_values': {
                config_domain.MODERATOR_EMAILS.name: moderator_emails,
            }
        }, csrf_token)
        self.logout()

    def get_current_logged_in_user_id(self):
        return os.environ['USER_ID']

    def get_user_id_from_email(self, email):
        return current_user_services.get_user_id_from_email(email)


class AppEngineTestBase(TestBase):
    """Base class for tests requiring App Engine services."""

    def login(self, email, is_super_admin=False):
        os.environ['USER_EMAIL'] = email
        os.environ['USER_ID'] = self.get_user_id_from_email(email)
        os.environ['USER_IS_ADMIN'] = '1' if is_super_admin else '0'

    def logout(self):
        # TODO(sll): Move this to the tearDown() method of the generic test
        # base?
        os.environ['USER_EMAIL'] = ''
        os.environ['USER_ID'] = ''
        del os.environ['USER_IS_ADMIN']

    def setUp(self):  # pylint: disable-msg=g-bad-name
        empty_environ()

        from google.appengine.datastore import datastore_stub_util
        from google.appengine.ext import testbed

        self.testbed = testbed.Testbed()
        self.testbed.activate()

        # Configure datastore policy to emulate instantaneously and globally
        # consistent HRD; we also patch dev_appserver in main.py to run under
        # the same policy.
        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=1)

        # Declare any relevant App Engine service stubs here.
        self.testbed.init_user_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub(consistency_policy=policy)
        self.testbed.init_taskqueue_stub()
        self.taskq = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

        # Set up the app to be tested.
        self.testapp = webtest.TestApp(main.app)

    def tearDown(self):  # pylint: disable-msg=g-bad-name
        os.environ['USER_IS_ADMIN'] = '0'
        self.testbed.deactivate()


if feconf.PLATFORM == 'gae':
    GenericTestBase = AppEngineTestBase
else:
    raise Exception('Invalid platform: expected one of [\'gae\']')
