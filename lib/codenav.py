import os
import sys
import urllib
import requests
import sublime
from collections import defaultdict
from string import Template
from threading import Timer, Lock

from ..lib import link_opener
from ..lib import errors
from ..lib import settings

def related_code_from_file(view):
    related_code(lambda: True, view.file_name(), None)

def related_code_from_line(view):
    sels = view.sel()
    start_point = sels[0].begin()
    zero_based_line_no = view.rowcol(start_point)[0]

    def precond():
        if len(sels) > 1:
            raise Exception('Navigation only works for a single selection.')

    related_code(precond, view.file_name(), zero_based_line_no+1)

def related_code(precond, filename, line_no):
    """ Runs a precondition function and then requests related code
        Catches expected errors and notifies the user
    """
    try:
        precond()
        request_related_code(filename, line_no)
    except Exception as e:
        sublime.error_message(
            'Kite Code Finder Error \n\n' +
            str(e)
        )

def request_related_code(filename, line_no):
    """ Attempts to initiate a related code request
        Raises exceptions from response errors
    """
    try:
        url = 'http://localhost:46624/codenav/editor/related'
        resp = requests.post(url, json=
                    {
                        'editor': 'sublime3',
                        'editor_install_path': sublime.executable_path(),
                        'location': {
                            'filename': filename,
                            'line': line_no
                        },
                    }
                )
        if resp.status_code != 200:
            err = resp.json()
            if "message" in err:
                raise Exception(err["message"])
            else:
                raise Exception('Oops! Something went wrong with Code Finder. Please try again later.')
    except requests.ConnectionError:
        raise Exception('Kite could not be reached. Please check that Kite engine is running.')

class RelatedCodeLinePhantom:
    """ RelatedCodeLinePhantom ...
    """

    _key = 'related-code'
    _template_path = 'Packages/KiteSublime/lib/assets/' \
                     'codenav-phantom.mini.html'
    _template = None

    def __init__(self):
        self._lock = Lock()
        self.html = None
        self.phantom_set = None
        self.active_view = None
        self.line_info = None
        self.row = None
        self.visible = False
        self.timer = None

    def on_modified(self, view):
        def timer_decorate(view):
            with self._lock:
                self._decorate_locked(view)
                self.timer = None

        if not settings.get('enable_codefinder_line_phantom', True):
            return
        with self._lock:
            self._clear_phantom()
            if self.timer is not None:
                self.timer.cancel()
            self.timer = Timer(1.0, timer_decorate, [view])
            self.timer.start()

    def on_selection_modified(self, view):
        if not settings.get('enable_codefinder_line_phantom', True):
            return
        with self._lock:
            # If a timer exists, the user has recently made an edit
            # and the timer must expire before movements can decorate again
            if self.timer is None:
                self._decorate_locked(view)

    def _decorate_locked(self, view):
        sel_end, redraw, clear = self._should_redraw(view)
        if not redraw:
            if clear:
                self._clear_phantom()
            return

        applicable = self.line_info is not None and 'project_ready' in self.line_info
        ready = self.line_info is not None and self.line_info.get('project_ready', False)
        if self.line_info is None or view != self.active_view or (applicable and not ready):
            self._reset(view)

        if self.line_info is not None and self.line_info.get('project_ready', False):
            p = sublime.Phantom(
                    sublime.Region(sel_end, sel_end+1),
                    self.html,
                    sublime.LAYOUT_INLINE,
                    on_navigate=lambda href: href == RelatedCodeLinePhantom._key and related_code_from_line(view)
            )
            self.phantom_set.update([p])
            self.visible = True

    def _should_redraw(self, view):
        """ _should_redraw determines whether the phantom should be shown
            and updates the saved row to where the cursor is
            It returns selection_end, redraw, clear
        """
        selections = view.sel()
        last_line = view.full_line(view.size())
        sel_line = view.full_line(selections[0])
        self.row, old_row = view.rowcol(sel_line.begin())[0], self.row

        # Avoids flickering while moving horizontally
        if self.row == old_row and self.visible:
            # Avoid cursor moving past phantom when deleting entire line
            clear = view.classify(sel_line.begin()) & sublime.CLASS_EMPTY_LINE != 0
            return None, False, clear

        if len(selections) != 1:
            return None, False, True

        # Last line shifts the last character past the phantom
        # Modiying the phantom region to end_pt+1, end_pt+2 helps,
        # But the cursor can then move past the phantom, making it
        # awkward to type. So we don't show it here.
        if last_line == sel_line:
            return None, False, True

        # Empty lines the cursor can move past the phantom
        if (view.classify(sel_line.begin()) & sublime.CLASS_EMPTY_LINE) != 0:
            return None, False, True

        # Convert to inclusive
        return sel_line.end()-1, True, False

    def _reset(self, view):
        self._clear_phantom()
        self.active_view = view
        self.phantom_set = sublime.PhantomSet(view, RelatedCodeLinePhantom._key)
        self.line_info = None
        self.line_info = self._request_line_decoration(view.file_name())
        if self.line_info is not None:
            if type(self)._template is None:
                type(self).load_template()
            self.html = type(self)._template.substitute(
                    # text-decoration: none makes whitespace not clickable in a-tags
                    # https://github.com/sublimehq/sublime_text/issues/3373
                    inline_message='\u00A0'.join(self.line_info['inline_message'].split(' ')),
                    logo_src='file://'+os.path.join(
                            os.path.dirname(os.path.abspath(__file__)),
                            'assets',
                            'kite-logo-light-blue.png'
                    )
            )

    def _clear_phantom(self):
        if self.phantom_set is not None:
            self.phantom_set.update([])
        self.visible = False

    @classmethod
    def _request_line_decoration(cls, filename):
        try:
            url = 'http://localhost:46624/codenav/decoration/line'
            resp = requests.post(url, json= { 'filename': filename })
            if resp.status_code != 200:
                return None
            return resp.json()
        except requests.ConnectionError as e:
            pass
        return None

    @classmethod
    def load_template(cls):
        t = Template(sublime.load_resource(cls._template_path))
        with_key = t.safe_substitute(href_key=RelatedCodeLinePhantom._key)
        cls._template = Template(with_key)
