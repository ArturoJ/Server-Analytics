(function () {
    window.CardModules = window.CardModules || {};
    window.CardModules['grafico_hora'] = {
        init: function (container, instanceId, config) {
            var canvas = container.querySelector('canvas');
            var chart = null;

            return {
                update: function (data) {
                    var labels = data.por_hora.map(function (h) { return h.hora + ':00'; });
                    var valores = data.por_hora.map(function (h) { return h.total; });

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
                                backgroundColor: labels.map(function (_, i) {
                                    return 'rgba(200,169,81,' + (0.4 + (i / labels.length) * 0.6) + ')';
                                }),
                                borderColor: '#C8A951',
                                borderWidth: 1,
                                borderRadius: 6,
                                borderSkipped: false,
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {legend: {display: false}},
                            scales: {
                                y: {grid: {color: 'rgba(255,255,255,.04)'}, ticks: {stepSize: 1}},
                                x: {grid: {display: false}}
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
