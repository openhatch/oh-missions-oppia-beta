# coding: utf-8
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

"""Models for Oppia statistics."""

__author__ = 'Sean Lip'

from google.appengine.ext import ndb

from utils import Enum


STATS_ENUMS = Enum('exploration_visited')


class EventHandler(object):
    """Records events."""

    @classmethod
    def record_event(cls, event_name, entity_id):
        """Updates statistics based on recorded events."""

        if event_name == STATS_ENUMS.exploration_visited:
            event_key = 'e.%s' % entity_id
            cls._inc(event_key)

    @classmethod
    def _inc(cls, event_key):
        """Increments the counter corresponding to an event key."""
        counter = Counter.get_or_insert(event_key, name=event_key)
        if not counter:
            counter = Counter(id=event_key, name=event_key)
        counter.value += 1
        counter.put()


class Counter(ndb.Model):
    """An integer-valued counter."""
    # The name of the property.
    name = ndb.StringProperty()
    # The value of the property.
    value = ndb.IntegerProperty(default=0)


class Statistics(object):
    """Retrieves statistics to display in the views."""

    @classmethod
    def get_stats(cls, event_name, entity_id):
        """Retrieves statistics for the given event name and entity id."""

        if event_name == STATS_ENUMS.exploration_visited:
            event_key = 'e.%s' % entity_id
            counter = Counter.get_by_id(event_key)
            if not counter:
                return 0
            return counter.value