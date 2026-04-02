var Dashboard = (function () {
    var CELL = 20, GAP = 4, MIN_W = 6, MIN_H = 5;
    var STORAGE_KEY = 'sa_dashboard_layout';
    var cards = [], modules = [];
    var dragState = null, resizeState = null, ctxTarget = null;
    var confirmCb = null, editMode = false, refreshTimer = null;
    var grid, ghost, canvas, cardTemplates = {};

    function init() {
        grid = document.getElementById('dash-grid');
        ghost = document.getElementById('ghost');
        canvas = document.getElementById('dash-canvas');
        modules = MODULES_DATA || [];
        cardTemplates = CARD_TEMPLATES || {};

        document.body.classList.add('edit-off');

        var saved = loadLocal();
        var source = saved || CARDS_DATA || [];
        source.forEach(function (c) {
            cards.push(c);
            renderCard(c);
        });

        if (!saved) persistLocal();

        renderModuleGrid();
        bindEvents();
        updateCount();
        updateGridHeight();
        fetchData();
        refreshTimer = setInterval(fetchData, 30000);
    }

    function loadLocal() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return null;
            var data = JSON.parse(raw);
            if (!Array.isArray(data) || !data.length) return null;
            return data;
        } catch (e) { return null; }
    }

    function persistLocal() {
        var items = cards.map(function (c) {
            return {
                id: c.id, instance_id: c.instance_id,
                module_slug: c.module_slug, module_nombre: c.module_nombre, module_color: c.module_color,
                label: c.label, config: c.config,
                grid_x: c.grid_x, grid_y: c.grid_y, grid_w: c.grid_w, grid_h: c.grid_h,
                z_index: c.z_index || 0,
            };
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
    }

    function fetchData() {
        fetch('/api/dashboard/').then(function (r) { return r.json(); }).then(function (data) {
            cards.forEach(function (c) {
                if (c._api && c._api.update) c._api.update(data);
            });
        });
    }

    function renderCard(c) {
        var el = document.createElement('div');
        el.className = 'sa-card';
        el.dataset.id = c.id;
        el.dataset.instanceId = c.instance_id;
        el.dataset.cardModule = c.module_slug;
        positionCard(el, c);

        var headLeft = document.createElement('div');
        headLeft.className = 'sa-card-head-left';

        var dot = document.createElement('span');
        dot.className = 'sa-card-dot';
        dot.style.setProperty('--dot-color', c.module_color);
        headLeft.appendChild(dot);

        var title = document.createElement('span');
        title.className = 'sa-card-title';
        title.textContent = c.label || c.module_nombre;
        headLeft.appendChild(title);

        var actions = document.createElement('div');
        actions.className = 'sa-card-actions';
        var btnDup = document.createElement('button');
        btnDup.className = 'sa-card-btn';
        btnDup.dataset.action = 'duplicate';
        btnDup.textContent = '+';
        var btnDel = document.createElement('button');
        btnDel.className = 'sa-card-btn del';
        btnDel.dataset.action = 'delete';
        btnDel.textContent = 'x';
        actions.appendChild(btnDup);
        actions.appendChild(btnDel);

        var head = document.createElement('div');
        head.className = 'sa-card-head';
        head.appendChild(headLeft);
        head.appendChild(actions);

        var body = document.createElement('div');
        body.className = 'card-body';
        body.innerHTML = cardTemplates[c.module_slug] || '<div class="card-empty">--</div>';

        el.appendChild(head);
        el.appendChild(body);

        var re = document.createElement('div'); re.className = 'resize-e';
        var rs = document.createElement('div'); rs.className = 'resize-s';
        var rse = document.createElement('div'); rse.className = 'resize-se';
        el.appendChild(re);
        el.appendChild(rs);
        el.appendChild(rse);

        grid.appendChild(el);

        var factory = window.CardModules && window.CardModules[c.module_slug];
        if (factory) {
            c._api = factory.init(body, c.instance_id, c.config || {});
            if (c._api) {
                var ro = new ResizeObserver(function () { if (c._api.resize) c._api.resize(); });
                ro.observe(body);
                c._ro = ro;
            }
        }
    }

    function positionCard(el, c) {
        el.style.setProperty('--cx', c.grid_x * CELL + GAP);
        el.style.setProperty('--cy', c.grid_y * CELL + GAP);
        el.style.setProperty('--cw', c.grid_w * CELL - GAP);
        el.style.setProperty('--ch', c.grid_h * CELL - GAP);
    }

    function findCard(id) { return cards.find(function (c) { return String(c.id) === String(id); }); }
    function findEl(id) { return grid.querySelector('[data-id="' + id + '"]'); }
    function pxToGrid(px, py) { return {gx: Math.max(0, Math.round((px - GAP) / CELL)), gy: Math.max(0, Math.round((py - GAP) / CELL))}; }
    function updateCount() { var el = document.getElementById('card-count'); if (el) el.textContent = cards.length; }

    function maxCols() {
        var w = canvas ? canvas.clientWidth : window.innerWidth;
        return Math.floor((w - GAP * 2) / CELL);
    }

    function hasCollision(c, exceptId) {
        return cards.some(function (o) {
            if (String(o.id) === String(exceptId)) return false;
            return !(c.grid_x + c.grid_w <= o.grid_x || o.grid_x + o.grid_w <= c.grid_x ||
                     c.grid_y + c.grid_h <= o.grid_y || o.grid_y + o.grid_h <= c.grid_y);
        });
    }

    function findFree(w, h) {
        var cols = maxCols();
        for (var y = 0; y < 200; y++) {
            for (var x = 0; x <= cols - w; x++) {
                if (!hasCollision({grid_x: x, grid_y: y, grid_w: w, grid_h: h}, -1)) return {x: x, y: y};
            }
        }
        return {x: 0, y: 0};
    }

    function updateGridHeight() {
        var maxY = 0;
        cards.forEach(function (c) {
            var bottom = c.grid_y + c.grid_h;
            if (bottom > maxY) maxY = bottom;
        });
        grid.style.setProperty('--grid-h', (maxY + 1) * CELL);
    }

    function saveLayout() {
        persistLocal();
    }

    function createCard(slug, extraConfig) {
        var mod = modules.find(function (m) { return m.slug === slug; });
        if (!mod) return;
        var pos = findFree(mod.default_w, mod.default_h);
        var conf = extraConfig || {};
        var c = {
            id: 'local_' + Date.now(),
            instance_id: 'local_' + Date.now() + '_' + Math.random().toString(36).substr(2, 8),
            module_slug: slug, module_nombre: mod.nombre, module_color: mod.color,
            label: '', config: conf,
            grid_x: pos.x, grid_y: pos.y, grid_w: mod.default_w, grid_h: mod.default_h,
            z_index: 0,
        };
        cards.push(c);
        renderCard(c);
        updateCount();
        updateGridHeight();
        persistLocal();
        fetchData();
        toast('Card agregada');
    }

    function deleteCard(id) {
        var c = findCard(id);
        if (!c) return;
        showConfirm('Eliminar "' + (c.label || c.module_nombre) + '"?', function () {
            if (c._api && c._api.destroy) c._api.destroy();
            if (c._ro) c._ro.disconnect();
            var el = findEl(id);
            if (el) el.remove();
            cards = cards.filter(function (x) { return String(x.id) !== String(id); });
            updateCount();
            updateGridHeight();
            persistLocal();
            toast('Card eliminada');
        });
    }

    function duplicateCard(id) {
        var orig = findCard(id);
        if (!orig) return;
        createCard(orig.module_slug, orig.config);
    }

    function renameCard(id) {
        var c = findCard(id);
        if (!c) return;
        var current = c.label || c.module_nombre;
        var name = prompt('Nombre de la card:', current);
        if (name === null) return;
        c.label = name;
        var el = findEl(id);
        if (el) {
            var titleEl = el.querySelector('.sa-card-title');
            if (titleEl) titleEl.textContent = name || c.module_nombre;
        }
        persistLocal();
        toast('Renombrada');
    }

    function resetLayout() {
        showConfirm('Restaurar layout por defecto?', function () {
            cards.forEach(function (c) {
                if (c._api && c._api.destroy) c._api.destroy();
                if (c._ro) c._ro.disconnect();
            });
            grid.querySelectorAll('.sa-card').forEach(function (el) { el.remove(); });
            cards = [];
            localStorage.removeItem(STORAGE_KEY);
            (CARDS_DATA || []).forEach(function (c) {
                cards.push(c);
                renderCard(c);
            });
            persistLocal();
            updateCount();
            updateGridHeight();
            fetchData();
            toast('Layout restaurado');
        });
    }

    function startDrag(e, el) {
        var c = findCard(el.dataset.id);
        if (!c) return;
        var r = el.getBoundingClientRect();
        var cr = canvas.getBoundingClientRect();
        dragState = {id: c.id, card: c, el: el, ox: e.clientX - r.left, oy: e.clientY - r.top, cl: cr.left, ct: cr.top + canvas.parentElement.scrollTop - canvas.offsetTop};
        el.classList.add('dragging');
        ghost.classList.add('visible');
        updateGhost(c.grid_x, c.grid_y, c.grid_w, c.grid_h);
    }

    function onDrag(e) {
        if (!dragState) return;
        e.preventDefault();
        var scrollTop = canvas.parentElement.scrollTop || 0;
        var cr = canvas.getBoundingClientRect();
        var px = e.clientX - cr.left - dragState.ox;
        var py = e.clientY - cr.top + scrollTop - dragState.oy;
        dragState.el.style.setProperty('--cx', px);
        dragState.el.style.setProperty('--cy', py);
        var g = pxToGrid(px + GAP, py + GAP);
        var sx = Math.max(0, Math.min(g.gx, maxCols() - dragState.card.grid_w));
        var sy = Math.max(0, g.gy);
        var coll = hasCollision({grid_x: sx, grid_y: sy, grid_w: dragState.card.grid_w, grid_h: dragState.card.grid_h}, dragState.id);
        ghost.style.setProperty('--ghost-color', coll ? 'var(--red)' : 'var(--gold)');
        ghost.style.setProperty('--ghost-bg', coll ? 'rgba(231,76,60,0.06)' : 'rgba(200,169,81,0.06)');
        updateGhost(sx, sy, dragState.card.grid_w, dragState.card.grid_h);
        dragState.tx = sx;
        dragState.ty = sy;
        dragState.coll = coll;
    }

    function endDrag() {
        if (!dragState) return;
        dragState.el.classList.remove('dragging');
        ghost.classList.remove('visible');
        if (dragState.tx !== undefined && !dragState.coll) {
            dragState.card.grid_x = dragState.tx;
            dragState.card.grid_y = dragState.ty;
        }
        positionCard(dragState.el, dragState.card);
        updateGridHeight();
        saveLayout();
        dragState = null;
    }

    function startResize(e, el, dir) {
        var c = findCard(el.dataset.id);
        if (!c) return;
        e.preventDefault();
        e.stopPropagation();
        resizeState = {id: c.id, card: c, el: el, dir: dir, sx: e.clientX, sy: e.clientY, sw: c.grid_w, sh: c.grid_h};
        ghost.classList.add('visible');
        updateGhost(c.grid_x, c.grid_y, c.grid_w, c.grid_h);
    }

    function onResize(e) {
        if (!resizeState) return;
        e.preventDefault();
        var dx = e.clientX - resizeState.sx;
        var dy = e.clientY - resizeState.sy;
        var nw = resizeState.sw, nh = resizeState.sh;
        if (resizeState.dir.indexOf('e') >= 0) nw = Math.max(MIN_W, resizeState.sw + Math.round(dx / CELL));
        if (resizeState.dir.indexOf('s') >= 0) nh = Math.max(MIN_H, resizeState.sh + Math.round(dy / CELL));
        nw = Math.min(nw, maxCols() - resizeState.card.grid_x);
        var coll = hasCollision({grid_x: resizeState.card.grid_x, grid_y: resizeState.card.grid_y, grid_w: nw, grid_h: nh}, resizeState.id);
        ghost.style.setProperty('--ghost-color', coll ? 'var(--red)' : 'var(--gold)');
        ghost.style.setProperty('--ghost-bg', coll ? 'rgba(231,76,60,0.06)' : 'rgba(200,169,81,0.06)');
        updateGhost(resizeState.card.grid_x, resizeState.card.grid_y, nw, nh);
        resizeState.tw = nw;
        resizeState.th = nh;
        resizeState.coll = coll;
    }

    function endResize() {
        if (!resizeState) return;
        ghost.classList.remove('visible');
        if (resizeState.tw && !resizeState.coll) {
            resizeState.card.grid_w = resizeState.tw;
            resizeState.card.grid_h = resizeState.th;
        }
        positionCard(resizeState.el, resizeState.card);
        updateGridHeight();
        saveLayout();
        resizeState = null;
    }

    function updateGhost(x, y, w, h) {
        ghost.style.setProperty('--gx', x * CELL + GAP);
        ghost.style.setProperty('--gy', y * CELL + GAP);
        ghost.style.setProperty('--gw', w * CELL - GAP);
        ghost.style.setProperty('--gh', h * CELL - GAP);
    }

    function renderModuleGrid() {
        var g = document.getElementById('module-grid');
        if (!g) return;
        var cats = {};
        var catLabels = {metricas: 'Metricas', graficos: 'Graficos', tablas: 'Tablas', general: 'General'};
        modules.forEach(function (m) {
            var cat = m.categoria || 'general';
            if (!cats[cat]) cats[cat] = [];
            cats[cat].push(m);
        });

        var catKeys = Object.keys(cats);
        var html = '<div class="mod-tabs">';
        catKeys.forEach(function (k, i) {
            html += '<button class="mod-tab' + (i === 0 ? ' active' : '') + '" data-cat="' + k + '">' +
                (catLabels[k] || k) + ' <span class="mod-tab-count">' + cats[k].length + '</span></button>';
        });
        html += '</div>';

        catKeys.forEach(function (k, i) {
            html += '<div class="mod-cat-grid' + (i === 0 ? ' active' : '') + '" data-cat="' + k + '">';
            html += '<div class="module-grid">';
            cats[k].forEach(function (m) {
                html += '<div class="module-opt" data-slug="' + m.slug + '" data-color="' + m.color + '">' +
                    '<div class="module-dot"></div>' +
                    '<div class="module-name">' + m.nombre + '</div>' +
                    '<div class="module-desc">' + m.descripcion + '</div></div>';
            });
            html += '</div></div>';
        });

        g.innerHTML = html;

        g.querySelectorAll('.module-opt').forEach(function (opt) {
            var dot = opt.querySelector('.module-dot');
            if (dot && opt.dataset.color) dot.style.setProperty('--dot-color', opt.dataset.color);
        });

        g.querySelectorAll('.mod-tab').forEach(function (tab) {
            tab.addEventListener('click', function () {
                g.querySelectorAll('.mod-tab').forEach(function (t) { t.classList.remove('active'); });
                g.querySelectorAll('.mod-cat-grid').forEach(function (c) { c.classList.remove('active'); });
                tab.classList.add('active');
                g.querySelector('.mod-cat-grid[data-cat="' + tab.dataset.cat + '"]').classList.add('active');
            });
        });
    }

    function openModal(id) { document.getElementById(id).classList.add('active'); }
    function closeModal(id) { document.getElementById(id).classList.remove('active'); }
    function toast(msg) {
        var el = document.createElement('div');
        el.className = 'toast';
        el.textContent = msg;
        document.getElementById('toasts').appendChild(el);
        setTimeout(function () { el.classList.add('out'); setTimeout(function () { el.remove(); }, 150); }, 2000);
    }
    function showConfirm(msg, cb) {
        document.getElementById('confirm-msg').textContent = msg;
        confirmCb = cb;
        openModal('confirm-overlay');
    }
    function hideConfirm() { closeModal('confirm-overlay'); confirmCb = null; }
    function showCtx(e, id) {
        e.preventDefault();
        ctxTarget = id;
        var m = document.getElementById('ctx-menu');
        m.style.setProperty('--ctx-x', e.clientX + 'px');
        m.style.setProperty('--ctx-y', e.clientY + 'px');
        m.classList.add('active');
    }
    function hideCtx() { document.getElementById('ctx-menu').classList.remove('active'); ctxTarget = null; }

    function bindEvents() {
        grid.addEventListener('mousedown', function (e) {
            if (!editMode) return;
            var btn = e.target.closest('.sa-card-btn');
            var rz = e.target.closest('[class^="resize-"]');
            var hd = e.target.closest('.sa-card-head');
            var el = e.target.closest('.sa-card');
            if (btn && el) {
                e.stopPropagation();
                var a = btn.dataset.action, id = el.dataset.id;
                if (a === 'delete') deleteCard(id);
                if (a === 'duplicate') duplicateCard(id);
                return;
            }
            if (rz && el) {
                var dir = rz.className.replace('resize-', '');
                startResize(e, el, dir);
                return;
            }
            if (hd && el) startDrag(e, el);
        });

        document.addEventListener('mousemove', function (e) {
            if (dragState) onDrag(e);
            if (resizeState) onResize(e);
        });
        document.addEventListener('mouseup', function () {
            if (dragState) endDrag();
            if (resizeState) endResize();
        });

        grid.addEventListener('contextmenu', function (e) {
            if (!editMode) return;
            var el = e.target.closest('.sa-card');
            if (el) showCtx(e, el.dataset.id);
        });
        document.addEventListener('click', hideCtx);

        document.getElementById('ctx-menu').addEventListener('click', function (e) {
            var it = e.target.closest('.ctx-item');
            if (!it || !ctxTarget) return;
            var a = it.dataset.action;
            if (a === 'rename') renameCard(ctxTarget);
            if (a === 'duplicate') duplicateCard(ctxTarget);
            if (a === 'delete') deleteCard(ctxTarget);
            if (a === 'front') {
                var el = findEl(ctxTarget);
                if (el) grid.appendChild(el);
            }
            hideCtx();
        });

        document.getElementById('btn-edit').addEventListener('click', function () {
            editMode = !editMode;
            document.body.classList.toggle('edit-off', !editMode);
            this.textContent = editMode ? 'Editor ON' : 'Editor OFF';
            this.classList.toggle('dash-btn-primary', editMode);
        });

        document.getElementById('btn-add').addEventListener('click', function () { openModal('modal-add'); });

        document.getElementById('btn-clear').addEventListener('click', function () {
            resetLayout();
        });

        document.querySelectorAll('.modal-x').forEach(function (btn) {
            btn.addEventListener('click', function () { closeModal(btn.dataset.close); });
        });
        document.querySelectorAll('.modal-overlay').forEach(function (ov) {
            ov.addEventListener('click', function (e) { if (e.target === ov) closeModal(ov.id); });
        });

        document.getElementById('module-grid').addEventListener('click', function (e) {
            var opt = e.target.closest('.module-opt');
            if (!opt) return;
            var slug = opt.dataset.slug;
            var conf = {};
            if (slug === 'kpi') {
                var tipos = ['ips', 'peticiones', 'ip_top', 'paises', 'visitantes'];
                var existing = cards.filter(function (c) { return c.module_slug === 'kpi'; }).map(function (c) { return c.config.tipo; });
                var available = tipos.filter(function (t) { return existing.indexOf(t) === -1; });
                var tipo = available.length ? available[0] : tipos[0];
                conf = {tipo: tipo};
            }
            createCard(slug, conf);
            closeModal('modal-add');
        });

        document.getElementById('confirm-yes').addEventListener('click', function () { if (confirmCb) confirmCb(); hideConfirm(); });
        document.getElementById('confirm-no').addEventListener('click', hideConfirm);

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { closeModal('modal-add'); hideConfirm(); hideCtx(); }
        });
    }

    return {init: init};
})();

document.addEventListener('DOMContentLoaded', Dashboard.init);
