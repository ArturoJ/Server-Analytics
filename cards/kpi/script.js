(function () {
    window.CardModules = window.CardModules || {};
    function cFlag(c){if(!c||c.length!==2)return '';return String.fromCodePoint(0x1F1E6+c.charCodeAt(0)-65)+String.fromCodePoint(0x1F1E6+c.charCodeAt(1)-65)}

    var KPI_DEFS = {
        ips: {icon: '\u{1F6E1}\uFE0F', label: 'IPs Bloqueadas', gold: true},
        peticiones: {icon: '\u{1F525}', label: 'Peticiones Bloqueadas', gold: false},
        ip_top: {icon: '\u26A0\uFE0F', label: 'IP M\u00E1s Agresiva', gold: false, small: true},
        paises: {icon: '\u{1F30D}', label: 'Pa\u00EDses Detectados', gold: true},
        visitantes: {icon: '\u{1F465}', label: 'Visitantes', gold: true},
    };

    window.CardModules['kpi'] = {
        init: function (container, instanceId, config) {
            var tipo = config.tipo || 'ips';
            var def = KPI_DEFS[tipo] || KPI_DEFS.ips;

            container.querySelector('.kpi-icon').textContent = def.icon;
            container.querySelector('.kpi-label').textContent = def.label;

            var valEl = container.querySelector('.kpi-value');
            var subEl = container.querySelector('.kpi-sub');

            if (!def.gold) valEl.classList.add('white');
            if (def.small) valEl.classList.add('small');

            return {
                update: function (data) {
                    var k = data.kpis;
                    if (tipo === 'ips') {
                        valEl.textContent = fmtNum(k.total_ips);
                        subEl.textContent = 'total acumulado';
                    } else if (tipo === 'peticiones') {
                        valEl.textContent = fmtNum(k.total_peticiones);
                        subEl.textContent = 'Promedio: ' + fmtNum(Math.round(k.total_peticiones / (k.total_ips || 1))) + ' por IP';
                    } else if (tipo === 'ip_top') {
                        if (k.ip_top) {
                            valEl.textContent = k.ip_top.ip;
                            subEl.textContent = fmtNum(k.ip_top.total) + ' pet. \u00B7 ' + k.ip_top.pais + ' ' + cFlag(k.ip_top.codigo_pais);
                        }
                    } else if (tipo === 'paises') {
                        valEl.textContent = fmtNum(k.paises);
                        subEl.textContent = (k.banderas_list || []).join(' ');
                    } else if (tipo === 'visitantes') {
                        valEl.textContent = fmtNum(k.visitantes);
                        subEl.textContent = fmtNum(k.visitas_peticiones) + ' peticiones totales';
                    }
                },
                destroy: function () {},
                resize: function () {},
            };
        }
    };
})();
