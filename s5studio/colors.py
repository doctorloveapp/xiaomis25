"""Shared representation of an explicitly absent fill color."""
import re
from PIL import ImageColor

NO_COLOR='none'


def valid_color(value):
    return isinstance(value,str) and (value==NO_COLOR or re.fullmatch(r'#[a-fA-F0-9]{6}',value) is not None)


def color_rgba(value,opacity=255):
    return (0,0,0,0) if value==NO_COLOR else (*ImageColor.getrgb(value),opacity)
