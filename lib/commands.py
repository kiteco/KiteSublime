import sublime
import sublime_plugin

from ..lib import logger, settings


class TogglePopularPatterns(sublime_plugin.TextCommand):
    """Command to toggle the setting which controls whether or not popular
    patterns should be rendered in the function signatures panel.
    """

    def run(self, edit):
        value = settings.get('show_popular_patterns', False)
        settings.set('show_popular_patterns', not value)
        logger.log('set show_popular_patterns to {}'
                   .format(settings.get('show_popular_patterns')))
