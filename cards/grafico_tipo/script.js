(function () {
    window.CardModules = window.CardModules || {};
    window.CardModules['grafico_tipo'] = {
        init: function (container, instanceId, config) {
            var canvas = container.querySelector('canvas');
            var chart = null;
            var MOTIVOS = {escaneo: 'Escaneo', exceso: 'Exceso', fuerza_bruta: 'Fuerza bruta', custom: 'Custom'};

            return {
                update: function (data) {
                    var labels = data.por_tipo.map(function (t) { return MOTIVOS[t.motivo] || t.motivo; });
                    var valores = data.por_tipo.map(function (t) { return t.total; });

                    if (chart) {
                        chart.data.labels = labels;
                        chart.data.datasets[0].data = valores;
                        chart.update();
                        return;
                    }

                    chart = new Chart(canvas, {
                        type: 'doughnut',
                        data: {
                            labels: labels,
                            datasets: [{
                                data: valores,
                                backgroundColor: ['#C8A951', '#E74C3C', '#a855f7', '#299cdb'],
                                borderColor: '#1e2a4a',
                                borderWidth: 3,
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            cutout: '65%',
                            plugins: {legend: {position: 'bottom', labels: {padding: 14, usePointStyle: true, color: '#8892a4'}}}
                        }
                    });
                },
                destroy: function () { if (chart) chart.destroy(); },
                resize: function () { if (chart) chart.resize(); },
            };
        }
    };
})();
