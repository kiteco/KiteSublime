import sublime
import sublime_plugin

import hashlib
import htmlmin
import json
import sys
from http.client import CannotSendRequest
from jinja2 import Template
from os.path import realpath
from threading import Lock
from urllib.parse import quote

from ..lib import deferred, keymap, link_opener, logger, settings, requests, languages
from ..lib.errors import ExpectedError
from ..lib.file_system import path_for_url
from ..setup import is_development, os_version, package_version

MAX_FILE_SIZE = 1048576  # 1 MB default

__all__ = [
    'EventDispatcher',
    'CompletionsHandler',
    'SignaturesHandler',
    'HoverHandler',
    'StatusHandler',
    'MaxFileSizeUpdater',
]


def _is_view_supported(view):
    return view.file_name() is not None and any(
        view.file_name().endswith(ext) for ext in languages.SUPPORTED_EXTS
    )


def _check_view_size(view):
    return view.size() <= MAX_FILE_SIZE


def _get_view_substr(view, start, end):
    return view.substr(sublime.Region(start, end))


def _get_word(view, point):
    word_region = view.word(point)
    return _get_view_substr(view, word_region.a, word_region.b)


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
            'selections': [{'start': r.a, 'end': r.b, 'encoding': 'utf-32'} for r in view.sel()],
            'editor_version': sublime.version(),
            'plugin_version': package_version(),
        }


class CompletionsHandler(sublime_plugin.EventListener):
    """Listener which handles completions by preemptively forwarding requests
    to the completions endpoint and then running the Sublime `auto_complete`
    command.
    """

    _lock = Lock()

    # The last buffer location at which completions were requested. This value
    # gets updated on every completions request, regardless of whether or not
    # a new set of completions are initialized.
    _last_location = None

    # The last prefix at which completions were requested. This value gets
    # updated on every completions request, regardless of whether or not a
    # new set of completions are initialized.
    _last_prefix = None

    # The last list of completions that were received from the backend. This
    # value gets updated on every completions request, regardless of whether
    # or not a new set of completions are initialized.
    _last_received_completions = []

    # The last character that triggered completions. This value gets updated on
    # every completions request.
    _last_trigger_char = None

    # The last buffer location at which completions were initialized. This
    # value only gets changed when a new set of completions is sent back to
    # the UI.
    _last_init_location = None

    # The last prefix that was recorded at completions initialization. This
    # value only gets changed when a new set of completions is sent back to
    # the UI.
    _last_init_prefix = None

    # The last list of completions that were initialized. This value only gets
    # changed when a new set of completions is sent back to the UI.
    _last_init_completions = []

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
                cls._last_received_completions = []
                cls._last_init_completions = []
                cls._last_location = None
                cls.queue_completions(view, locations[0])
                return None

            if (cls._last_location != locations[0]
                    and cls._last_received_completions):
                logger.debug('completions location mismatch: {} != {}'
                             .format(cls._last_location, locations[0]))
                cls._clear_cache()

            completions = None
            if (cls._last_location == locations[0] and
                    cls._last_received_completions):
                completions = self._flatten_completions(
                    cls._last_received_completions)
                cls._last_init_completions = cls._last_received_completions
                cls._last_init_location = cls._last_location
                cls._last_init_prefix = prefix

            return completions

    def on_post_text_command(self, view, command_name, args):
        if command_name not in ('prev_field', 'next_field',
                                'commit_completion', 'insert_best_completion'):
            return
        if len(view.sel()) != 1:
            return

        cls = self.__class__
        region = view.sel()[0]
        on_placeholder = not region.empty()

        # we must only show completions if a placeholder was selected
        # there's no way to be notified when a particular completion item was
        # inserted
        # the closest thing we can do is to show completions
        # only when a non-empty selection (i.e. size > 1) is present after the
        # command was executed
        if on_placeholder:
            # a reversed region might have region.a > region.b
            a, b = sorted([region.a, region.b])
            cls.queue_completions(view, [a, b])

        if command_name in ('commit_completion', 'insert_best_completion'):
            if settings.get('replace_text_after_commit_completion', True):
                cls._process_replace_text(view, region)
            cls._last_init_completions = []
            cls._last_init_prefix = None
            cls._last_location = None
            logger.debug('cleared completions')

    @classmethod
    def queue_completions(cls, view, location):
        deferred.defer(cls._request_completions,
                       view, cls._event_data(view, location))

    @classmethod
    def hide_completions(cls, view):
        with cls._lock:
            cls._clear_cache()
        view.run_command('hide_auto_complete')

    @classmethod
    def _process_replace_text(cls, view, region):
        inserted_completion, is_snippet = cls._find_inserted_completion(view)

        if inserted_completion and not is_snippet:
            inserted_text = inserted_completion['snippet']['text']
            replace_begin = inserted_completion['replace']['begin']

            logger.debug('inserted {} / {} -> {}:\n{}'
                         .format(cls._last_init_prefix, cls._last_prefix,
                                 inserted_text,
                                 cls._completion_str(inserted_completion)))

            in_buffer = _get_view_substr(view, replace_begin,
                                         replace_begin + len(inserted_text))

            if inserted_text == in_buffer:
                cls._process_matched_replace_text(view, region,
                                                  inserted_completion)
            else:
                cls._process_unmatched_replace_text(view, region,
                                                    inserted_completion)

        elif inserted_completion and is_snippet:
            replace = inserted_completion['post_commit']['replace']
            view.run_command('kite_view_erase', {
                'range': (replace['begin'], replace['end']),
            })

        else:
            logger.debug('no matching completion')

    @classmethod
    def _process_matched_replace_text(cls, view, region, inserted):
        inserted_text = inserted['snippet']['text']

        word_region = view.word(region.b)
        word = _get_view_substr(view, word_region.a, word_region.b)
        logger.debug('word: {}, inserted: {}'.format(word, inserted_text))
        if word == inserted_text:
            logger.debug('word matches, nothing to do!')
            return

        replace_begin = inserted['replace']['begin']
        replace_end = inserted['replace']['end']

        chars_to_trim = replace_end - replace_begin
        leftover_chars = chars_to_trim - \
            (cls._last_location - cls._last_init_location) - \
            len(cls._last_init_prefix)

        logger.debug('chars to trim: {}, leftover: {}'
                     .format(chars_to_trim, leftover_chars))

        if leftover_chars > 0:
            logger.debug('trimming: {}'
                         .format(_get_view_substr(view, region.b,
                                                  region.b + leftover_chars)))

            view.run_command('kite_view_erase', {
                'range': (region.b, region.b + leftover_chars),
            })

    @classmethod
    def _process_unmatched_replace_text(cls, view, region, inserted):
        inserted_text = inserted['snippet']['text']
        replace_begin = inserted['replace']['begin']
        replace_end = inserted['replace']['end']

        chars_to_trim = replace_end - replace_begin - len(cls._last_prefix)
        trim_before = (replace_begin, region.b - len(inserted_text))
        trimmed = trim_before[1] - trim_before[0]
        rem_chars = chars_to_trim - trimmed
        trim_after = (region.b, region.b + rem_chars)

        logger.debug('trim before {} = {}'
                     .format(trim_before,
                             _get_view_substr(view, trim_before[0],
                                              trim_before[1])))

        logger.debug('trim after {} = {}'
                     .format(trim_after,
                             _get_view_substr(view, trim_after[0],
                                              trim_after[1])))

        # This is a hack that handles the situation when dict keys are inserted
        # from an attribute expression. In this case, the typed out attribute
        # is already completely replaced by the index expression, so the only
        # character that needs to be trimmed is the leading ".".
        before_str = _get_view_substr(view, trim_before[0], trim_before[1])
        attr_to_dict_key = (before_str == '.' and inserted_text[0] == '['
                            and inserted_text[-1] == ']')

        view.run_command('kite_view_erase', {'range': trim_before})
        if not attr_to_dict_key:
            view.run_command('kite_view_erase', {
                'range': (trim_after[0] - trimmed, trim_after[1] - trimmed),
            })

    @classmethod
    def _find_inserted_completion(cls, view):
        if len(view.sel()) != 1:
            return None

        region = view.sel()[0]
        is_snippet = not region.empty()

        def _search(_completions):
            candidates = []
            for _c in _completions:
                text = _c['snippet']['text']
                in_buffer = _get_view_substr(view, region.a - len(text),
                                             region.a)
                if in_buffer == text:
                    candidates.append(_c)
                if 'children' in _c:
                    candidates.extend(_search(_c['children']))
            return candidates

        def _search_snippet(_completions):
            candidates = []
            for _c in _completions:
                if 'post_commit' not in _c:
                    continue
                buffer = _c['post_commit']['buffer']
                text = buffer['text']
                in_buffer = _get_view_substr(view, buffer['start'],
                                             buffer['end'])
                logger.debug('comparing {} to {}'.format(text, in_buffer))
                if in_buffer == text:
                    candidates.append(_c)
                if 'children' in _c:
                    candidates.extend(_search_snippet(_c['children']))
            return candidates

        completions = (_search(cls._last_received_completions) if not is_snippet
                       else _search_snippet(cls._last_received_completions))
        logger.debug('possible matched completions: {}'
                     .format(cls._completions_str(completions)))

        longest = None
        for i, c in enumerate(completions):
            if longest is None:
                longest = c
            elif len(c['snippet']['text']) > len(longest['snippet']['text']):
                longest = c

        return longest, is_snippet

    @staticmethod
    def _is_snippets_enabled():
        return settings.get('enable_snippets', True)

    @classmethod
    def _request_completions(cls, view, data):
        logger.debug('fetching completions')
        resp, body = requests.kited_post('/clientapi/editor/complete', data)

        if resp.status != 200 or not body:
            logger.debug('no completions!')
            return

        resp_data = json.loads(body.decode('utf-8'))
        completions = resp_data['completions'] or []
        logger.debug('received completions: {}'
                     .format(cls._completions_str(completions,
                                                  display_only=True)))
        with cls._lock:
            cls._last_received_completions = completions
            cls._last_location = data['position']['end']
            cls._augment_completions_replace(view, cls._last_location,
                                             cls._last_received_completions)

        # Setting the last prefix inside the lock seems to hang on Linux and
        # Windows so we do it outside. Using Sublime's view API inside the
        # lock may be the reason.
        cls._last_prefix = _get_word(view, data['position']['end'])
        cls._last_trigger_char = _get_view_substr(view,
                                                  data['position']['end'] - 1,
                                                  data['position']['end'])
        logger.debug('last trigger char: "{}"'.format(cls._last_trigger_char))

        cls._run_auto_complete(view)

    @classmethod
    def _augment_completions_replace(cls, view, position, completions):
        for c in completions:
            begin = c['replace']['begin']
            end = c['replace']['end']
            text = c['snippet']['text']
            n = len(text)

            if begin >= position and end > begin:
                c['post_commit'] = {
                    'replace': {
                        'begin': begin + n,
                        'end': end + n,
                    },
                    'buffer': {
                        'start': position,
                        'end': position + n + end - begin,
                        'text': '{}{}'.format(text,
                                              _get_view_substr(view, begin,
                                                               end)),
                    },
                }

    @classmethod
    def _run_auto_complete(cls, view):
        # Don't refresh if Kite doesn't have completions. Sublime will
        # filter the completions for us automatically. Note that Sublime
        # performs fuzzy matching so it is possible that Kite will suggest
        # completions that aren't exactly prefix matched.
        with cls._lock:
            if len(cls._last_received_completions) == 0:
                logger.debug('nothing to do: no new completions')
                return

        # It seems like the `auto_complete` command does not always result in
        # `on_query_completions` from being triggered if a completion list is
        # currently shown, so we need to hide it first.
        #
        # However, we only need to refresh the completions UI if the incoming
        # completions contain any completions that were not in the previous
        # list. Otherwise, Sublime will filter the UI automatically.
        #
        # We also need to force the completions UI to show when the user
        # types a space, because Sublime will hide the completions otherwise.
        if not cls._is_completions_subset() or cls._last_trigger_char == ' ':
            view.run_command('hide_auto_complete')
            view.run_command('auto_complete', {
                'api_completions_only': True,
                'disable_auto_insert': True,
                'next_completion_if_showing': False,
            })
        else:
            logger.debug('nothing to do: completions are subset')

    @classmethod
    def _is_completions_subset(cls):
        with cls._lock:
            # both sets of completions are in the Kite's original data format
            previous = cls._flatten_completions(cls._last_init_completions)
            current = cls._flatten_completions(cls._last_received_completions)

        if len(previous) == 0 or len(current) > len(previous):
            return False

        for index, item in enumerate(current):
            if not any((cls._completions_equal(item, prev_item)
                        for prev_item in previous)):
                return False

        return True

    @classmethod
    def _clear_cache(cls):
        cls._last_location = None
        cls._last_prefix = None
        cls._last_trigger_char = None
        cls._last_received_completions = []
        cls._last_init_location = None
        cls._last_init_prefix = None
        cls._last_init_completions = []

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
            placeholders = completion['snippet']['placeholders'] or []
            # sort placeholders in reverse order for easier string patching
            # we assume that placeholders do not overlap
            copy = sorted(placeholders, key=lambda i: i['begin'], reverse=True)
            for p in copy:
                a, b = p['begin'], p['end']
                # +1 because $0 is the last placeholder
                index = placeholders.index(p) + 1
                text = text[:a] + "${{{}:{}}}".format(index, text[a:b]) \
                    + text[b:]
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
            'offset_encoding': 'utf-32',
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

    @staticmethod
    def _prune_completion(completion, display_only=False):
        if not display_only:
            fields = ('snippet', 'replace', 'display', 'post_commit')
            return {k: completion.get(k, None) for k in fields}
        else:
            return completion.get('display', None)

    @classmethod
    def _completions_str(cls, completions, display_only=False):
        def _help(completions, nesting=0):
            if not completions:
                return []

            result = []
            for c in completions:
                # We were previously using _is_snippets_enabled to branch on
                # old/new logic, but it appears that sometimes this check fails
                # so we need handle each completion item individually.
                #
                # See: https://rollbar.com/Kite/sublime-prod/items/14275/
                if 'snippet' not in c:
                    result.append(cls._prune_completion(c, display_only))
                else:
                    result.append(cls._prune_completion(c, display_only))
                    if 'children' in c:
                        result.extend(_help(c['children'], nesting + 1))

            return result

        return logger.jsonstr(_help(completions))

    @classmethod
    def _completion_str(cls, completion):
        return logger.jsonstr(cls._prune_completion(completion))


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

            refs = []
            try:
                # It seems like this function was removed at some point. It
                # still works on some installations of Sublime 3 though.
                #
                # See: https://rollbar.com/Kite/sublime-prod/items/22783/
                refs = window.lookup_references_in_index(symbol['name'])
            except AttributeError:
                pass

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


class MaxFileSizeUpdater(sublime_plugin.EventListener):
    """Listener which updates MAX_FILE_SIZE when a file is focused
    """

    def on_activated(self, view):
        deferred.defer(self.__class__._handle, view)

    @classmethod
    def _handle(cls, view):
        try:
            resp, body = requests.kited_get(
                '/clientapi/settings/max_file_size_kb')
            if resp.status == 200 and body:
                max_file_size_kb = json.loads(body.decode('utf-8'))
                MAX_FILE_SIZE = max_file_size_kb << 10
        except:
            pass
