from nicegui import ui

from app.components.layout import app_shell, bottom_nav, screen_container
from app.core.roles import ADMIN_ROLE
from app.core.session import get_current_role, get_current_user, has_any_role
from app.guards.role_guard import require_roles
from app.services.admin_analytics_service import analytics_service
from app.theme import register_theme


GREEN = '#0B8A66'
MINT = '#6BE6A8'
PURPLE = '#6D63D6'
AMBER = '#EFC28B'
MUTED = '#6E7687'
TEXT = '#1D2433'
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


def line_trend_options(daily_trend: list[dict]) -> dict:
    days = [item['day'] for item in daily_trend]
    values = [item['score'] for item in daily_trend]

    return {
        'backgroundColor': 'transparent',
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': 40, 'right': 18, 'top': 30, 'bottom': 28},
        'xAxis': {
            'type': 'category',
            'boundaryGap': False,
            'data': days,
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
            'data': values,
        }],
    }


def trigger_bar_options(triggers: list[dict]) -> dict:
    labels = [item['label'] for item in triggers]
    values = [item['value'] for item in triggers]

    return {
        'backgroundColor': 'transparent',
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': 72, 'right': 18, 'top': 24, 'bottom': 30},
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


def heatmap_options(heatmap: dict) -> dict:
    return {
        'backgroundColor': 'transparent',
        'tooltip': {'position': 'top'},
        'grid': {'left': 54, 'right': 18, 'top': 20, 'bottom': 28},
        'xAxis': {
            'type': 'category',
            'data': heatmap['hours'],
            'splitArea': {'show': True},
            'axisLine': {'show': False},
            'axisLabel': {'color': MUTED},
        },
        'yAxis': {
            'type': 'category',
            'data': heatmap['days'],
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
            'data': heatmap['values'],
            'label': {'show': False},
            'emphasis': {'itemStyle': {'shadowBlur': 10, 'shadowColor': 'rgba(0,0,0,0.12)'}},
        }],
    }


def radar_options(profile: dict) -> dict:
    return {
        'backgroundColor': 'transparent',
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
                'value': profile['values'],
                'name': 'Cohort profile',
                'areaStyle': {'color': 'rgba(109,99,214,0.18)'},
                'lineStyle': {'color': PURPLE, 'width': 3},
                'itemStyle': {'color': PURPLE},
            }]
        }],
    }


def recommendation_pie_options(recommendations: list[dict]) -> dict:
    return {
        'backgroundColor': 'transparent',
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
            'data': [{'value': item['value'], 'name': item['label']} for item in recommendations],
            'color': [GREEN, PURPLE, AMBER, '#A6B1C2'],
        }],
    }


def node_health_options(nodes: list[dict]) -> dict:
    return {
        'backgroundColor': 'transparent',
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': 42, 'right': 18, 'top': 20, 'bottom': 28},
        'xAxis': {
            'type': 'category',
            'data': [node['name'] for node in nodes],
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
            'data': [node['health'] for node in nodes],
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

    analytics_state = {'data': analytics_service.get_dashboard_data()}

    def refresh_dashboard():
        analytics_state['data'] = analytics_service.get_dashboard_data()
        render_dashboard.refresh()
        ui.notify('Analytics refreshed', color='positive')

    auto_refresh_timer = ui.timer(8.0, refresh_dashboard, active=False)

    @ui.refreshable
    def render_dashboard():
        data = analytics_state['data']
        overview = data['overview']
        trends = data['trends']
        triggers = data['triggers']
        profile = data['cohort_profile']
        cohort_cards = data['cohort_cards']
        recommendations = data['recommendations']
        recent_alerts = data['recent_alerts']
        federated_status = data['federated_status']

        with ui.element('div').classes('nm-admin-grid-3 mt-6'):
            kpi_card('Active sessions', str(overview['active_sessions']), 'Shared mock analytics scope', 'groups')
            kpi_card('Average stress', str(overview['avg_stress_score']), 'Aggregated across check-in events', 'monitor_heart')
            kpi_card('Support flags', str(overview['support_flags']), 'Isolation / no calm space / shutdown / high stress', 'shield')

        with ui.element('div').classes('grid grid-cols-1 xl:grid-cols-[1.18fr_0.82fr] gap-8 mt-6 items-start'):
            # LEFT COLUMN
            with ui.column().classes('w-full gap-5'):
                with ui.element('div').classes('nm-admin-grid-2'):
                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Daily stress trend').classes('nm-admin-chart-title')
                        ui.label('Average stress score by weekday').classes('nm-admin-chart-subtitle')
                        ui.echart(line_trend_options(trends['daily_trend']), renderer='svg').classes('nm-admin-chart')

                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Dominant triggers').classes('nm-admin-chart-title')
                        ui.label('Weighted distribution from contextual + physiological + behavioral parameters').classes('nm-admin-chart-subtitle')
                        ui.echart(trigger_bar_options(triggers), renderer='svg').classes('nm-admin-chart')

                with ui.element('div').classes('nm-admin-grid-2'):
                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Stress heatmap').classes('nm-admin-chart-title')
                        ui.label('Day × hour hotspots derived from stress scores').classes('nm-admin-chart-subtitle')
                        ui.echart(heatmap_options(trends['heatmap']), renderer='svg').classes('nm-admin-chart')

                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Cohort profile').classes('nm-admin-chart-title')
                        ui.label('Average contextual load across core dimensions').classes('nm-admin-chart-subtitle')
                        ui.echart(radar_options(profile), renderer='svg').classes('nm-admin-chart')

                with ui.element('div').classes('nm-admin-grid-2'):
                    with ui.card().classes('nm-admin-chart-card w-full'):
                        ui.label('Support actions').classes('nm-admin-chart-title')
                        ui.label('Recommended support categories derived from event conditions').classes('nm-admin-chart-subtitle')
                        ui.echart(recommendation_pie_options(recommendations), renderer='svg').classes('nm-admin-chart')

                    if is_admin:
                        with ui.card().classes('nm-admin-chart-card w-full'):
                            ui.label('Edge / MEC node health').classes('nm-admin-chart-title')
                            ui.label('Admin-only mock system health derived from aggregated pressure').classes('nm-admin-chart-subtitle')
                            ui.echart(node_health_options(federated_status['nodes']), renderer='svg').classes('nm-admin-chart')
                    else:
                        with ui.card().classes('nm-admin-card w-full'):
                            ui.label('Admin-only infrastructure').classes('text-xl font-bold text-[#0B4A38]')
                            ui.label(
                                'Node-level system health is hidden for researcher sessions.'
                            ).classes('nm-small mt-2')
                            with ui.card().classes('nm-admin-soft mt-4 shadow-none'):
                                ui.label('Researcher scope').classes('font-semibold text-[#0B4A38]')
                                ui.label(
                                    'This session currently exposes analytics and cohort-level insights only.'
                                ).classes('nm-small mt-1')

            # RIGHT COLUMN
            with ui.column().classes('w-full gap-5'):
                with ui.card().classes('nm-admin-card w-full lg:sticky lg:top-8'):
                    ui.label('Live analytics controls').classes('text-xl font-bold text-[#0B4A38]')
                    ui.label(
                        'The dashboard now re-reads a shared analytics provider instead of generating random values inside the page.'
                    ).classes('nm-small mt-1')

                    with ui.element('div').classes('nm-admin-toolbar'):
                        ui.button(
                            'Refresh analytics',
                            on_click=refresh_dashboard,
                        ).props('unelevated no-caps icon=refresh').classes('nm-primary-btn')

                        auto_switch = ui.switch('Auto refresh', value=False).props('color=primary')
                        auto_switch.bind_value_to(auto_refresh_timer, 'active')

                        with ui.row().classes('nm-admin-live-badge'):
                            ui.icon('dataset')
                            ui.label(f"{data['events_count']} events in shared analytics store")

                    with ui.row().classes('w-full gap-3 mt-5 flex-wrap'):
                        with ui.column().classes('nm-admin-kpi'):
                            ui.label('Current role').classes('nm-admin-kpi-label')
                            ui.label(role.title()).classes('nm-admin-kpi-value')
                            ui.label('Session-derived UI access').classes('nm-admin-kpi-note')

                        with ui.column().classes('nm-admin-kpi'):
                            ui.label('FL round').classes('nm-admin-kpi-label')
                            ui.label(str(federated_status['fl_round'])).classes('nm-admin-kpi-value')
                            ui.label(federated_status['global_model_version']).classes('nm-admin-kpi-note')

                        with ui.column().classes('nm-admin-kpi'):
                            ui.label('Last update').classes('nm-admin-kpi-label')
                            ui.label(overview['last_update'][11:16] if overview['last_update'] else '—').classes('nm-admin-kpi-value')
                            ui.label('Latest aggregated event time').classes('nm-admin-kpi-note')

                    with ui.card().classes('nm-admin-soft mt-5 shadow-none'):
                        ui.label('Cohort metric summary').classes('font-semibold text-[#0B4A38]')
                        ui.label(
                            f"Physiological burden {cohort_cards['physiological_burden']} · "
                            f"Sensory load {cohort_cards['sensory_load']} · "
                            f"Communication friction {cohort_cards['communication_friction']}"
                        ).classes('nm-small mt-1')
                        ui.label(
                            f"Quiet space availability: {cohort_cards['quiet_space_availability']}%"
                        ).classes('nm-small mt-1')

                    with ui.column().classes('w-full gap-4 mt-5'):
                        with ui.card().classes('nm-admin-soft shadow-none'):
                            ui.label('Recent alerts').classes('font-semibold text-[#0B4A38]')
                            if recent_alerts:
                                with ui.column().classes('w-full gap-3 mt-3'):
                                    for alert in recent_alerts:
                                        with ui.card().classes('nm-admin-list-item shadow-none'):
                                            ui.label(alert['title']).classes('font-semibold text-[#0B4A38]')
                                            ui.label(alert['details']).classes('nm-small')
                                            ui.label(alert['time']).classes('text-xs text-[#98A1AF]')
                            else:
                                ui.label('No support flags detected yet.').classes('nm-small mt-2')

                        with ui.card().classes('nm-admin-soft shadow-none'):
                            ui.label('Interpretation note').classes('font-semibold text-[#0B4A38]')
                            ui.label(
                                'This panel now uses aggregated check-in parameters and derived metrics. '
                                'When the backend is ready, the same contract can be fulfilled by backend APIs reading the external DB / MEC aggregation layer.'
                            ).classes('nm-small mt-1')

                    if is_admin:
                        with ui.card().classes('nm-admin-card w-full mt-2'):
                            ui.label('Admin-only tools').classes('text-xl font-bold text-[#0B4A38]')
                            ui.label(
                                'System and lifecycle placeholders reserved for backend-connected admin operations.'
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
                        'Analytics-first panel powered by a shared admin analytics provider.'
                    ).classes('nm-subtitle text-[1.05rem]')
                    ui.label(
                        f"Signed in as {user.get('display_name', 'Unknown')} · role: {role}"
                    ).classes('nm-small mt-2')

                with ui.row().classes('items-center gap-2 flex-wrap'):
                    with ui.row().classes('nm-admin-badge'):
                        ui.icon('shield')
                        ui.label('Role-aware UI')
                    with ui.row().classes('nm-admin-badge'):
                        ui.icon('dataset')
                        ui.label('Shared analytics mock')
                    with ui.row().classes('nm-admin-badge'):
                        ui.icon('hub')
                        ui.label('Backend-ready contract')

        render_dashboard()

        ui.element('div').classes('h-24')
        bottom_nav('admin')