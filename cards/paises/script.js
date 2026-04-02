(function () {
    window.CardModules = window.CardModules || {};

    function esc(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

    window.CardModules['paises'] = {
        init: function (container, instanceId, config) {
            var tbody = container.querySelector('.pa-body');
            var loaded = false;

            function load() {
                fetch('/api/estadisticas/paises/').then(function (r) { return r.json(); }).then(function (data) {
                    container.querySelector('#paTotalPaises').textContent = fmtNum(data.total_paises);
                    container.querySelector('#paTotalPet').textContent = fmtNum(data.total_peticiones);
                    container.querySelector('#paTotalIps').textContent = fmtNum(data.total_ips);

                    tbody.innerHTML = data.ranking.map(function (p, i) {
                        return '<tr>' +
                            '<td class="pa-pos ' + (i === 0 ? 'pa-pos-1' : 'pa-pos-n') + '">' + (i + 1) + '</td>' +
                            '<td><span class="flag">' + esc(p.bandera) + '</span> ' + esc(p.pais) + '</td>' +
                            '<td>' + fmtNum(p.ips) + '</td>' +
                            '<td class="pa-pet">' + fmtNum(p.peticiones) + '</td>' +
                            '<td class="pa-pct">' + p.porcentaje + '%</td>' +
                            '</tr>';
                    }).join('');
                });
            }

            return {
                update: function () {
                    if (!loaded) { load(); loaded = true; }
                },
                destroy: function () {},
                resize: function () {},
            };
        }
    };
})();
