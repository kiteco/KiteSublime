import sublime
import sublime_plugin

import json

from ..lib import deferred, logger


__all__ = ['EditorEventListener', 'EditorCompletionsListener']


def _is_view_supported(view):
    return view.file_name() is not None and view.file_name().endswith('.py')


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

        if action == 'selection':
            cls._last_selection_region = cls._view_region(view)

        if action == 'edit':
            edit_type, num_chars = cls._edit_info(cls._last_selection_region,
                                                  cls._view_region(view))
            if edit_type == 'addition' and num_chars == 1:
                view.run_command('auto_complete', {
                    'api_completions_only': True,
                    'disable_auto_insert': True,
                    'next_completion_if_showing': False,
                })

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



class EditorCompletionsListener(sublime_plugin.EventListener):
    """Listener which handles completions by hooking into Sublime's builtin
    triggers and forwarding requests to the completions endpoint
    """

    def on_query_completions(self, view, prefix, locations):
        if not _is_view_supported(view):
            return

        logger.log("firing completions")
        compls = []
        return compls

    @staticmethod
    def _brand_completion(symbol, hint=None):
        return ('{}\t{} ⓚ'.format(symobl, hint) if hint
                else '{}\tⓚ'.format(symbol))
