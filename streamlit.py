# Minimal streamlit shim used only for local smoke tests / demo mode.
import sys
from contextlib import contextmanager


class SessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        # allow setting internal attrs
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self[name] = value


session_state = SessionState()


def set_page_config(**kwargs):
    return None


def markdown(*a, **k):
    # no-op for tests
    return None


def _noop(*a, **k):
    return None


def button(label, use_container_width=False, **kwargs):
    return False


def form_submit_button(label, use_container_width=False, **kwargs):
    # Simulate a form submit button; always return False in smoke tests
    return False


def form(key, clear_on_submit=False):
    @contextmanager
    def _ctx():
        yield None
    return _ctx()


def text_area(label, label_visibility=None, placeholder=None, height=None, key=None):
    return ""


def text_input(label, key=None, label_visibility=None, placeholder=None):
    return ""


def columns(spec):
    # Return a simple tuple of dummy column objects that can be used with `with` if needed.
    class _Col:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    return tuple(_Col() for _ in range(len(spec)))


class spinner:
    def __init__(self, msg=""):
        self.msg = msg

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def rerun():
    return None


def cache_resource(func):
    return func


def expander(label, expanded=False):
    @contextmanager
    def _ctx():
        yield None

    return _ctx()


def code(*a, **k):
    return None


def caption(*a, **k):
    return None


def warning(*a, **k):
    return None


# Provide a sidebar object with context manager
class _Sidebar:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


sidebar = _Sidebar()

# Minimal st object alias: set attributes on this module object so `import streamlit as st` works.
_mod = sys.modules[__name__]
_mod.set_page_config = set_page_config
_mod.markdown = markdown
_mod.button = button
_mod.form = form
_mod.text_area = text_area
_mod.text_input = text_input
_mod.columns = columns
_mod.spinner = spinner
_mod.rerun = rerun
_mod.cache_resource = cache_resource
_mod.expander = expander
_mod.code = code
_mod.caption = caption
_mod.warning = warning
_mod.session_state = session_state
_mod.sidebar = sidebar
