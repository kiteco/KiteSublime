import sublime
import sublime_plugin

import json

from ..lib import deferred


__all__ = ['EditorEventListener', 'EditorCompletionsListener']


class EditorEventListener(sublime_plugin.EventListener):
    """Listener which forwards editor events to /clientapi/editor/event
    """

    def on_modified(self, view):
        deferred.defer(self._handle, view, 'edit')

    def on_selection_modified(self, view):
        deferred.defer(self._handle, view, 'selection')

    def _handle(self, view, action):
        if action == 'edit':
            view.run_command('auto_complete', {
                'api_completions_only': True,
                'disable_auto_insert': True,
                'next_completion_if_showing': False,
            })


class EditorCompletionsListener(sublime_plugin.EventListener):
    """Listener which handles completions by hooking into Sublime's builtin
    triggers and forwarding requests to /clientapi/editor/completions
    """

    def on_query_completions(self, view, prefix, locations):
        print("firing completions")
        return []
