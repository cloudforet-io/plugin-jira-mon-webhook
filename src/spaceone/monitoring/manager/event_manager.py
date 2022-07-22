import logging
import datetime
from spaceone.core.manager import BaseManager
from spaceone.core.utils import random_string
from spaceone.monitoring.model.event_response_model import EventModel
from spaceone.monitoring.error.event import *

_LOGGER = logging.getLogger(__name__)
DEFAULT_TITLE = 'Issue Notification'


class EventManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, options, data):
        """ data sample
            "event": {}
        """
        try:
            _LOGGER.debug("-----")
            _LOGGER.debug(data)
            _LOGGER.debug("-----")

            issue = data.get('issue', {})
            issue_fields = issue.get('fields', {})
            user = data.get('user', {})

            event_dict = {
                'event_key': self._generate_event_key(issue),
                'event_type': self._set_event_type(),
                'severity': self._set_severity(),
                'resource': {},
                'title': self._set_title(issue_fields),
                'description': self._set_description(issue_fields),
                'rule': '',
                'additional_info': self._set_additional_info(issue, user)
            }

            if occurred_at := self._set_occurred_at(data):
                event_dict.update({'occurred_at': occurred_at})

            event_model = EventModel(event_dict, strict=False)
            event_model.validate()
            return [event_model.to_native()]

        except Exception as e:
            raise ERROR_EVENT_PARSE()

    @staticmethod
    def _generate_event_key(issue):
        if self := issue.get('self'):
            return self
        else:
            return random_string()

    @staticmethod
    def _set_severity():
        return 'INFO'

    @staticmethod
    def _set_event_type():
        return 'ALERT'

    @staticmethod
    def _set_title(issue_fields):
        return f'[Jira] {issue_fields.get("summary", DEFAULT_TITLE)}'

    @staticmethod
    def _set_description(issue_fields):
        return issue_fields.get('description', '')

    @staticmethod
    def _set_occurred_at(data):
        occurred_at = None

        if timestamp := data.get('timestamp'):
            occurred_at = datetime.datetime.fromtimestamp(timestamp/1000)

        return occurred_at

    @staticmethod
    def _set_additional_info(issue, user):
        issue_fields = issue.get('fields', {})

        info = {}

        info.update({'Issue ID': issue.get('id')})
        info.update({'Ticket Key': issue.get('key')})

        if priority := issue_fields.get('priority', {}).get('name'):
            info.update({'priority': priority})

        if project_key := issue_fields.get('project', {}).get('key'):
            info.update({'project_key': project_key})

        if project_name := issue_fields.get('project', {}).get('name'):
            info.update({'project_name': project_name})

        creator_name = issue_fields.get('creator', {}).get('name')
        creator_display_name = issue_fields.get('creator', {}).get('displayName')

        if creator_display_name:
            info.update({'Creator Name': creator_display_name})
        elif creator_name:
            info.update({'Creator Name': creator_name})

        if creator_email := issue_fields.get('creator', {}).get('emailAddress'):
            info.update({'Creator Email': creator_email})

        return info
