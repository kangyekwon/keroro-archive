/* === Keroro Archive - D3.js Relationship Graph === */

var RELATION_COLORS = {
    'friend': '#55efc4',
    'enemy': '#ff4466',
    'family': '#4fc3f7',
    'rival': '#ff9f43',
    'partner': '#a29bfe',
    'subordinate': '#888',
    '친구': '#55efc4',
    '적': '#ff4466',
    '가족': '#4fc3f7',
    '라이벌': '#ff9f43',
    '파트너': '#a29bfe',
    '부하': '#888'
};

var NODE_COLORS = {
    '케로로': '#4a7c59',
    '기로로': '#cc3333',
    '타마마': '#3366cc',
    '쿠루루': '#ffd700',
    '도로로': '#66bbee',
    '가루루': '#6633cc',
    '나츠미': '#ff9f43',
    '후유키': '#88aa88',
    '모모카': '#fd79a8',
    '앙골 모아': '#ff6b6b'
};

var graphSim = null;
var graphSvg = null;

async function initGraph() {
    var canvas = document.getElementById('graph-canvas');
    canvas.innerHTML = '<div class="loading"><div class="spinner"></div>관계도 로딩 중...</div>';

    try {
        var data = await api('/api/graph');
        var nodes = data.nodes || [];
        var links = data.links || [];

        if (!nodes.length) {
            canvas.innerHTML = '<p style="color:var(--text-secondary);padding:2rem;text-align:center;">관계 데이터가 없습니다.</p>';
            return;
        }

        canvas.innerHTML = '';
        buildGraph(nodes, links, canvas);
    } catch (e) {
        canvas.innerHTML = '<p style="color:var(--danger);padding:2rem;text-align:center;">관계도 로드 실패: ' + e.message + '</p>';
    }
}

function getNodeColor(node) {
    var name = node.name || node.id || '';
    // Check if name matches any known character
    var keys = Object.keys(NODE_COLORS);
    for (var i = 0; i < keys.length; i++) {
        if (name.indexOf(keys[i]) !== -1) return NODE_COLORS[keys[i]];
    }
    // Fallback by group/race
    if (node.color) return node.color;
    if (node.race === '케론인') return '#4a7c59';
    if (node.race === '인간') return '#ff9f43';
    return '#888';
}

function getRelationColor(link) {
    var type = (link.relation_type || link.type || '').toLowerCase();
    return RELATION_COLORS[type] || '#555';
}

function nodeRadius(d) {
    // Main characters bigger
    var name = d.name || d.id || '';
    var mainChars = ['케로로', '기로로', '타마마', '쿠루루', '도로로'];
    for (var i = 0; i < mainChars.length; i++) {
        if (name.indexOf(mainChars[i]) !== -1) return 22;
    }
    // Secondary characters
    var secondaryChars = ['나츠미', '후유키', '모모카', '가루루', '앙골 모아'];
    for (var j = 0; j < secondaryChars.length; j++) {
        if (name.indexOf(secondaryChars[j]) !== -1) return 18;
    }
    return 14;
}

function buildGraph(nodes, links, container) {
    var w = container.clientWidth || 800;
    var h = container.clientHeight || 600;

    var svg = d3.select(container).append('svg')
        .attr('width', w).attr('height', h)
        .style('position', 'absolute').style('top', '0').style('left', '0');
    graphSvg = svg;

    var zoomG = svg.append('g');
    svg.call(d3.zoom().scaleExtent([0.3, 4]).on('zoom', function(event) {
        zoomG.attr('transform', event.transform);
    }));

    // Defs for glow effect
    var defs = svg.append('defs');
    var glow = defs.append('filter').attr('id', 'glow')
        .attr('x', '-50%').attr('y', '-50%').attr('width', '200%').attr('height', '200%');
    glow.append('feGaussianBlur').attr('stdDeviation', '4').attr('result', 'blur');
    var merge = glow.append('feMerge');
    merge.append('feMergeNode').attr('in', 'blur');
    merge.append('feMergeNode').attr('in', 'SourceGraphic');

    // Arrow marker
    defs.append('marker').attr('id', 'arrow')
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 25).attr('refY', 0)
        .attr('markerWidth', 6).attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path').attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', '#4a7c59').attr('opacity', 0.6);

    // Force simulation
    var sim = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(function(d) { return d.id; }).distance(140))
        .force('charge', d3.forceManyBody().strength(-500))
        .force('center', d3.forceCenter(w / 2, h / 2))
        .force('collision', d3.forceCollide().radius(function(d) { return nodeRadius(d) + 10; }));
    graphSim = sim;

    // Links
    var link = zoomG.append('g').selectAll('line').data(links).enter().append('line')
        .attr('stroke', function(d) { return getRelationColor(d); })
        .attr('stroke-width', 2)
        .attr('opacity', 0.5)
        .attr('marker-end', 'url(#arrow)');

    // Link labels
    var linkLabel = zoomG.append('g').selectAll('text').data(links).enter().append('text')
        .attr('text-anchor', 'middle')
        .attr('font-size', '9px')
        .attr('fill', function(d) { return getRelationColor(d); })
        .attr('pointer-events', 'none')
        .attr('opacity', 0)
        .text(function(d) { return d.relation_type || d.type || ''; });

    // Nodes
    var node = zoomG.append('g').selectAll('g').data(nodes).enter().append('g')
        .call(d3.drag()
            .on('start', function(e, d) { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
            .on('drag', function(e, d) { d.fx = e.x; d.fy = e.y; })
            .on('end', function(e, d) { if (!e.active) sim.alphaTarget(0); d.fx = null; d.fy = null; })
        );

    // Glow circle
    node.append('circle')
        .attr('r', function(d) { return nodeRadius(d) + 5; })
        .attr('fill', function(d) { return getNodeColor(d); })
        .attr('opacity', 0.15)
        .attr('filter', 'url(#glow)');

    // Main circle
    node.append('circle')
        .attr('r', nodeRadius)
        .attr('fill', function(d) { return getNodeColor(d); })
        .attr('stroke', 'rgba(255,255,255,0.3)')
        .attr('stroke-width', 2);

    // Node initial letter
    node.append('text')
        .text(function(d) { return (d.name || d.id || '?').charAt(0); })
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('fill', 'white')
        .attr('font-size', function(d) { return nodeRadius(d) > 18 ? '14px' : '10px'; })
        .attr('font-weight', '800')
        .attr('pointer-events', 'none');

    // Node name label below
    node.append('text')
        .text(function(d) { return d.name || d.id || ''; })
        .attr('y', function(d) { return nodeRadius(d) + 14; })
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('fill', 'var(--text-primary)')
        .attr('font-weight', '600')
        .attr('pointer-events', 'none');

    // Tooltip
    var tooltip = document.getElementById('node-tooltip');
    node.on('mouseover', function(event, d) {
        // Highlight connected
        var connected = new Set([d.id]);
        links.forEach(function(l) {
            var s = l.source.id !== undefined ? l.source.id : l.source;
            var t = l.target.id !== undefined ? l.target.id : l.target;
            if (s === d.id) connected.add(t);
            if (t === d.id) connected.add(s);
        });

        node.attr('opacity', function(n) { return connected.has(n.id) ? 1 : 0.1; });
        link.attr('opacity', function(l) {
            var s = l.source.id !== undefined ? l.source.id : l.source;
            var t = l.target.id !== undefined ? l.target.id : l.target;
            return (s === d.id || t === d.id) ? 0.9 : 0.03;
        });
        linkLabel.attr('opacity', function(l) {
            var s = l.source.id !== undefined ? l.source.id : l.source;
            var t = l.target.id !== undefined ? l.target.id : l.target;
            return (s === d.id || t === d.id) ? 1 : 0;
        });

        // Show tooltip
        var name = d.name || d.id || '';
        tooltip.innerHTML = '<strong style="color:' + getNodeColor(d) + ';">' + esc(name) + '</strong>';
        if (d.race) tooltip.innerHTML += '<div style="color:var(--text-secondary);font-size:0.85em;">' + esc(d.race) + '</div>';
        if (d.platoon) tooltip.innerHTML += '<div style="color:var(--text-secondary);font-size:0.85em;">' + esc(d.platoon) + '</div>';
        if (d.description) tooltip.innerHTML += '<div style="margin-top:0.3rem;font-size:0.85em;">' + esc(d.description.substring(0, 100)) + '</div>';
        tooltip.style.display = 'block';
        tooltip.style.left = (event.pageX + 12) + 'px';
        tooltip.style.top = (event.pageY + 12) + 'px';
    }).on('mousemove', function(event) {
        tooltip.style.left = (event.pageX + 12) + 'px';
        tooltip.style.top = (event.pageY + 12) + 'px';
    }).on('mouseout', function() {
        node.attr('opacity', 1);
        link.attr('opacity', 0.5);
        linkLabel.attr('opacity', 0);
        tooltip.style.display = 'none';
    });

    // Tick
    sim.on('tick', function() {
        link
            .attr('x1', function(d) { return d.source.x; })
            .attr('y1', function(d) { return d.source.y; })
            .attr('x2', function(d) { return d.target.x; })
            .attr('y2', function(d) { return d.target.y; });

        linkLabel
            .attr('x', function(d) { return (d.source.x + d.target.x) / 2; })
            .attr('y', function(d) { return (d.source.y + d.target.y) / 2 - 6; });

        node.attr('transform', function(d) { return 'translate(' + d.x + ',' + d.y + ')'; });
    });

    // Resize handler
    window.addEventListener('resize', function() {
        var nw = container.clientWidth;
        var nh = container.clientHeight;
        if (nw && nh) {
            svg.attr('width', nw).attr('height', nh);
            sim.force('center', d3.forceCenter(nw / 2, nh / 2));
            sim.alpha(0.3).restart();
        }
    });
}
