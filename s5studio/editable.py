"""Compatibility helpers for reading observed native containers.

Editable export is built by native_graph; no Suit and tie groups are grafted.
"""
import struct
from .watchface_library import read_tables

def tables(data,screen=0):
    return read_tables(data,screen)

def preview_blob(data):
    pos=struct.unpack_from('<I',data,32)[0]
    if pos<168 or pos+12>len(data):raise ValueError('Anteprima binaria mancante.')
    length=12+struct.unpack_from('<I',data,pos+8)[0]
    if pos+length>len(data):raise ValueError('Anteprima binaria troncata.')
    return data[pos:pos+length]

