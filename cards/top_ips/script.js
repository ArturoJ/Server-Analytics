(function () {
    window.CardModules = window.CardModules || {};
    window.CardModules['top_ips'] = {
        init: function (container, instanceId, config) {
            var canvas = container.querySelector('canvas');
            var chart = null;

            return {
                update: function (data) {
                    var labels = data.top_ips.map(function (i) { return i.ip; });
                    var valores = data.top_ips.map(function (i) { return i.total; });

                    if (chart) {
                        chart.data.labels = labels;
                        chart.data.datasets[0].data = valores;
                        chart.update();
                        return;
                    }

                    chart = new Chart(canvas, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                data: valores,
                                backgroundColor: ['#FFD700', '#C8A951', '#E8D5A0', '#9A7B2F', '#7A6223'],
                                borderRadius: 6,
                                borderSkipped: false,
                            }]
                        },
                        options: {
                            indexAxis: 'y',
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {legend: {display: false}},
                            scales: {
                                x: {grid: {color: 'rgba(255,255,255,.04)'}},
                                y: {grid: {display: false}, ticks: {font: {size: 9}, color: '#8892a4'}}
                            }
                        }
                    });
                },
                destroy: function () { if (chart) chart.destroy(); },
                resize: function () { if (chart) chart.resize(); },
            };
        }
    };
})();
