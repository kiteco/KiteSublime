import sublime
import sublime_plugin

from ..lib import logger, settings


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
