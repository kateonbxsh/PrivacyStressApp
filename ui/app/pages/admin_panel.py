import random
from statistics import mean

from nicegui import ui

from app.components.layout import app_shell, bottom_nav, screen_container
from app.core.roles import ADMIN_ROLE
from app.core.session import get_current_role, get_current_user, has_any_role
from app.guards.role_guard import require_roles
from app.theme import register_theme


GREEN = '#0B8A66'
GREEN_DARK = '#06684D'
MINT = '#6BE6A8'
PURPLE = '#6D63D6'
AMBER = '#EFC28B'
RED = '#F5B9B6'
TEXT = '#1D2433'
MUTED = '#6E7687'
GRID = 'rgba(17,24,39,0.06)'


def kpi_card(title: str, value: str, subtitle: str, icon: str):
    with ui.card().classes('nm-admin-card w-full'):
        with ui.row().classes('w-full items-start justify-between gap-4'):
            with ui.column().classes('gap-1'):
                ui.label(title).classes('nm-admin-kpi-label')
                ui.label(value).classes('nm-admin-kpi-value')
                ui.label(subtitle).classes('nm-admin-kpi-note')
            with ui.avatar(color='#F1F7F3', text_color='primary').classes('shadow-none'):
                ui.icon(icon)


def info_item(title: str, body: str, icon: str):
    with ui.row().classes('items-start gap-4'):
        with ui.avatar(color='#F1F7F3', text_color='primary').classes('shadow-none mt-1'):
            ui.icon(icon)
        with ui.column().classes('gap-1'):
            ui.label(title).classes('font-semibold text-[#0B4A38]')
            ui.label(body).classes('nm-small')


def generate_mock_state() -> dict:
    daily = [round(random.uniform(0.22, 0.78), 2) for _ in range(7)]
    triggers = {
        'Noise': random.randint(48, 86),
        'Crowd': random.randint(40, 82),
        'Routine': random.randint(30, 72),
        'Social': random.randint(28, 76),
        'Transit': random.randint(22, 64),
    }
    heatmap = []
    for day in range(7):
        for hour in range(8):
            base = random.randint(0, 2)
            if hour in (3, 4):   # midday / early afternoon
                base += random.randint(1, 3)
            if day in (2, 3, 4):  # mid-week slightly more intense
                base += random.randint(0, 1)
            heatmap.append([hour, day, min(base, 5)])

    radar = [
        random.randint(42, 84),  # Noise
        random.randint(35, 72),  # Light
        random.randint(38, 83),  # Crowd
        random.randint(30, 77),  # Routine
        random.randint(34, 79),  # Social
        random.randint(24, 68),  # Transit
    ]

    recommendations = {
        'Quiet place': random.randint(24, 48),
        'Short pause': random.randint(16, 38),
        'Breathing': random.randint(10, 28),
        'Trusted contact': random.randint(6, 20),
    }

    node_health = [random.randint(76, 99) for _ in range(5)]

    sessions = random.randint(18, 34)
    avg_stress = round(mean(daily), 2)
    support_flags = random.randint(4, 12)

    return {
        'daily': daily,
        'triggers': triggers,
        'heatmap': heatmap,
        'radar': radar,
        'recommendations': recommendations,
        'node_health': node_health,
        'sessions': sessions,
        'avg_stress': avg_stress,
        'support_flags': support_flags,
        'peak_trigger': max(triggers, key=triggers.get),
        'dominant_recommendation': max(recommendations, key=recommendations.get),
    }


def line_trend_options(data: list[float]) -> dict:
    return {
        'backgroundColor': 'transparent',
        'animationDuration': 500,
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': 40, 'right': 18, 'top': 30, 'bottom': 28},
        'xAxis': {
            'type': 'category',
            'boundaryGap': False,
            'data': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'axisLine': {'lineStyle': {'color': GRID}},
            'axisLabel': {'color': MUTED},
        },
        'yAxis': {
            'type': 'value',
            'min': 0,
            'max': 1,
            'splitLine': {'lineStyle': {'color': GRID}},
            'axisLine': {'show': False},
            'axisLabel': {'color': MUTED},
        },
        'series': [{
            'type': 'line',
            'smooth': True,
            'symbol': 'circle',
            'symbolSize': 8,
            'lineStyle': {'width': 4, 'color': GREEN},
            'itemStyle': {'color': GREEN},
            'areaStyle': {
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                    'colorStops': [
                        {'offset': 0, 'color': 'rgba(11,138,102,0.28)'},
                        {'offset': 1, 'color': 'rgba(11,138,102,0.03)'},
                    ],
                }
            },
            'data': data,
        }],
    }


def trigger_bar_options(data: dict[str, int]) -> dict:
    labels = list(data.keys())
    values = list(data.values())
    return {
        'backgroundColor': 'transparent',
        'animationDuration': 500,
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': 58, 'right': 18, 'top': 24, 'bottom': 30},
        'xAxis': {
            'type': 'value',
            'axisLine': {'show': False},
            'splitLine': {'lineStyle': {'color': GRID}},
            'axisLabel': {'color': MUTED},
        },
        'yAxis': {
            'type': 'category',
            'data': labels,
            'inverse': True,
            'axisLine': {'show': False},
            'axisTick': {'show': False},
            'axisLabel': {'color': TEXT},
        },
        'series': [{
            'type': 'bar',
            'barWidth': 14,
            'data': values,
            'itemStyle': {
                'borderRadius': [0, 12, 12, 0],
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 0, 'x2': 1, 'y2': 0,
                    'colorStops': [
                        {'offset': 0, 'color': GREEN},
                        {'offset': 1, 'color': MINT},
                    ],
                },
            },
        }],
    }


def heatmap_options(raw: list[list[int]]) -> dict:
    hours = ['06', '08', '10', '12', '14', '16', '18', '20']
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return {
        'backgroundColor': 'transparent',
        'animationDuration': 500,
        'tooltip': {'position': 'top'},
        'grid': {'left': 54, 'right': 18, 'top': 20, 'bottom': 28},
        'xAxis': {
            'type': 'category',
            'data': hours,
            'splitArea': {'show': True},
            'axisLine': {'show': False},
            'axisLabel': {'color': MUTED},
        },
        'yAxis': {
            'type': 'category',
            'data': days,
            'splitArea': {'show': True},
            'axisLine': {'show': False},
            'axisLabel': {'color': MUTED},
        },
        'visualMap': {
            'min': 0,
            'max': 5,
            'calculable': False,
            'orient': 'horizontal',
            'left': 'center',
            'bottom': 0,
            'textStyle': {'color': MUTED},
            'inRange': {
                'color': ['#F4FAF6', '#DDF6E8', '#BDF0D1', '#87E5B0', '#4DCB87', '#0B8A66'],
            },
        },
        'series': [{
            'name': 'Stress hotspots',
            'type': 'heatmap',
            'data': raw,
            'label': {'show': False},
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0,0,0,0.12)'}},
        }],
    }


def radar_options(values: list[int]) -> dict:
    return {
        'backgroundColor': 'transparent',
        'animationDuration': 500,
        'legend': {'show': False},
        'radar': {
            'radius': '68%',
            'indicator': [
                {'name': 'Noise', 'max': 100},
                {'name': 'Light', 'max': 100},
                {'name': 'Crowd', 'max': 100},
                {'name': 'Routine', 'max': 100},
                {'name': 'Social', 'max': 100},
                {'name': 'Transit', 'max': 100},
            ],
            'axisName': {'color': MUTED},
            'splitLine': {'lineStyle': {'color': GRID}},
            'splitArea': {'areaStyle': {'color': ['transparent']}},
            'axisLine': {'lineStyle': {'color': GRID}},
        },
        'series': [{
            'type': 'radar',
            'data': [{
                'value': values,
                'name': 'Cohort A',
                'areaStyle': {'color': 'rgba(109,99,214,0.18)'},
                'lineStyle': {'color': PURPLE, 'width': 3},
                'itemStyle': {'color': PURPLE},
            }]
        }],
    }


def pie_options(data: dict[str, int]) -> dict:
    pie_data = [{'value': value, 'name': key} for key, value in data.items()]
    return {
        'backgroundColor': 'transparent',
        'animationDuration': 500,
        'tooltip': {'trigger': 'item'},
        'legend': {
            'bottom': 0,
            'left': 'center',
            'textStyle': {'color': MUTED},
        },
        'series': [{
            'type': 'pie',
            'radius': ['52%', '76%'],
            'center': ['50%', '44%'],
            'avoidLabelOverlap': False,
            'itemStyle': {'borderRadius': 10, 'borderColor': '#fff', 'borderWidth': 4},
            'label': {'show': False},
            'data': pie_data,
            'color': [GREEN, PURPLE, AMBER, '#A6B1C2'],
        }],
    }


def node_health_options(values: list[int]) -> dict:
    return {
        'backgroundColor': 'transparent',
        'animationDuration': 500,
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': 42, 'right': 18, 'top': 20, 'bottom': 28},
        'xAxis': {
            'type': 'category',
            'data': ['Node A', 'Node B', 'Node C', 'Node D', 'Node E'],
            'axisLabel': {'color': MUTED},
            'axisLine': {'lineStyle': {'color': GRID}},
        },
        'yAxis': {
            'type': 'value',
            'max': 100,
            'axisLabel': {'color': MUTED},
            'splitLine': {'lineStyle': {'color': GRID}},
        },
        'series': [{
            'type': 'bar',
            'barWidth': 20,
            'data': values,
            'itemStyle': {
                'borderRadius': [10, 10, 0, 0],
                'color': {
                    'type': 'linear',
                    'x': 0, 'y': 1, 'x2': 0, 'y2': 0,
                    'colorStops': [
                        {'offset': 0, 'color': GREEN},
                        {'offset': 1, 'color': MINT},
                    ],
                },
            },
        }],
    }


@ui.page('/admin')
def admin_panel_page() -> None:
    register_theme()
    if not require_roles('researcher', 'admin'):
        return

    ui.element('div').classes('nm-hero-blur')

    user = get_current_user() or {}
    role = get_current_role()
    is_admin = has_any_role(ADMIN_ROLE)

    analytics_state = {'data': generate_mock_state()}

    def refresh_analytics():
        analytics_state['data'] = generate_mock_state()
        render_dashboard.refresh()
        ui.notify('Mock analytics refreshed', color='positive')

    auto_refresh_timer = ui.timer(8.0, refresh_analytics, active=False)

    @ui.refreshable
    def render_dashboard():
        data = analytics_state['data']

        with ui.element('div').classes('nm-admin-grid-3 mt-6'):
            kpi_card('Active sessions', str(data['sessions']), 'Mock current sessions', 'groups')
            kpi_card('Average stress', f"{data['avg_stress']}", 'Rolling mock score', 'monitor_heart')
            kpi_card('Support flags', str(data['support_flags']), 'Quiet-space / recovery prompts', 'shield')

        with ui.element('div').classes('grid grid-cols-1 xl:grid-cols-[1.18fr_0.82fr] gap-8 mt-6 items-start'):
            # LEFT COLUMN = charts
            with ui.column().classes('w-full gap-5'):
                with ui.element('div').classes('nm-admin-grid-2'):
                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Daily stress trend').classes('nm-admin-chart-title')
                        ui.label('Mock rolling score across the week').classes('nm-admin-chart-subtitle')
                        ui.echart(line_trend_options(data['daily']), renderer='svg').classes('nm-admin-chart')

                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Main triggers').classes('nm-admin-chart-title')
                        ui.label('Most frequent contextual contributors').classes('nm-admin-chart-subtitle')
                        ui.echart(trigger_bar_options(data['triggers']), renderer='svg').classes('nm-admin-chart')

                with ui.element('div').classes('nm-admin-grid-2'):
                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Stress heatmap').classes('nm-admin-chart-title')
                        ui.label('Hotspots by day and time window').classes('nm-admin-chart-subtitle')
                        ui.echart(heatmap_options(data['heatmap']), renderer='svg').classes('nm-admin-chart')

                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Cohort pattern profile').classes('nm-admin-chart-title')
                        ui.label('Mock sensory / social profile for a cohort').classes('nm-admin-chart-subtitle')
                        ui.echart(radar_options(data['radar']), renderer='svg').classes('nm-admin-chart')

                with ui.element('div').classes('nm-admin-grid-2'):
                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Recommended actions').classes('nm-admin-chart-title')
                        ui.label('Distribution of top recovery prompts').classes('nm-admin-chart-subtitle')
                        ui.echart(pie_options(data['recommendations']), renderer='svg').classes('nm-admin-chart')

                    if is_admin:
                        with ui.card().classes('nm-admin-chart-card w-full'):
                            ui.label('Edge node health').classes('nm-admin-chart-title')
                            ui.label('Admin-only mock infrastructure status').classes('nm-admin-chart-subtitle')
                            ui.echart(node_health_options(data['node_health']), renderer='svg').classes('nm-admin-chart')
                    else:
                        with ui.card().classes('nm-admin-card w-full'):
                            ui.label('Admin-only infrastructure').classes('text-xl font-bold text-[#0B4A38]')
                            ui.label(
                                'System and node health panels are hidden for researcher sessions.'
                            ).classes('nm-small mt-2')
                            with ui.card().classes('nm-admin-soft mt-4 shadow-none'):
                                ui.label('Researcher scope').classes('font-semibold text-[#0B4A38]')
                                ui.label(
                                    'You currently see analytics and cohort-level insights only.'
                                ).classes('nm-small mt-1')

            # RIGHT COLUMN = side insights
            with ui.column().classes('w-full gap-5'):
                with ui.card().classes('nm-admin-card w-full lg:sticky lg:top-8'):
                    ui.label('Live analytics controls').classes('text-xl font-bold text-[#0B4A38]')
                    ui.label(
                        'Use manual or automatic refresh to simulate a living dashboard.'
                    ).classes('nm-small mt-1')

                    with ui.element('div').classes('nm-admin-toolbar'):
                        ui.button(
                            'Refresh mock analytics',
                            on_click=refresh_analytics,
                        ).props('unelevated no-caps icon=refresh').classes('nm-primary-btn')

                        auto_switch = ui.switch('Auto refresh', value=False).props('color=primary')
                        auto_switch.bind_value_to(auto_refresh_timer, 'active')

                        with ui.row().classes('nm-admin-live-badge'):
                            ui.icon('bolt')
                            ui.label('Mock live mode')

                    with ui.row().classes('w-full gap-3 mt-5 flex-wrap'):
                        with ui.column().classes('nm-admin-kpi'):
                            ui.label('Current role').classes('nm-admin-kpi-label')
                            ui.label(role.title()).classes('nm-admin-kpi-value')
                            ui.label('Session-derived').classes('nm-admin-kpi-note')

                        with ui.column().classes('nm-admin-kpi'):
                            ui.label('Peak trigger').classes('nm-admin-kpi-label')
                            ui.label(data['peak_trigger']).classes('nm-admin-kpi-value')
                            ui.label('Most intense current factor').classes('nm-admin-kpi-note')

                        with ui.column().classes('nm-admin-kpi'):
                            ui.label('Top action').classes('nm-admin-kpi-label')
                            ui.label(data['dominant_recommendation']).classes('nm-admin-kpi-value')
                            ui.label('Most suggested support path').classes('nm-admin-kpi-note')

                    with ui.card().classes('nm-admin-soft mt-5 shadow-none'):
                        ui.label('Cohort summary').classes('font-semibold text-[#0B4A38]')
                        ui.label(
                            f"Average stress is currently {data['avg_stress']}, with {data['peak_trigger']} as the strongest mock trigger."
                        ).classes('nm-small mt-1')

                    with ui.column().classes('w-full gap-4 mt-5'):
                        with ui.card().classes('nm-admin-soft shadow-none'):
                            info_item(
                                'Most frequent trigger pair',
                                f"{data['peak_trigger']} often appears alongside social and routine-related load in the mock set.",
                                'volume_up',
                            )
                        with ui.card().classes('nm-admin-soft shadow-none'):
                            info_item(
                                'Most common support strategy',
                                f"{data['dominant_recommendation']} currently dominates the recommendation mix.",
                                'self_improvement',
                            )
                        with ui.card().classes('nm-admin-soft shadow-none'):
                            info_item(
                                'Privacy note',
                                'This panel should later use only aggregated or anonymized backend results.',
                                'privacy_tip',
                            )

                    if is_admin:
                        with ui.card().classes('nm-admin-card w-full mt-2'):
                            ui.label('Admin-only tools').classes('text-xl font-bold text-[#0B4A38]')
                            ui.label(
                                'System operations, audit, and user lifecycle placeholders.'
                            ).classes('nm-small mt-1')

                            with ui.column().classes('w-full gap-3 mt-4'):
                                with ui.card().classes('nm-admin-list-item shadow-none'):
                                    ui.label('User management').classes('font-semibold text-[#0B4A38]')
                                    ui.label('Placeholder for user list, roles, and access lifecycle.').classes('nm-small')
                                with ui.card().classes('nm-admin-list-item shadow-none'):
                                    ui.label('Audit & compliance').classes('font-semibold text-[#0B4A38]')
                                    ui.label('Placeholder for model usage logs and access history.').classes('nm-small')
                                with ui.card().classes('nm-admin-list-item shadow-none'):
                                    ui.label('Feature flags / deployment').classes('font-semibold text-[#0B4A38]')
                                    ui.label('Placeholder for rollout toggles and service health.').classes('nm-small')

    with screen_container():
        app_shell(active='admin')

        with ui.card().classes('nm-admin-hero w-full mt-6'):
            with ui.row().classes('w-full items-start justify-between gap-4 flex-wrap'):
                with ui.column().classes('gap-1'):
                    ui.label('Admin Panel').classes('nm-page-title text-left')
                    ui.label(
                        'Research analytics, anonymized patterns, and system visibility.'
                    ).classes('nm-subtitle text-[1.05rem]')
                    ui.label(
                        f"Signed in as {user.get('display_name', 'Unknown')} · role: {role}"
                    ).classes('nm-small mt-2')

                with ui.row().classes('items-center gap-2 flex-wrap'):
                    with ui.row().classes('nm-admin-badge'):
                        ui.icon('shield')
                        ui.label('Role-aware UI')
                    with ui.row().classes('nm-admin-badge'):
                        ui.icon('insights')
                        ui.label('Analytics-ready')
                    with ui.row().classes('nm-admin-badge'):
                        ui.icon('hub')
                        ui.label('FL-ready')

        render_dashboard()

        ui.element('div').classes('h-24')
        bottom_nav('admin')