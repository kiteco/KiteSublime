import requests
import sublime
from collections import defaultdict

from ..lib import link_opener
from ..lib import errors

err_to_exception = defaultdict(lambda: errors.GenericRelatedCodeError, {
    'ErrPathNotInSupportedProject': errors.PathNotInSupportedProjectError,
    'ErrProjectStillIndexing': errors.ProjectStillIndexingError,
})

def related_code_from_file(view):
    related_code(lambda: True, view.file_name(), None)

def related_code_from_line(view):
    sels = view.sel()
    start_point = sels[0].begin()
    zero_based_line_no = view.rowcol(start_point)[0]

    def precond():
        if len(sels) > 1:
            raise errors.MultipleSelectionError("", "MultipleSelectionError")
        if (view.classify(start_point) & sublime.CLASS_EMPTY_LINE) != 0:
            raise errors.EmptyLineSelectionError("", "EmptyLineSeletionError")

    related_code(precond, view.file_name(), zero_based_line_no+1)

def related_code(precond, filename, line_no):
    """ Runs a precondition function and then requests related code
        Catches expected errors and notifies the user
    """
    try:
        precond()
        request_related_code(filename, line_no)
    except errors.MultipleSelectionError:
        sublime.error_message(
            "Kite Code Finder Error \n\n" +
            "Navigation only works for a single selection."
        )
    except errors.EmptyLineSelectionError:
        sublime.error_message(
            "Kite Code Finder Error \n\n" +
            " ".join(["Line", str(line_no), "in", filename, "is empty. "]) +
            "Code finder only works on non-empty lines."
        )
    except requests.exceptions.RequestException:
        sublime.error_message(
            "Kite Code Finder Error \n\n" +
            "Kite could not be reached. " +
            "Please check that Kite engine is running."
        )
    except errors.PathNotInSupportedProjectError:
        sublime.error_message(
            "Kite Code Finder Error \n\n" +
            " ".join(["The file", filename, "is not in any Git project. "]) +
            "Code finder only works inside Git projects."
        )
    except errors.ProjectStillIndexingError:
        sublime.error_message(
            "Kite Code Finder Error \n\n" +
            "Kite is not done indexing your project yet. " +
            "Please wait for the status icon to switch to ready before using Code Finder."
        )
    except errors.GenericRelatedCodeError:
        sublime.error_message(
            "Kite Code Finder Error \n\n" +
            "Oops! Something went wrong with Code Finder. Please try again later."
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
        exc = resp.content.decode('utf8').strip()
        raise err_to_exception[exc](exc, exc)
