import sublime
import sublime_plugin

from ..lib import link_opener, logger, settings
from ..lib.handlers import HoverHandler


class ToggleKeywordArguments(sublime_plugin.TextCommand):
    """Command to toggle the setting which controls whether or not keyword
    arguments should be rendered in the function signatures panel.
    """

    def run(self, edit):
        value = settings.get('show_keyword_arguments', False)
        settings.set('show_keyword_arguments', not value)


class TogglePopularPatterns(sublime_plugin.TextCommand):
    """Command to toggle the setting which controls whether or not popular
    patterns should be rendered in the function signatures panel.
    """

    def run(self, edit):
        value = settings.get('show_popular_patterns', False)
        settings.set('show_popular_patterns', not value)


class DocsAtCursor(sublime_plugin.TextCommand):
    """Command to retrieve documentation for the symbol currently underneath
    the user's cursor and if available, to render it in the Copilot. If there
    are no docs, then the symbol at the user's cursor position will flash
    invalid.
    """

    _UNRESOLVED_KEY = 'kite.unresolved'
    _FLASH_INTERVAL = 100

    def run(self, edit):
        cls = self.__class__
        points, symbol = HoverHandler.symbol_at_cursor(self.view)
        if symbol:
            link_opener.open_copilot(symbol['id'])
        elif points:
            self.__class__._flash_invalid(self.view, points)

    @classmethod
    def _flash_invalid(cls, view, points, cnt=2):
        if cnt <= 0:
            return

        def next_flash():
            view.erase_regions(cls._UNRESOLVED_KEY)
            sublime.set_timeout_async(
                lambda: cls._flash_invalid(view, points, cnt-1),
                cls._FLASH_INTERVAL)

        view.add_regions(cls._UNRESOLVED_KEY, [points], 'invalid')
        sublime.set_timeout_async(next_flash, cls._FLASH_INTERVAL)
