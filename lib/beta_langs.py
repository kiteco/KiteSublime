import sublime
from ..lib import settings, app_controller, requests 
from ..lib.link_opener import open_copilot_root
from ..lib.languages import Languages, Extensions, ext_to_lang, kited_ext_enabled

_BETA_EXTS = (Extensions.GO, Extensions.JS, Extensions.JSX, Extensions.VUE)

_LANG_TO_SHOW_NOTIF_KEY = {
  Languages.GO: "show_go_beta_notif", 
  Languages.JAVASCRIPT: "show_javascript_beta_notif",
}

def should_show_notif(ext):
  if ext not in _BETA_EXTS:
    return False
  
  show_notif_key = _LANG_TO_SHOW_NOTIF_KEY[ext_to_lang(ext)]
  return settings.get(show_notif_key, default=True) and kited_ext_enabled(ext)

def show_notif(ext):
  lang = ext_to_lang(ext)
  msg = (
    "Welcome to Kite for "+lang+" Beta!\n\n" +
    "You\'ve got access to our line-of-code completions for "+lang+", " +
    "powered by machine learning. If you'd like to disable beta, " +
    "you can do so in the Copilot" 
  )
  
  res = sublime.yes_no_cancel_dialog(msg, yes_title="Hide Forever", no_title="Open Copilot")
  if res == sublime.DIALOG_NO:
    app_controller.launch_kite_if_not_running()
    open_copilot_root('')
  
  settings.set(_LANG_TO_SHOW_NOTIF_KEY[lang], False)
