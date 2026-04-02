(function () {
    window.CardModules = window.CardModules || {};
    function cFlag(c){if(!c||c.length!==2)return '';return String.fromCodePoint(0x1F1E6+c.charCodeAt(0)-65)+String.fromCodePoint(0x1F1E6+c.charCodeAt(1)-65)}

    function esc(str) { var d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

    window.CardModules['tabla_bloqueos'] = {
        init: function (container, instanceId, config) {
            var tbody = container.querySelector('.tb-body');
            var countEl = container.querySelector('.tb-count');
            var filtro = 'all';
            var allData = [];

            container.querySelectorAll('.tb-btn').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.stopPropagation();
                    container.querySelectorAll('.tb-btn').forEach(function (b) { b.classList.remove('active'); });
                    btn.classList.add('active');
                    filtro = btn.dataset.filter;
                    render();
                });
            });

            function render() {
                var datos = allData;
                if (filtro !== 'all') datos = datos.filter(function (u) { return u.motivo === filtro; });
                countEl.textContent = datos.length;
                tbody.innerHTML = datos.map(function (u) {
                    var sev = u.peticiones >= 50 ? ' tag-red' : u.peticiones >= 25 ? ' tag-gold' : '';
                    var tc = u.motivo === 'exceso' ? 'tag-red' : 'tag-gold';
                    var label = u.motivo === 'exceso' ? 'Exceso' : 'Escaneo';
                    var dt = new Date(u.fecha_bloqueo);
                    return '<tr>' +
                        '<td class="td-date">' + esc(dt.toLocaleDateString('es-ES', {day:'2-digit',month:'2-digit'})) + '</td>' +
                        '<td class="td-time">' + esc(dt.toLocaleTimeString('es-ES', {hour:'2-digit',minute:'2-digit'})) + '</td>' +
                        '<td><a href="/bloqueos/' + esc(u.ip) + '/" class="ip">' + esc(u.ip) + '</a></td>' +
                        '<td><span class="flag">' + cFlag(u.codigo_pais) + '</span><span class="country">' + esc(u.pais) + '</span></td>' +
                        '<td><span class="tag ' + tc + '">' + esc(label) + '</span></td>' +
                        '<td><span class="tag' + sev + '">' + fmtNum(u.peticiones) + '</span></td>' +
                        '<td class="td-regla">' + esc(u.regla || '') + '</td>' +
                        '<td class="td-status">\u25CF Bloqueada</td></tr>';
                }).join('');
            }

            return {
                update: function (data) {
                    allData = data.ultimos || [];
                    render();
                },
                destroy: function () {},
                resize: function () {},
            };
        }
    };
})();
