/* ============================================================
   dashboard.js — Chart rendering for the Dashboard page
   Data values are injected via inline script in dashboard.html
   ============================================================ */

/**
 * Initialise both charts once the DOM is ready.
 * `DASHBOARD_DATA` is expected to be set by the inline script
 * in dashboard.html before this file is loaded.
 */
document.addEventListener('DOMContentLoaded', function () {
    const high   = DASHBOARD_DATA.high;
    const medium = DASHBOARD_DATA.medium;
    const low    = DASHBOARD_DATA.low;

    // ── Doughnut chart: cluster distribution ──
    new Chart(document.getElementById('pieChart'), {
        type: 'doughnut',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                data: [high, medium, low],
                backgroundColor: ['#2d6a4f', '#b5770d', '#8b2e2e'],
                borderWidth: 0
            }]
        },
        options: {
            plugins: { legend: { position: 'bottom' } }
        }
    });

    // ── Bar chart: customer count per cluster ──
    new Chart(document.getElementById('barChart'), {
        type: 'bar',
        data: {
            labels: ['High', 'Medium', 'Low'],
            datasets: [{
                label: 'Customers',
                data: [high, medium, low],
                backgroundColor: ['#2d6a4f', '#b5770d', '#8b2e2e'],
                borderRadius: 4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
});
