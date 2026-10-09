"""English calendar labels for live data; native sources remain numeric.

The supplied S5 faces use dateWeek index 0=SUN through 6=SAT and explicit
dateMonth values 1..12. Only number layers use this presentation.
"""
WEEKDAYS = ('SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT')
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December')


def labels_for(element):
    if element.kind != 'number':
        return {}
    if element.source == 'dateWeek':
        return dict(enumerate(WEEKDAYS))
    if element.source in ('month', 'dateMonth'):
        return dict(enumerate(MONTHS, 1))
    return {}


def sample_label(element, values):
    if element.source == 'dateWeek':
        value = values.get('dateWeek', 1)
    else:
        value = values.get(element.source, values.get('month' if element.source == 'dateMonth' else 'dateMonth'))
    try:
        return labels_for(element).get(int(value), '---')
    except (TypeError, ValueError, OverflowError):
        return '---'
