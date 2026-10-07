// AcxiomCRM Chart.js Dashboard Visualizations

document.addEventListener('DOMContentLoaded', function () {
    const leadCanvas = document.getElementById('leadStatusChart');
    const pipelineCanvas = document.getElementById('pipelineChart');

    if (!leadCanvas || !pipelineCanvas) return;

    fetch('/api/dashboard/chart-data')
        .then(response => response.json())
        .then(data => {
            // 1. Lead Status Doughnut Chart
            new Chart(leadCanvas, {
                type: 'doughnut',
                data: {
                    labels: data.lead_chart.labels,
                    datasets: [{
                        data: data.lead_chart.data,
                        backgroundColor: [
                            '#3b82f6', // New - Blue
                            '#8b5cf6', // Contacted - Purple
                            '#10b981', // Qualified - Emerald
                            '#6b7280', // Unqualified - Gray
                            '#059669', // Converted - Green
                            '#ef4444'  // Lost - Red
                        ],
                        borderWidth: 2,
                        borderColor: '#1f2937'
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#9ca3af', font: { family: 'Inter', size: 12 } }
                        }
                    }
                }
            });

            // 2. Opportunity Pipeline Bar Chart
            new Chart(pipelineCanvas, {
                type: 'bar',
                data: {
                    labels: data.pipeline_chart.labels,
                    datasets: [{
                        label: 'Pipeline Amount ($)',
                        data: data.pipeline_chart.values,
                        backgroundColor: '#6366f1',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: '#374151' }
                        },
                        y: {
                            ticks: { color: '#9ca3af' },
                            grid: { color: '#374151' }
                        }
                    }
                }
            });
        })
        .catch(err => console.error('Error loading dashboard chart data:', err));
});
