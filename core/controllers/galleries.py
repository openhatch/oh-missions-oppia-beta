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

"""Controllers for the gallery pages."""

__author__ = 'sll@google.com (Sean Lip)'

import collections

from core.controllers import base
from core.domain import config_domain
from core.domain import exp_domain
from core.domain import exp_services
from core.domain import rights_manager
from core.domain import widget_registry
from core.platform import models
current_user_services = models.Registry.import_current_user_services()
import feconf

import jinja2


EXPLORATION_ID_KEY = 'explorationId'

ALLOW_YAML_FILE_UPLOAD = config_domain.ConfigProperty(
    'allow_yaml_file_upload', 'Boolean',
    'Whether to allow file uploads via YAML in the gallery page.',
    default_value=False)

CONTRIBUTE_GALLERY_PAGE_ANNOUNCEMENT = config_domain.ConfigProperty(
    'contribute_gallery_page_announcement', 'Html',
    'An announcement to display on top of the contribute gallery page.',
    default_value='')


class LearnPage(base.BaseHandler):
    """The exploration gallery page for learners."""

    def get(self):
        """Handles GET requests."""
        self.values.update({
            'nav_mode': feconf.NAV_MODE_LEARN,
            'contribute_gallery_login_url': (
                current_user_services.create_login_url(
                    feconf.CONTRIBUTE_GALLERY_URL))
        })
        self.render_template('galleries/learn.html')


class LearnHandler(base.BaseHandler):
    """Provides data for the exploration gallery page for learners."""

    def get(self):
        """Handles GET requests."""
        # TODO(sll): Implement paging.
        explorations_dict = (
            exp_services.get_non_private_explorations_summary_dict())

        categories = collections.defaultdict(list)
        for (eid, exploration_data) in explorations_dict.iteritems():
            categories[exploration_data['category']].append({
                'id': eid,
                'is_public': (
                    exploration_data['rights']['status'] ==
                    rights_manager.EXPLORATION_STATUS_PUBLIC),
                'is_publicized': (
                    exploration_data['rights']['status'] ==
                    rights_manager.EXPLORATION_STATUS_PUBLICIZED),
                'title': exploration_data['title'],
                'to_playtest': False,
            })

        if self.user_id:
            playtest_dict = (
                exp_services.get_explicit_viewer_explorations_summary_dict(
                    self.user_id))
            for (eid, exploration_data) in playtest_dict.iteritems():
                categories[exploration_data['category']].append({
                    'id': eid,
                    'is_public': (
                        exploration_data['rights']['status'] ==
                        rights_manager.EXPLORATION_STATUS_PUBLIC),
                    'is_publicized': (
                        exploration_data['rights']['status'] ==
                        rights_manager.EXPLORATION_STATUS_PUBLICIZED),
                    'title': exploration_data['title'],
                    'to_playtest': True,
                })

        self.values.update({
            'categories': categories,
        })
        self.render_json(self.values)


class ContributePage(base.BaseHandler):
    """The exploration gallery page for contributors."""

    PAGE_NAME_FOR_CSRF = 'contribute'

    @base.require_registered_as_editor
    def get(self):
        """Handles GET requests."""
        widget_js_directives = (
            widget_registry.Registry.get_noninteractive_widget_js())

        self.values.update({
            'nav_mode': feconf.NAV_MODE_CONTRIBUTE,
            'allow_yaml_file_upload': ALLOW_YAML_FILE_UPLOAD.value,
            'announcement': jinja2.utils.Markup(
                CONTRIBUTE_GALLERY_PAGE_ANNOUNCEMENT.value),
            'widget_js_directives': jinja2.utils.Markup(widget_js_directives),
        })
        self.render_template('galleries/contribute.html')


class ContributeHandler(base.BaseHandler):
    """Provides data for the exploration gallery page for contributors."""

    @base.require_registered_as_editor
    def get(self):
        """Handles GET requests."""
        # TODO(sll): Implement paging.

        explorations_dict = (
            exp_services.get_editable_explorations_summary_dict(
                self.user_id))
        if (rights_manager.Actor(self.user_id).is_moderator() or
                self.is_super_admin):
            explorations_dict.update(
                exp_services.get_non_private_explorations_summary_dict())

        categories = collections.defaultdict(list)
        for (eid, exploration_data) in explorations_dict.iteritems():
            categories[exploration_data['category']].append({
                'id': eid,
                'title': exploration_data['title'],
                'can_clone': (
                    rights_manager.Actor(self.user_id).can_clone(eid) or
                    self.is_super_admin),
                'can_edit': (
                    rights_manager.Actor(self.user_id).can_edit(eid) or
                    self.is_super_admin),
                'is_private': (
                    exploration_data['rights']['status'] ==
                    rights_manager.EXPLORATION_STATUS_PRIVATE),
                'is_public': (
                    exploration_data['rights']['status'] ==
                    rights_manager.EXPLORATION_STATUS_PUBLIC),
                'is_publicized': (
                    exploration_data['rights']['status'] ==
                    rights_manager.EXPLORATION_STATUS_PUBLICIZED),
                'is_cloned': bool(exploration_data['rights']['cloned_from']),
            })

        self.values.update({
            'categories': categories,
        })
        self.render_json(self.values)


class NewExploration(base.BaseHandler):
    """Creates a new exploration."""

    PAGE_NAME_FOR_CSRF = 'contribute'

    @base.require_registered_as_editor
    def post(self):
        """Handles POST requests."""
        title = self.payload.get('title')
        category = self.payload.get('category')

        if not title:
            raise self.InvalidInputException('No title supplied.')
        if not category:
            raise self.InvalidInputException('No category chosen.')

        new_exploration_id = exp_services.get_new_exploration_id()
        exploration = exp_domain.Exploration.create_default_exploration(
            new_exploration_id, title, category)
        exp_services.save_new_exploration(self.user_id, exploration)

        self.render_json({EXPLORATION_ID_KEY: new_exploration_id})


class UploadExploration(base.BaseHandler):
    """Uploads a new exploration."""

    PAGE_NAME_FOR_CSRF = 'contribute'

    @base.require_registered_as_editor
    def post(self):
        """Handles POST requests."""
        title = self.payload.get('title')
        category = self.payload.get('category')
        yaml_content = self.request.get('yaml_file')

        if not title:
            raise self.InvalidInputException('No title supplied.')
        if not category:
            raise self.InvalidInputException('No category chosen.')

        new_exploration_id = exp_services.get_new_exploration_id()
        if ALLOW_YAML_FILE_UPLOAD.value:
            exp_services.save_new_exploration_from_yaml_and_assets(
                self.user_id, yaml_content, title, category,
                new_exploration_id, [])
            self.render_json({EXPLORATION_ID_KEY: new_exploration_id})
        else:
            raise self.InvalidInputException(
                'This server does not allow file uploads.')


class CloneExploration(base.BaseHandler):
    """Clones an existing exploration."""

    PAGE_NAME_FOR_CSRF = 'contribute'

    @base.require_registered_as_editor
    def post(self):
        """Handles POST requests."""
        exploration_id = self.payload.get('exploration_id')

        if not rights_manager.Actor(self.user_id).can_clone(
                exploration_id):
            raise Exception('You cannot copy this exploration.')

        self.render_json({
            EXPLORATION_ID_KEY: exp_services.clone_exploration(
                self.user_id, exploration_id)
        })


class RecentCommitsHandler(base.BaseHandler):
    """Returns a list of recent commits."""

    def get(self):
        """Handles GET requests."""
        urlsafe_start_cursor = self.request.get('cursor')
        all_commits, new_urlsafe_start_cursor, more = (
            exp_services.get_next_page_of_all_non_private_commits(
                urlsafe_start_cursor=urlsafe_start_cursor))
        all_commit_dicts = [commit.to_dict() for commit in all_commits]
        self.render_json({
            'results': all_commit_dicts,
            'cursor': new_urlsafe_start_cursor,
            'more': more,
        })
