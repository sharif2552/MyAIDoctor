# Minimal streamlit shim used only for local smoke tests / demo mode.
from contextlib import contextmanager

class SessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

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


def button(label, use_container_width=False):
    return False


def form_submit_button(label, use_container_width=False):
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


# Provide a sidebar object with context manager
class _Sidebar:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return False


sidebar = _Sidebar()


import sys

# Minimal st object alias: set attributes on this module object so `import streamlit as st` works.
_mod = sys.modules[__name__]
setattr(_mod, "set_page_config", set_page_config)
setattr(_mod, "markdown", markdown)
setattr(_mod, "button", button)
setattr(_mod, "form", form)
setattr(_mod, "text_area", text_area)
setattr(_mod, "text_input", text_input)
setattr(_mod, "columns", columns)
setattr(_mod, "spinner", spinner)
setattr(_mod, "rerun", rerun)
setattr(_mod, "cache_resource", cache_resource)
setattr(_mod, "session_state", session_state)
setattr(_mod, "sidebar", sidebar)
