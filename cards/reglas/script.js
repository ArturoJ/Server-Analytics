(function () {
    window.CardModules = window.CardModules || {};

    function esc(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

    var TIPO_COLORS = {escaneo: 'tag-gold', exceso: 'tag-red', fuerza_bruta: 'tag-purple', custom: 'tag-blue'};

    window.CardModules['reglas'] = {
        init: function (container, instanceId, config) {
            var listEl = container.querySelector('.rl-list');
            var loaded = false;

            function load() {
                fetch('/api/reglas/').then(function (r) { return r.json(); }).then(function (data) {
                    listEl.innerHTML = data.reglas.map(function (r) {
                        var tc = TIPO_COLORS[r.tipo] || 'tag-blue';
                        var sc = r.activa ? 'tag-green' : 'tag-red';
                        return '<div class="rl-item' + (r.activa ? '' : ' inactive') + '">' +
                            '<div class="rl-head">' +
                                '<span class="rl-name">' + esc(r.nombre) + '</span>' +
                                '<div class="rl-tags">' +
                                    '<span class="tag ' + tc + '">' + esc(r.tipo_display) + '</span>' +
                                    '<span class="tag ' + sc + '">' + (r.activa ? 'Activa' : 'Inactiva') + '</span>' +
                                '</div>' +
                            '</div>' +
                            (r.descripcion ? '<div class="rl-pattern">' + esc(r.descripcion) + '</div>' : '') +
                            '<div class="rl-stats">' +
                                '<div class="rl-stat"><div class="rl-stat-val">' + fmtNum(r.disparos_hoy) + '</div><div class="rl-stat-lbl">Disparos</div></div>' +
                                '<div class="rl-stat"><div class="rl-stat-val">' + fmtNum(r.ips_hoy) + '</div><div class="rl-stat-lbl">IPs</div></div>' +
                                '<div class="rl-stat"><div class="rl-stat-val">' + fmtNum(r.peticiones_hoy) + '</div><div class="rl-stat-lbl">Peticiones</div></div>' +
                            '</div>' +
                            '</div>';
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
