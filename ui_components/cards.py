# reusable UI widgets (cards, tables)
from nicegui import ui


def stat_card(label, value, classes=''):
    """Create a statistics card with label and value"""
    with ui.card().classes(f'flex-1 {classes}'):
        ui.label(label).classes('text-h6')
        ui.label(str(value)).classes('text-h4 text-primary')


def chart_card(title, chart_data, chart_type='bar', classes=''):
    """Create a card with an EChart visualization"""
    with ui.card().classes(f'flex-1 {classes}'):
        ui.echart({
            'title': {'text': title},
            'xAxis': {
                'type': 'category',
                'data': list(chart_data.keys()),
                'axisLabel': {
                    'rotate': 45,
                    'interval': 0
                }
            },
            'yAxis': {'type': 'value'},
            'series': [{
                'type': chart_type,
                'data': list(chart_data.values()),
                'label': {
                    'show': True,
                    'position': 'inside',
                    'rotate': 90,
                    'formatter': '{c}'
                }
            }],
            'grid': {
                'bottom': '20%',
                'containLabel': True
            }
        }).classes('w-full').style('min-height: 400px')
