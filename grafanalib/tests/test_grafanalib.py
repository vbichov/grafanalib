"""Tests for Grafanalib."""

import grafanalib.core as G
from grafanalib import _gen

import sys, re, json
if sys.version_info[0] < 3:
    from io import BytesIO as StringIO
else:
    from io import StringIO

# TODO: Use Hypothesis to generate a more thorough battery of smoke tests.


def test_serialization():
    """Serializing a graph doesn't explode."""
    graph = G.Graph(
        title="CPU Usage by Namespace (rate[5m])",
        dataSource="My data source",
        targets=[
            G.Target(
                expr='namespace:container_cpu_usage_seconds_total:sum_rate',
                legendFormat='{{namespace}}',
                refId='A',
            ),
        ],
        id=1,
        yAxes=[
            G.YAxis(format=G.SHORT_FORMAT, label="CPU seconds / second"),
            G.YAxis(format=G.SHORT_FORMAT),
        ],
    )
    stream = StringIO()
    _gen.write_dashboard(graph, stream)
    assert stream.getvalue() != ''


def test_auto_id():
    """auto_panel_ids() provides IDs for all panels without IDs already set."""
    dashboard = G.Dashboard(
        title="Test dashboard",
        panels=[
            G.Row(panels=[
                G.Graph(
                    title="CPU Usage by Namespace (rate[5m])",
                    dataSource="My data source",
                    targets=[
                        G.Target(
                            expr='whatever #B',
                            legendFormat='{{namespace}}',
                        ),
                        G.Target(
                            expr='hidden whatever',
                            legendFormat='{{namespace}}',
                            refId='B',
                            hide=True
                        ),
                    ],
                    yAxes=[
                        G.YAxis(format=G.SHORT_FORMAT, label="CPU seconds"),
                        G.YAxis(format=G.SHORT_FORMAT),
                    ],
                )
            ]),
        ],
    ).auto_panel_ids()
    assert dashboard.panels[0].panels[0].id == 1


def test_auto_refids():
    """auto_ref_ids() provides refIds for all targets without refIds already set."""
    dashboard = G.Dashboard(
        title="Test dashboard",
        panels=[
            G.Row(panels=[
                G.Graph(
                    title="CPU Usage by Namespace (rate[5m])",
                    dataSource="My data source",
                    targets=[
                        G.Target(
                            expr='whatever #Q',
                            legendFormat='{{namespace}}',
                        ),
                        G.Target(
                            expr='hidden whatever',
                            legendFormat='{{namespace}}',
                            refId='Q',
                            hide=True
                        ),
                        G.Target(
                            expr='another target'
                        ),
                    ],
                    yAxes=[
                        G.YAxis(format=G.SHORT_FORMAT, label="CPU seconds"),
                        G.YAxis(format=G.SHORT_FORMAT),
                    ],
                ).auto_ref_ids()
            ]),
        ],
    )
    assert dashboard.panels[0].panels[0].targets[0].refId == 'A'
    assert dashboard.panels[0].panels[0].targets[1].refId == 'Q'
    assert dashboard.panels[0].panels[0].targets[2].refId == 'B'


def test_row_show_title():
    row = G.Row().to_json_data()
    assert row[0]['title'] == 'New row'
    assert not row[0]['showTitle']

    row = G.Row(title='My title').to_json_data()
    assert row[0]['title'] == 'My title'
    assert row[0]['showTitle']

    row = G.Row(title='My title', showTitle=False).to_json_data()
    assert row[0]['title'] == 'My title'
    assert not row[0]['showTitle']


def test_graphite_target_full():
    dashboard = G.Graph(
        title="Graphite target full test",
        dataSource="graphite datasource",
        targets=[
            G.GraphiteTarget(
                refId="A",
                target="foo.bar"
            ),
            G.GraphiteTarget(
                refId="B",
                target="sumSeries(#A,foo2.bar2)"
            )
        ]
    )
    dashboard.resolve_graphite_targets()
    for target in dashboard.targets:
        assert target.targetFull != ""
        
        assert not re.findall("#[A-Z]", target.targetFull)

def test_alert_thresholds():
    some_target_for_alert = G.GraphiteTarget( refId="A",target="foo.bar")

    graph = G.Graph(
        title = "Graph with alert",
        targets=[
            some_target_for_alert
        ],
        alert = G.Alert(
                name = "alert name",
                message = "alert message",
                alertConditions = [
                    G.AlertCondition(
                        some_target_for_alert,
                        timeRange=G.TimeRange("5m", "now"),
                        evaluator=G.GreaterThan(10),
                        reducerType=G.RTYPE_MAX,
                        operator=G.OP_AND
                    )
                ]
        )
    )

    stream = StringIO()
    _gen.write_dashboard(graph, stream)
    graph_json = json.loads(stream.getvalue())
    print(graph_json.keys())
    #threre is a threshold
    assert graph_json['thresholds'][0] != None
