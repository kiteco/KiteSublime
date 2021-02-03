import sublime
import json

from ..lib import link_opener

def from_local_requests_error(body):
    """ from_local_requests_error parses the body of a non-200 response
        returned by our local requests library for a notification. If
        one exists, it will create a sublime dialog.
    """
    try:
        data = json.loads(body.decode('utf-8'))
        _from_data(data)
    except ValueError as ex:
        print(ex)

def from_py_requests_error(resp, default_title="", default_body=""):
    """ from_py_requests_error parses the response of a non-200 response
        returned by the python requests library for a notification. If
        one exists, it will create a sublime dialog. If provided defaults, they
        will be used to fill missing information or create a generic notification.
    """
    try:
        data = resp.json()
        _from_data(data, default_title)
    except ValueError as ex:
        print(ex)

def _from_data(data, default_title="", default_body=""):
    try:
        if 'notification' in data:
            notif = data['notification']
            title, body = notif['title'], notif['body']
            buttons = [] if not notif['buttons'] else notif['buttons']
            # All notifications have a dismiss according to the API,
            # So remove them when deciding which to use
            buttons = list(filter(lambda b: b['action'] != 'dismiss', buttons))
            if len(buttons) == 0:
                _dismiss_only_notify(title, body)
            elif len(buttons) == 1:
                print(1)
                _single_custom_button_notify(title, body, buttons[0])
            elif len(buttons) == 2:
                print(2)
                _double_custom_button_notify(title, body, buttons)
            # Sublime's API doesn't support 3 or more custom buttons
            else:
                _dismiss_only_notify(default_title, default_body)
        elif "message" in data:
            _dismiss_only_notify(default_title, data["message"])
        else:
            _dismiss_only_notify(default_title, default_body)
    except KeyError as ex:
        print(ex)
        _dismiss_only_notify(default_title, default_body)

def _single_custom_button_notify(title, body, button):
    ok = sublime.ok_cancel_dialog(title+"\n\n"+body, button['text'])
    if ok:
        _do_button_action(button)

def _double_custom_button_notify(title, body, buttons):
    first, second = buttons[0], buttons[1]

    res = sublime.yes_no_cancel_dialog(title+"\n\n"+body, first['text'], second['text'])
    if res == sublime.DIALOG_YES:
        _do_button_action(first)
    elif res == sublime.DIALOG_NO:
        _do_button_action(second)

def _do_button_action(button):
    if button['action'] == 'open':
        link_opener.open_browser_url(button['link'])
    elif button['action'] == 'dismiss':
        return

def _dismiss_only_notify(title, body):
    if title != "" and body != "":
        sublime.error_message(title + "\n\n" + body)
    elif body != "":
        sublime.error_message(body)
