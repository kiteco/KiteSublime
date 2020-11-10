import sublime
import sublime_plugin

from ..lib import app_controller, link_opener, logger, settings
from ..lib import onboarding, codenav
from ..lib.handlers import HoverHandler, SignaturesHandler
from ..lib.languages import Languages


class KiteShowHover(sublime_plugin.TextCommand):
    """Command to show the hover popup for the symbol currently underneath the
    user's cursor. If there are no docs, then the symbol at the user's cursor
    position will flash invalid.
    """

    _UNRESOLVED_KEY = 'kite.unresolved'
    _FLASH_INTERVAL = 100

    def run(self, edit):
        points, symbol = HoverHandler.symbol_at_cursor(self.view, render=True)
        if not symbol and points:
            self.__class__.flash_invalid(self.view, points)

    @classmethod
    def flash_invalid(cls, view, points, times=2):
        if times <= 0:
            return

        def next_flash():
            view.erase_regions(cls._UNRESOLVED_KEY)
            sublime.set_timeout_async(
                lambda: cls.flash_invalid(view, points, times-1),
                cls._FLASH_INTERVAL)

        view.add_regions(cls._UNRESOLVED_KEY, [points], 'invalid')
        sublime.set_timeout_async(next_flash, cls._FLASH_INTERVAL)


class KiteDocsAtCursor(sublime_plugin.TextCommand):
    """Command to retrieve documentation for the symbol currently underneath
    the user's cursor and if available, to render it in the Copilot. If there
    are no docs, then the symbol at the user's cursor position will flash
    invalid.
    """

    def run(self, edit):
        points, symbol = HoverHandler.symbol_at_cursor(self.view)
        if symbol:
            link_opener.open_copilot(symbol['id'])
        elif points:
            KiteShowHover.flash_invalid(self.view, points)


class KiteShowSignatures(sublime_plugin.TextCommand):
    """Command to show signatures for the function call the cursor is currently
    in.
    """

    def run(self, edit):
        if len(self.view.sel()) != 1:
            return None
        r = self.view.sel()[0]
        SignaturesHandler.queue_signatures(self.view, r.end())


class KiteToggleKeywordArguments(sublime_plugin.TextCommand):
    """Command to toggle the setting which controls whether or not keyword
    arguments should be rendered in the function signatures panel.
    """

    def run(self, edit):
        value = settings.get('show_keyword_arguments', False)
        settings.set('show_keyword_arguments', not value)


class KiteTogglePopularPatterns(sublime_plugin.TextCommand):
    """Command to toggle the setting which controls whether or not popular
    patterns should be rendered in the function signatures panel.
    """

    def run(self, edit):
        value = settings.get('show_popular_patterns', False)
        settings.set('show_popular_patterns', not value)


class KiteHideSignatures(sublime_plugin.TextCommand):
    """Command to hide signatures if they are currently being displayed.
    """

    def run(self, edit):
        SignaturesHandler.hide_signatures_if_showing(self.view)


class KiteViewErase(sublime_plugin.TextCommand):
    """Command to erase a range of text from a view.
    """

    def run(self, edit, range):
        logger.debug('erasing {}'.format(range))
        self.view.erase(edit, sublime.Region(range[0], range[1]))


class KiteOpenCopilot(sublime_plugin.ApplicationCommand):
    """Command to open the Copilot.
    """

    def run(self):
        link_opener.open_copilot_root('')


class KiteStartEngine(sublime_plugin.ApplicationCommand):
    """Command to start the Kite Engine.
    """

    def run(self):
        if not app_controller.is_kite_installed():
            if sublime.ok_cancel_dialog(
                'Kite Engine is not installed. You can install it at ' \
                'https://kite.com/download.',
                ok_title='Download'
            ):
                link_opener.open_browser_url('https://kite.com/download')

        elif app_controller.is_kite_running():
            sublime.message_dialog('Kite Engine is already running!')

        else:
            app_controller.launch_kite_if_not_running()


class KiteEngineSettings(sublime_plugin.ApplicationCommand):
    """Command to open Kite settings in the Copilot.
    """

    def run(self):
        link_opener.open_copilot_root('settings')


class KitePythonTutorial(sublime_plugin.ApplicationCommand):
    """Command to start the live onboarding.
    """

    def run(self):
        onboarding.open_tutorial(Languages.PYTHON)


class KiteJavascriptTutorial(sublime_plugin.ApplicationCommand):
    """Command to start the live onboarding.
    """

    def run(self):
        onboarding.open_tutorial(Languages.JAVASCRIPT)


class KiteGoTutorial(sublime_plugin.ApplicationCommand):
    """Command to start the live onboarding.
    """

    def run(self):
        onboarding.open_tutorial(Languages.GO)


class KiteHelp(sublime_plugin.ApplicationCommand):
    """Command to open the help docs.
    """

    _URL = 'https://help.kite.com/category/44-sublime-text-integration'

    def run(self):
        link_opener.open_browser_url(self._URL)

class KiteFindRelatedCodeFromFile(sublime_plugin.WindowCommand):
    """Command to initiate file-based codenav
    """

    def run(self):
        codenav.related_code_from_file(self.window.active_view())

class KiteFindRelatedCodeFromLine(sublime_plugin.WindowCommand):
    """Command to initiate line-based codenav
    """

    def run(self):
        codenav.related_code_from_line(self.window.active_view())
