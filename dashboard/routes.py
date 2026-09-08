from datetime import datetime
from typing import List, Optional


def get_dashboard_html(
    total_calls: int,
    resolution_rate: float,
    escalation_rate: float,
    avg_turns: float,
    recent_calls: List,
) -> str:
    """Generate dashboard HTML with metrics."""

    recent_calls_html = ""
    for call in recent_calls:
        recent_calls_html += f"""
        <tr>
            <td class="call-id">{call.call_id[:12]}...</td>
            <td>{call.intent or "N/A"}</td>
            <td>{call.turn_count}</td>
            <td><span class="status {call.resolution_status.lower()}">{call.resolution_status.upper()}</span></td>
            <td>{call.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dental Clinic AI Agent - Dashboard</title>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}

            header {{
                background: white;
                border-radius: 12px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}

            header h1 {{
                color: #2d3748;
                margin-bottom: 10px;
                font-size: 28px;
            }}

            header p {{
                color: #718096;
                font-size: 14px;
            }}

            .metrics-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .metric-card {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                transition: transform 0.2s, box-shadow 0.2s;
            }}

            .metric-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
            }}

            .metric-label {{
                color: #718096;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 8px;
            }}

            .metric-value {{
                color: #2d3748;
                font-size: 32px;
                font-weight: bold;
            }}

            .metric-unit {{
                color: #a0aec0;
                font-size: 16px;
                margin-left: 5px;
            }}

            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .chart-container {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}

            .chart-container h2 {{
                color: #2d3748;
                margin-bottom: 20px;
                font-size: 18px;
            }}

            .chart-wrapper {{
                position: relative;
                height: 300px;
            }}

            .recent-calls {{
                background: white;
                border-radius: 12px;
                padding: 25px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}

            .recent-calls h2 {{
                color: #2d3748;
                margin-bottom: 20px;
                font-size: 18px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                background: #f7fafc;
                color: #2d3748;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                border-bottom: 2px solid #e2e8f0;
            }}

            td {{
                padding: 12px;
                border-bottom: 1px solid #e2e8f0;
                color: #4a5568;
            }}

            .call-id {{
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #667eea;
            }}

            .status {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 11px;
                font-weight: 600;
            }}

            .status.resolved {{
                background: #c6f6d5;
                color: #22543d;
            }}

            .status.escalated {{
                background: #bee3f8;
                color: #2c5282;
            }}

            .status.failed {{
                background: #fed7d7;
                color: #742a2a;
            }}

            tr:hover {{
                background: #f7fafc;
            }}

            .footer {{
                text-align: center;
                color: white;
                margin-top: 30px;
                font-size: 12px;
            }}

            .refresh-info {{
                color: #a0aec0;
                font-size: 12px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🦷 Dental Clinic AI Agent Dashboard</h1>
                <p>Real-time conversation analytics and metrics</p>
                <p class="refresh-info">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </header>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Calls Handled</div>
                    <div class="metric-value">{total_calls}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Resolution Rate</div>
                    <div class="metric-value">{resolution_rate:.1f}<span class="metric-unit">%</span></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Escalation Rate</div>
                    <div class="metric-value">{escalation_rate:.1f}<span class="metric-unit">%</span></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Avg Turns per Call</div>
                    <div class="metric-value">{avg_turns:.1f}</div>
                </div>
            </div>

            <div class="charts-grid">
                <div class="chart-container">
                    <h2>📊 Call Resolution</h2>
                    <div class="chart-wrapper">
                        <canvas id="resolutionChart"></canvas>
                    </div>
                </div>
                <div class="chart-container">
                    <h2>📈 Call Distribution</h2>
                    <div class="chart-wrapper">
                        <canvas id="distributionChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="recent-calls">
                <h2>📞 Recent Calls (Last 20)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Call ID</th>
                            <th>Intent</th>
                            <th>Turns</th>
                            <th>Status</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recent_calls_html if recent_calls_html else '<tr><td colspan="5" style="text-align:center; color: #a0aec0;">No calls yet</td></tr>'}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <p>Bright Smile Dental Clinic • AI-Powered Customer Service</p>
                <p>For support, call +1-555-123-4567</p>
            </div>
        </div>

        <script>
            // Resolution Chart
            const resolutionCtx = document.getElementById('resolutionChart').getContext('2d');
            new Chart(resolutionCtx, {{
                type: 'doughnut',
                data: {{
                    labels: ['Resolved', 'Escalated', 'Failed'],
                    datasets: [{{
                        data: [{total_calls * resolution_rate / 100}, {total_calls * escalation_rate / 100}, {total_calls * (100 - resolution_rate - escalation_rate) / 100}],
                        backgroundColor: ['#48bb78', '#4299e1', '#f56565'],
                        borderColor: ['#ffffff', '#ffffff', '#ffffff'],
                        borderWidth: 3,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            position: 'bottom',
                            labels: {{
                                usePointStyle: true,
                                padding: 15,
                            }}
                        }}
                    }}
                }}
            }});

            // Distribution Chart
            const distributionCtx = document.getElementById('distributionChart').getContext('2d');
            new Chart(distributionCtx, {{
                type: 'bar',
                data: {{
                    labels: ['Resolved', 'Escalated', 'Failed'],
                    datasets: [{{
                        label: 'Calls',
                        data: [{total_calls * resolution_rate / 100}, {total_calls * escalation_rate / 100}, {total_calls * (100 - resolution_rate - escalation_rate) / 100}],
                        backgroundColor: ['#48bb78', '#4299e1', '#f56565'],
                        borderRadius: 8,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false,
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            ticks: {{
                                stepSize: 1,
                            }}
                        }}
                    }}
                }}
            }});

            // Auto-refresh every 30 seconds
            setTimeout(() => {{
                location.reload();
            }}, 30000);
        </script>
    </body>
    </html>
    """

    return html
