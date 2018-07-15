import sublime
import sublime_plugin

import json
from os.path import realpath
from threading import Lock

from ..lib import deferred, logger, requests


__all__ = ['EditorEventListener', 'EditorCompletionsListener']


def _is_view_supported(view):
    return view.file_name() is not None and view.file_name().endswith('.py')

def _check_view_size(view):
    return view.size() <= (1 << 20)


class EditorEventListener(sublime_plugin.EventListener):
    """Listener which forwards editor events to the event endpoint and also
    runs Sublime's `auto_complete` command when the buffer has been modified
    by a single character
    """

    _last_selection_region = None

    def on_modified(self, view):
        self._handle(view, 'edit')

    def on_selection_modified(self, view):
        self._handle(view, 'selection')

    @classmethod
    def _handle(cls, view, action):
        if not _is_view_supported(view):
            return

        deferred.defer(requests.kited_post, '/clientapi/editor/event',
                       data=cls._event_data(view, action))

        if action == 'selection':
            cls._last_selection_region = cls._view_region(view)

        if action == 'edit':
            edit_region = cls._view_region(view)
            edit_type, num_chars = cls._edit_info(cls._last_selection_region,
                                                  edit_region)
            if num_chars == 1:
                EditorCompletionsListener.queue_completions(
                    view, edit_region['end'])

    @staticmethod
    def _view_region(view):
        if view is None or view.sel() is None or len(view.sel()) != 1:
            return None

        r = view.sel()[0]
        return {
            'file': view.file_name(),
            'begin': r.begin(),
            'end': r.end(),
        }

    @staticmethod
    def _edit_info(selection, edit):
        no_info = (None, None)

        if (selection is None or edit is None or
            selection['file'] != edit['file']):
            return no_info

        if (edit['end'] > selection['end']):
            return ('addition', edit['end'] - selection['end'])
        if (edit['end'] < selection['end']):
            return ('deletion', selection['end'] - edit['end'])

        return no_info

    @staticmethod
    def _event_data(view, action):
        text = view.substr(sublime.Region(0, view.size()))

        if not _check_view_size(view):
            action = 'skip'
            text = ''

        return {
            'source': 'sublime3',
            'filename': realpath(view.file_name()),
            'text': text,
            'action': action,
            'selections': [{'start': r.a, 'end': r.b} for r in view.sel()],
        }


class EditorCompletionsListener(sublime_plugin.EventListener):
    """Listener which handles completions by hooking into Sublime's builtin
    triggers and forwarding requests to the completions endpoint
    """

    _received_completions = []
    _lock = Lock()

    def on_query_completions(self, view, prefix, locations):
        cls = self.__class__
        logger.log("running on_query_completions with {} completions"
                   .format(len(cls._received_completions)))

        if not _is_view_supported(view):
            return None

        if not _check_view_size(view):
            return None

        if len(locations) != 1:
            return None

        with cls._lock:
            completions = []
            if len(cls._received_completions) > 0:
                completions = [
                    (self._brand_completion(c['display'], c['hint']),
                     c['insert']) for c in cls._received_completions
                ]
                cls._received_completions = []
            logger.log("displaying {} completions".format(len(completions)))
            return completions

    @classmethod
    def queue_completions(cls, view, location):
        deferred.defer(cls._request_completions,
                       view, cls._event_data(view, location))

    @classmethod
    def _request_completions(cls, view, data):
        resp = requests.kited_post('/clientapi/editor/completions', data)

        logger.log("completions returned {} status code".format(resp.status))
        if resp.status != 200:
            return

        try:
            body = resp.read()
            if body:
                resp_data = json.loads(body.decode('utf-8'))
                completions = resp_data['completions'] or []
                with cls._lock:
                    cls._received_completions = completions
                if len(completions) > 0:
                    logger.log("running auto_complete with {} completions"
                               .format(len(cls._received_completions)))
                    cls._run_auto_complete(view)
        except ValueError as ex:
            logger.log("error decoding json: {}".format(ex))

    @staticmethod
    def _run_auto_complete(view):
        view.run_command('hide_auto_complete')
        view.run_command('auto_complete', {
            'api_completions_only': True,
            'disable_auto_insert': True,
            'next_completion_if_showing': False,
        })

    @staticmethod
    def _brand_completion(symbol, hint=None):
        return ('{}\t{} ⓚ'.format(symbol, hint) if hint
                else '{}\tⓚ'.format(symbol))
        # return ('{}\t{} ♢'.format(symbol, hint) if hint
        #         else '{}\t♢'.format(symbol))

    @staticmethod
    def _event_data(view, location):
        return {
            'filename': realpath(view.file_name()),
            'editor': 'sublime3',
            'text': view.substr(sublime.Region(0, view.size())),
            'cursor_runes': location,
        }
