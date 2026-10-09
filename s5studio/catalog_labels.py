"""English display names for Chinese entries in the personal hand catalog."""
import hashlib,re

NAMES={
    '彩色刻度':'Colorful Markers','户外探险家':'Outdoor Explorer',
    '璀璨宝石':'Brilliant Gemstones','粉凝陀飞轮':'Pink Tourbillon',
    '艺术时空':'Artistic Space-Time','轨迹':'Trajectory','雕琢':'Sculpted','黑豹':'Black Panther',
    '三尺设计':'San Chi Design','小米':'Xiaomi',
}


def english(text):
    text=str(text)
    if text in NAMES:return NAMES[text]
    text=re.sub(r'样式\s*(\d+)',r'Style \1',text)
    if re.search(r'[\u3400-\u9fff]',text):
        return 'Custom design '+hashlib.sha256(text.encode('utf8')).hexdigest()[:6]
    return text


def display_preset(preset):
    result=dict(preset)
    for key in ('name','theme','author','variant'):
        original=preset.get(key,'');result[key]=english(original)
        if result[key]!=str(original):result['original'+key.title()]=original
    return result
