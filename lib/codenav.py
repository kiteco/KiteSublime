import os
import requests
import sublime
from collections import defaultdict

from ..lib import link_opener
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
        Raises exceptions from response errors
    """
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
            raise Exception("Oops! Something went wrong with Code Finder. Please try again later.")
