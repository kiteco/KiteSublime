import os
import requests
import sublime
from collections import defaultdict

from ..lib import link_opener, notification
from ..lib import errors

def related_code_from_file(view):
    related_code(lambda: True, view.file_name(), None)

def related_code_from_line(view):
    sels = view.sel()
    start_point = sels[0].begin()
    zero_based_line_no = view.rowcol(start_point)[0]

    def precond():
        if len(sels) > 1:
            raise Exception("Navigation only works for a single selection.")

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
            "Kite Code Finder Error \n\n" +
            str(e)
        )

def request_related_code(filename, line_no):
    """ Attempts to initiate a related code request
        Notifies on non-200 responses
    """
    # This uses the regular requests library instead of the local one
    # because it needs a long timeout to allow the copilot to launch
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
        notification.from_py_requests_error(
                resp,
                "Kite Code Finder Error",
                "Oops! Something went wrong with Code Finder. Please try again later."
        )
