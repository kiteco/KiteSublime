import sublime
import sublime_plugin

import hashlib
import htmlmin
import json
import sys
from http.client import CannotSendRequest
from os.path import realpath
from threading import Lock
from urllib.parse import quote

from ..lib import deferred, keymap, link_opener, logger, settings, requests
from ..lib.errors import ExpectedError
from ..lib.file_system import path_for_url
from ..setup import is_development, os_version, package_version

# Use the vendored version explicitly in case the user has an older version
# of jinja2 in his environment e.g. GitGutter uses v2.8, which is outdated.
import importlib

jinja_mods = [m for m in sys.modules.keys()
              if m == 'jinja2' or m.startswith('jinja2.')]
for m in jinja_mods:
    logger.log('unloading {}'.format(m))
    del sys.modules[m]

from ..vendor.jinja2 import Template

for m in jinja_mods:
    if m not in sys.modules:
        logger.log('reloading {}'.format(m))
        try:
            importlib.import_module(m)
        except ImportError:
            logger.log('could not load {}'.format(m))

__all__ = [
    'EventDispatcher',
    'CompletionsHandler',
    'SignaturesHandler',
    'HoverHandler',
    'StatusHandler',
]


def _is_view_supported(view):
    return view.file_name() is not None and view.file_name().endswith('.py')


def _check_view_size(view):
    # max file size is 75 kilobytes (75 * 1024)
    return view.size() <= 76800


def _in_function_call(view, point):
    # The first matched scope is for 3176, and the second is for 3200. Both
    # are checked here as a hacky fix to account for changes in the API. We
    # should instead factor version handling logic into a separate module.
    return ((view.match_selector(point, 'meta.function-call.python') or
             view.match_selector(point, 'meta.function-call.arguments.python'))
            and not view.match_selector(point, 'variable.function.python'))


def _at_function_call_begin(view, point):
    return (_in_function_call(view, point) and
            view.match_selector(point,
                                'punctuation.section.arguments.begin.python'))


def _at_function_call_end(view, point):
    return (_in_function_call(view, point) and
            view.match_selector(point,
                                'punctuation.section.arguments.end.python'))


def _in_empty_function_call(view, point):
    return (_at_function_call_begin(view, point - 1) and
            _at_function_call_end(view, point))


def _md5(text):
    return hashlib.md5(str.encode(text)).hexdigest()


class EventDispatcher(sublime_plugin.EventListener):
    """Listener which forwards editor events to the event endpoint and also
    fetches completions and function signature information when the proper
    event triggers are fired.
    """

    _last_selection_region = None

    def on_modified(self, view):
        self.__class__._handle(view, 'edit')

    def on_selection_modified(self, view):
        self.__class__._handle(view, 'selection')

    @classmethod
    def _handle(cls, view, action):
        if not _is_view_supported(view):
            return

        # Workaround to handle cloned views
        # See https://github.com/SublimeTextIssues/Core/issues/289
        view = sublime.active_window().active_view()

        deferred.defer(requests.kited_post, '/clientapi/editor/event',
                       data=cls._event_data(view, action))

        if action == 'selection':
            select_region = cls._view_region(view)
            cls._last_selection_region = select_region

            if (select_region is not None and
                    _in_function_call(view, select_region['end'])):
                if SignaturesHandler.is_activated():
                    SignaturesHandler.queue_signatures(view,
                                                       select_region['end'])
            else:
                SignaturesHandler.hide_signatures(view)

        if action == 'edit' and _check_view_size(view):
            edit_region = cls._view_region(view)
            edit_type, num_chars = cls._edit_info(cls._last_selection_region,
                                                  edit_region)
            if edit_type == 'insertion' and num_chars == 1:
                if view.settings().get('auto_complete'):
                    CompletionsHandler.queue_completions(view,
                                                         edit_region['end'])
            elif edit_type == 'deletion' and num_chars > 1:
                CompletionsHandler.hide_completions(view)

            if (edit_region is not None
                    and _in_function_call(view, edit_region['end'])):
                if (settings.get('show_function_signatures', True) or
                        SignaturesHandler.is_activated()):
                    SignaturesHandler.queue_signatures(view,
                                                       edit_region['end'])
            else:
                SignaturesHandler.hide_signatures(view)

    @staticmethod
    def _view_region(view):
        if len(view.sel()) != 1:
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

        if edit['end'] > selection['end']:
            return 'insertion', edit['end'] - selection['end']
        if edit['end'] < selection['end']:
            return 'deletion', selection['end'] - edit['end']

        return no_info

    @staticmethod
    def _event_data(view, action):
        text = view.substr(sublime.Region(0, view.size()))

        if not _check_view_size(view):
            action = 'skip'
            text = ''

        return {
            'source': 'sublime3',
            'filename': realpath(view.file_name()),
            'text': text,
            'action': action,
            'selections': [{'start': r.a, 'end': r.b} for r in view.sel()],
            'editor_version': sublime.version(),
            'plugin_version': package_version(),
        }


class CompletionsHandler(sublime_plugin.EventListener):
    """Listener which handles completions by preemptively forwarding requests
    to the completions endpoint and then running the Sublime `auto_complete`
    command.
    """

    _received_completions = []
    _visible_completions = []
    _last_location = None
    _lock = Lock()

    def on_query_completions(self, view, prefix, locations):
        # Prevent completions from showing up in non-active views
        if sublime.active_window().active_view().id() != view.id():
            return None

        cls = self.__class__

        if not _is_view_supported(view):
            return None

        if not _check_view_size(view):
            return None

        if len(locations) != 1:
            return None

        with cls._lock:
            if cls._last_location is None:
                cls._received_completions = []
                cls._visible_completions = []
                cls._last_location = None
                cls.queue_completions(view, locations[0])
                return None

            if (cls._last_location != locations[0]
                    and cls._received_completions):
                logger.debug('completions location mismatch: {} != {}'
                             .format(cls._last_location, locations[0]))

            completions = None
            if (cls._last_location == locations[0] and
                    cls._received_completions):
                completions = self._flatten_completions(
                    cls._received_completions)

            cls._visible_completions = cls._received_completions
            cls._received_completions = []
            cls._last_location = None

            return completions

    def on_post_text_command(self, view, command_name, args):
        if command_name not in ('prev_field', 'next_field', 'commit_completion', 'insert_best_completion'):
            return
        if len(view.sel()) != 1:
            return

        # we must only show completions if a placeholder was selected
        # there's no way to be notified when a particular completion item was inserted
        # the closest thing we can do is to show completions
        # only when a non-empty selection (i.e. size > 1) is present after the command
        # was executed
        r = view.sel()[0]
        if not r.empty():
            # a reversed region might have r.a > r.b
            a, b = sorted([r.a, r.b])
            self.queue_completions(view, [a, b])

    @classmethod
    def queue_completions(cls, view, location):
        deferred.defer(cls._request_completions,
                       view, cls._event_data(view, location))

    @classmethod
    def hide_completions(cls, view):
        with cls._lock:
            cls._received_completions = []
            cls._visible_completions = []
            cls._last_location = None
        view.run_command('hide_auto_complete')

    @staticmethod
    def _is_snippets_enabled():
        return settings.get('enable_snippets', True)

    @classmethod
    def _request_completions(cls, view, data):
        resp, body = requests.kited_post('/clientapi/editor/complete', data)

        if resp.status != 200 or not body:
            return

        resp_data = json.loads(body.decode('utf-8'))
        completions = resp_data['completions'] or []
        with cls._lock:
            cls._received_completions = completions
            cls._last_location = data['position']['end']
        cls._run_auto_complete(view)

    @classmethod
    def _run_auto_complete(cls, view):
        # Don't refresh if Kite doesn't have completions. Sublime will
        # filter the completions for us automatically.
        with cls._lock:
            if len(cls._received_completions) == 0:
                return

        # It seems like the `auto_complete` command does not always result in
        # `on_query_completions` from being triggered if a completion list is
        # currently shown, so we need to hide it first.
        #
        # However, we only need to refresh the completions UI if the incoming
        # completions contain any completions that were not in the previous
        # list. Otherwise, Sublime will filter the UI automatically.
        if not cls._is_completions_subset():
            view.run_command('hide_auto_complete')
            view.run_command('auto_complete', {
                'api_completions_only': True,
                'disable_auto_insert': True,
                'next_completion_if_showing': False,
            })

    @classmethod
    def _is_completions_subset(cls):
        with cls._lock:
            # both sets of completions are in the Kite's original data format
            previous = cls._flatten_completions(cls._visible_completions)
            current = cls._flatten_completions(cls._received_completions)

        if len(previous) == 0 or len(current) > len(previous):
            return False

        for index, item in enumerate(current):
            if not any((cls._completions_equal(item, prev_item)
                        for prev_item in previous)):
                return False

        return True

    @staticmethod
    def _completions_equal(lhs, rhs):
        return lhs[0] == rhs[0] and lhs[1] == rhs[1]

    @classmethod
    def _flatten_completions(cls, completions, nesting=0):
        if not completions:
            return []

        result = []
        for c in completions:
            # We were previously using _is_snippets_enabled to branch on old/new
            # logic, but it appears that sometimes this check fails so we need
            # handle each completion item individually.
            #
            # See: https://rollbar.com/Kite/sublime-prod/items/14275/
            if 'snippet' not in c:
                result.append((
                    cls._brand_completion(c['display'], c['hint']),
                    c['insert']
                ))
            else:
                result.append((cls._brand_completion(c['display'], c['hint']),
                               cls._placeholder_text(c)))
                if 'children' in c:
                    result.extend(cls._flatten_completions(c['children'],
                                                           nesting + 1))

        return result

    @staticmethod
    def _placeholder_text(completion):
        text = completion['snippet']['text']
        try:
            placeholders = completion['snippet']['placeholders']
            # sort placeholders in reverse order for easier string patching
            # we assume that placeholders do not overlap
            copy = sorted(placeholders, key=lambda i: i['begin'], reverse=True)
            for p in copy:
                a, b = p['begin'], p['end']
                index = placeholders.index(p) + 1  # +1 because $0 is the last placeholder
                text = text[:a] + "${{{}:{}}}".format(index, text[a:b]) + text[b:]
        except KeyError:
            return completion['snippet']['text']
        return text

    @staticmethod
    def _brand_completion(symbol, hint=None):
        return ('{}\t{} ⟠'.format(symbol, hint) if hint
                else '{}\t⟠'.format(symbol))

    @classmethod
    def _event_data(cls, view, location):
        if isinstance(location, list):
            a, b = location[0], location[1]
        else:
            a, b = location, location

        return {
            'filename': realpath(view.file_name()),
            'editor': 'sublime3',
            'text': view.substr(sublime.Region(0, view.size())),
            'position': {
                'begin': a,
                'end': b,
            },
            'no_snippets': not cls._is_snippets_enabled(),
        }

    @staticmethod
    def _event_data_old(view, location):
        return {
            'filename': realpath(view.file_name()),
            'editor': 'sublime3',
            'text': view.substr(sublime.Region(0, view.size())),
            'cursor_runes': location,
        }


class SignaturesHandler(sublime_plugin.EventListener):
    """Listener which handles signatures by sending requests to the signatures
    endpoint and rendering the returned data.
    """

    _activated = False
    _view = None
    _call = None
    _lock = Lock()

    _template_path = 'Packages/KiteSublime/lib/assets/' \
                     'function-signature-panel.html'
    _template = None
    _css_path = 'Packages/KiteSublime/lib/assets/styles.css'
    _css = ''

    def on_post_text_command(self, view, command_name, args):
        if command_name in ('kite_toggle_popular_patterns',
                            'kite_toggle_keyword_arguments'):
            self.__class__._rerender()

    def on_query_context(self, view, key, operator, operand, match_all):
        if (key == 'kite_signature_shown' and _is_view_supported(view) and
                self.__class__._activated):
            # In case Vintage is enabled, make sure we switch to command mode.
            # Questionable if this is the right behavior, since it differs
            # from the builtin behavior with respect to what happens when the
            # user hits escape while completions are shown - In this case, the
            # user still has to hit escape twice to enter command mode. However,
            # since we've received feedback about this, we've enabled this
            # behavior and have made it configurable.
            if settings.get('hide_signatures_enters_command_mode', True):
                view.run_command('exit_insert_mode')

            return True
        return None

    @classmethod
    def queue_signatures(cls, view, location):
        deferred.defer(cls._request_signatures,
                       view, cls._event_data(view, location))

    @classmethod
    def hide_signatures(cls, view):
        reset = False
        if cls._lock.acquire(blocking=False):
            if cls._activated:
                cls._activated = False
                cls._view = None
                cls._call = None
                reset = True
            cls._lock.release()

        if reset:
            view.hide_popup()

    @classmethod
    def hide_signatures_if_showing(cls, view):
        reset = False
        if cls._lock.acquire(blocking=False):
            if cls._activated:
                cls._activated = False
                cls._view = None
                cls._call = None
                reset = True
            cls._lock.release()

        if reset:
            # This needs to be deferred to handle a race condition when the
            # user is using Vintage. When command mode is entered, the cursor
            # moves back one character, which causes signatures to be requested
            # again. See this class's method `on_query_context` above.
            deferred.defer(view.hide_popup)

    @classmethod
    def is_activated(cls):
        return cls._activated

    @classmethod
    def _request_signatures(cls, view, data):
        resp, body = requests.kited_post('/clientapi/editor/signatures', data)

        if resp.status != 200 or not body:
            if resp.status in (400, 404):
                cls.hide_signatures(view)
            return

        resp_data = json.loads(body.decode('utf-8'))
        calls = resp_data['calls'] or []
        if len(calls):
            call = calls[0]

            if call['callee']['kind'] == 'type':
                call['callee']['details']['function'] = (
                    call['callee']['details']['type']['language_details']
                    ['python']['constructor'])
                ret = [{'type': call['func_name']}]
                call['callee']['details']['function']['return_value'] = ret

            # Separate out the keyword-only parameters
            func = call['callee']['details']['function']
            func.update({
                'positional_parameters': [],
                'keyword_only_parameters': [],
            })
            for _, param in enumerate(func['parameters'] or []):
                param_details = param['language_details']['python']
                if not param_details['keyword_only']:
                    func['positional_parameters'].append(param)
                else:
                    func['keyword_only_parameters'].append(param)

            in_kwargs = call['language_details']['python']['in_kwargs']

            content = None
            if cls._lock.acquire(blocking=False):
                cls._activated = True
                cls._view = view
                cls._call = call
                content = cls._render(call)
                cls._lock.release()

            requested_pos = data['cursor_runes']
            current_pos = EventDispatcher._last_selection_region['end']

            if content is not None and requested_pos == current_pos:
                view.show_popup(content,
                                flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                                max_width=400,
                                on_navigate=cls._handle_link_click)

    @classmethod
    def _render(cls, call):
        if is_development() or cls._template is None:
            cls._template = Template(sublime.load_resource(cls._template_path))
            cls._css = sublime.load_resource(cls._css_path)

        opts = {
            'platform': sys.platform,
            'os_version': os_version(),
            'show_popular_patterns': settings.get('show_popular_patterns'),
            'show_keyword_arguments': settings.get('show_keyword_arguments'),
            'keyword_argument_highlighted': cls._kwarg_highlighted(),
            'keyword_arguments_keys':
                keymap.keystr(keymap.get('kite_toggle_keyword_arguments')),
            'popular_patterns_keys':
                keymap.keystr(keymap.get('kite_toggle_popular_patterns')),
        }

        return htmlmin.minify(cls._template.render(css=cls._css, call=call,
                                                   **opts),
                              remove_all_empty_space=True)

    @classmethod
    def _rerender(cls):
        content = None
        if cls._lock.acquire(blocking=False):
            content = cls._render(cls._call) if cls._activated else None
            cls._lock.release()

        if content is not None:
            cls._view.show_popup(content,
                                 flags=sublime.COOPERATE_WITH_AUTO_COMPLETE,
                                 max_width=400,
                                 on_navigate=cls._handle_link_click)

    @classmethod
    def _handle_link_click(cls, target):
        if target == 'hide_popular_patterns':
            settings.set('show_popular_patterns', False)
            cls._rerender()

        elif target == 'show_popular_patterns':
            settings.set('show_popular_patterns', True)
            cls._rerender()

        elif target == 'hide_keyword_arguments':
            settings.set('show_keyword_arguments', False)
            cls._rerender()

        elif target == 'show_keyword_arguments':
            settings.set('show_keyword_arguments', True)
            cls._rerender()

        elif (target.startswith('open_browser') or
              target.startswith('open_copilot')):
            idx = target.find(':')
            if idx == -1:
                logger.debug('invalid open link format: {}'.format(target))
                return

            action = target[:idx]
            ident = target[idx + 1:]

            if action == 'open_browser':
                link_opener.open_browser(ident)
            else:
                link_opener.open_copilot(ident)

    @classmethod
    def _kwarg_highlighted(cls):
        return (cls._activated and
                cls._call['language_details']['python']['in_kwargs'] and
                cls._call['arg_index'] != -1)

    @staticmethod
    def _event_data(view, location):
        return {
            'editor': 'sublime3',
            'filename': realpath(view.file_name()),
            'text': view.substr(sublime.Region(0, view.size())),
            'cursor_runes': location,
        }


class HoverHandler(sublime_plugin.EventListener):
    """Listener which listens to the user's mouse position and forwards
    requests to the hover endpoint.
    """

    _template_path = 'Packages/KiteSublime/lib/assets/hover-panel.html'
    _template = None
    _css_path = 'Packages/KiteSublime/lib/assets/styles.css'
    _css = ''

    def on_hover(self, view, point, hover_zone):
        if not settings.get('show_hover', True):
            return

        if hover_zone != sublime.HOVER_TEXT:
            return

        if (_is_view_supported(view) and _check_view_size(view) and
                len(view.sel()) == 1):
            cls = self.__class__
            deferred.defer(cls._request_hover, view, point)

    @classmethod
    def symbol_at_cursor(cls, view, render=False):
        if (not _is_view_supported(view) or not _check_view_size(view) or
                len(view.sel()) != 1):
            return (None, None)

        view = sublime.active_window().active_view()

        point = view.sel()[0].end()
        points = view.word(point)

        resp, body = requests.kited_get(cls._event_url(view, point))

        if resp.status != 200 or not body:
            return (points, None)

        try:
            resp_data = json.loads(body.decode('utf-8'))
            symbol = None if not resp_data['symbol'] else resp_data['symbol'][0]

            if symbol and render:
                symbol['hint'] = cls._symbol_hint(symbol)

                def func():
                    view.show_popup(cls._render(symbol, resp_data['report'],
                                                view, point),
                                    max_width=1024, location=point,
                                    on_navigate=cls._handle_link_click)

                sublime.set_timeout_async(func, 0)

            return points, symbol

        except ValueError as ex:
            return points, None

    @classmethod
    def _request_hover(cls, view, point):
        resp, body = requests.kited_get(cls._event_url(view, point))

        if resp.status != 200 or not body:
            return

        resp_data = json.loads(body.decode('utf-8'))

        if resp_data['symbol'] is None:
            return

        symbol = resp_data['symbol'][0]
        symbol['hint'] = cls._symbol_hint(symbol)

        view.show_popup(cls._render(symbol, resp_data['report'], view, point),
                        flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
                        max_width=1024,
                        location=point,
                        on_navigate=cls._handle_link_click)

    @classmethod
    def _render(cls, symbol, report, view=None, point=None):
        if is_development() or cls._template is None:
            cls._template = Template(sublime.load_resource(cls._template_path))
            cls._css = sublime.load_resource(cls._css_path)

        defs = None
        refs = None
        if settings.get_global('show_definitions'):
            window = sublime.active_window()
            defs = window.lookup_symbol_in_index(symbol['name'])
            refs = window.lookup_references_in_index(symbol['name'])

            if view is not None and point is not None:
                line, col = view.rowcol(point)
                filename = realpath(view.file_name())
                defs = [d for d in defs
                        if d[0] != filename or d[2][0] != line + 1]
                refs = [r for r in refs
                        if r[0] != filename or r[2][0] != line + 1]

        return htmlmin.minify(cls._template.render(css=cls._css,
                                                   platform=sys.platform,
                                                   os_version=os_version(),
                                                   symbol=symbol,
                                                   report=report,
                                                   definitions=defs,
                                                   references=refs),
                              remove_all_empty_space=True)

    @classmethod
    def _handle_link_click(cls, target):
        if (target.startswith('open_browser') or
                target.startswith('open_copilot')):
            idx = target.find(':')
            if idx == -1:
                logger.debug('invalid open link format: {}'.format(target))
                return

            action = target[:idx]
            ident = target[idx + 1:]

            if action == 'open_browser':
                link_opener.open_browser(ident)
            else:
                link_opener.open_copilot(ident)

        elif target.startswith('open_definition'):
            idx = target.find(':')
            if idx == -1:
                logger.debug('invalid open definition format: {}'
                             .format(target))
                return

            dest = target[idx + 1:]
            if not dest[dest.rfind(':') + 1:].isdigit():
                logger.debug('invalid open definition format: {}'
                             .format(target))
                return

            sublime.active_window().open_file(dest,
                                              flags=sublime.ENCODED_POSITION)

    @staticmethod
    def _event_url(view, point):
        editor = 'sublime3'
        filename = quote(path_for_url(realpath(view.file_name())))
        hash_ = _md5(view.substr(sublime.Region(0, view.size())))
        return ('/api/buffer/{}/{}/{}/hover?cursor_runes={}'
                .format(editor, filename, hash_, point))

    @staticmethod
    def _symbol_hint(symbol):
        if symbol['value'][0]['kind'] != 'instance':
            return symbol['value'][0]['kind']
        else:
            unique_types = []
            for v in symbol['value']:
                if v['kind'] != 'instance':
                    continue
                if v['type'] not in unique_types:
                    unique_types.append(v['type'])
                    if len(unique_types) == 3:
                        break
            return ' | '.join(unique_types)


class StatusHandler(sublime_plugin.EventListener):
    """Listener which sets the status bar message when the view is activated
    and on every selection event.
    """

    _status_key = 'kite'

    def on_activated(self, view):
        deferred.defer(self.__class__._handle, view)

    def on_selection_modified(self, view):
        deferred.defer(self.__class__._handle, view)

    @classmethod
    def erase_all_statuses(cls):
        for w in sublime.windows():
            for v in w.views():
                v.erase_status(cls._status_key)

    @classmethod
    def _handle(cls, view):
        if not _is_view_supported(view):
            view.erase_status(cls._status_key)
            return

        if not _check_view_size(view):
            view.set_status(cls._status_key,
                            cls._brand_status('File too large'))
            return

        try:
            url = ('/clientapi/status?filename={}'
                   .format(quote(realpath(view.file_name()))))
            resp, body = requests.kited_get(url)

            if resp.status != 200 or not body:
                view.set_status(cls._status_key,
                                cls._brand_status('Server error'))
            else:
                resp_data = json.loads(body.decode('utf-8'))
                status = resp_data['status']
                if status == 'noIndex':
                    status = 'Ready (unindexed)'
                else:
                    status = status.capitalize()
                view.set_status(cls._status_key,
                                cls._brand_status(status))

        except ConnectionRefusedError as ex:
            view.set_status(cls._status_key,
                            cls._brand_status('Connection error'))

        except ExpectedError as exc:
            if isinstance(exc.exc, ConnectionRefusedError):
                view.set_status(cls._status_key,
                                cls._brand_status('Connection error'))

        except CannotSendRequest as ex:
            logger.debug('could not request status: {}'.format(ex))

    @classmethod
    def _brand_status(cls, status):
        return '𝕜𝕚𝕥𝕖: {}'.format(status)
