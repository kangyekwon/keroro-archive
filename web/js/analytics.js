/* === Keroro Archive - MAL Analytics (D3.js Charts) === */

function initAnalytics() {
    loadAnalyticsOverview();
    loadExtendedAnalytics();
}

async function loadExtendedAnalytics() {
    Promise.all([
        loadImageGalleries(),
        loadStaffChart(),
        loadFranchiseMap(),
        loadMangaComparison(),
        loadPlatformComparison(),
    ]);
}

async function loadAnalyticsOverview() {
    try {
        var overview = await api('/api/analytics/overview');
        if (!overview.available) {
            document.getElementById('analytics-container').innerHTML =
                '<div class="analytics-empty">' +
                '<h3>MAL 데이터 없음</h3>' +
                '<p>크롤러를 먼저 실행해주세요: <code>python -m crawler.mal_crawler</code></p>' +
                '</div>';
            return;
        }

        // Fill overview cards
        var main = overview.main_anime;
        var el;
        el = document.getElementById('anal-score');
        if (el) el.textContent = main.score ? main.score.toFixed(2) : '--';
        el = document.getElementById('anal-scored-by');
        if (el) el.textContent = (main.scored_by || 0).toLocaleString() + ' 명 평가';
        el = document.getElementById('anal-rank');
        if (el) el.textContent = main.rank ? '#' + main.rank.toLocaleString() : '--';
        el = document.getElementById('anal-popularity');
        if (el) el.textContent = main.popularity ? '#' + main.popularity.toLocaleString() : '--';
        el = document.getElementById('anal-members');
        if (el) el.textContent = (main.members || 0).toLocaleString() + ' 명 등록';
        el = document.getElementById('anal-favorites');
        if (el) el.textContent = (main.favorites || 0).toLocaleString();

        // Load all charts in parallel
        Promise.all([
            loadScoreDistChart(),
            loadViewingStatusChart(),
            loadCharPopularityChart(),
            loadMoviesChart(),
            loadEpisodeTrendChart(),
            loadReviewScoresChart(),
            loadRecommendationsList(),
            loadRecentReviews(),
        ]);

    } catch (e) {
        console.error('Analytics overview failed:', e);
    }
}

/* === Score Distribution Bar Chart === */
async function loadScoreDistChart() {
    try {
        var data = await api('/api/analytics/score-distribution');
        if (!data.scores || data.scores.length === 0) return;

        var container = document.getElementById('chart-score-dist');
        container.innerHTML = '';
        var width = container.clientWidth || 400;
        var height = 280;
        var margin = {top: 20, right: 20, bottom: 40, left: 50};
        var w = width - margin.left - margin.right;
        var h = height - margin.top - margin.bottom;

        var svg = d3.select('#chart-score-dist').append('svg')
            .attr('width', width).attr('height', height);
        var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var scores = data.scores;
        var x = d3.scaleBand().domain(scores.map(function(d) { return d.score; }))
            .range([0, w]).padding(0.2);
        var y = d3.scaleLinear().domain([0, d3.max(scores, function(d) { return d.percentage; })])
            .nice().range([h, 0]);

        // Color scale: low=red, mid=yellow, high=green
        var colorScale = d3.scaleLinear()
            .domain([1, 5, 10])
            .range(['#ff4466', '#ffd700', '#4a7c59']);

        g.selectAll('.bar').data(scores).enter().append('rect')
            .attr('class', 'bar')
            .attr('x', function(d) { return x(d.score); })
            .attr('y', function(d) { return y(d.percentage); })
            .attr('width', x.bandwidth())
            .attr('height', function(d) { return h - y(d.percentage); })
            .attr('fill', function(d) { return colorScale(d.score); })
            .attr('rx', 3)
            .style('cursor', 'pointer')
            .on('mouseover', function(event, d) {
                d3.select(this).attr('opacity', 0.8);
                tooltip.style('display', 'block')
                    .html(d.score + '점: ' + d.votes.toLocaleString() + '표 (' + d.percentage.toFixed(1) + '%)');
            })
            .on('mousemove', function(event) {
                tooltip.style('left', (event.offsetX + 10) + 'px')
                    .style('top', (event.offsetY - 30) + 'px');
            })
            .on('mouseout', function() {
                d3.select(this).attr('opacity', 1);
                tooltip.style('display', 'none');
            });

        // Percentage labels on bars
        g.selectAll('.bar-label').data(scores).enter().append('text')
            .attr('class', 'bar-label')
            .attr('x', function(d) { return x(d.score) + x.bandwidth() / 2; })
            .attr('y', function(d) { return y(d.percentage) - 4; })
            .attr('text-anchor', 'middle')
            .attr('fill', '#ccc')
            .attr('font-size', '10px')
            .text(function(d) { return d.percentage > 2 ? d.percentage.toFixed(1) + '%' : ''; });

        // X axis
        g.append('g').attr('transform', 'translate(0,' + h + ')')
            .call(d3.axisBottom(x))
            .selectAll('text').attr('fill', '#aaa');
        g.selectAll('.domain, .tick line').attr('stroke', '#555');

        // Y axis
        g.append('g').call(d3.axisLeft(y).ticks(5).tickFormat(function(d) { return d + '%'; }))
            .selectAll('text').attr('fill', '#aaa');

        // Tooltip
        var tooltip = d3.select('#chart-score-dist').append('div')
            .attr('class', 'chart-tooltip').style('display', 'none');

    } catch (e) {
        console.error('Score distribution chart failed:', e);
    }
}

/* === Viewing Status Donut Chart === */
async function loadViewingStatusChart() {
    try {
        var data = await api('/api/analytics/viewing-status');
        if (!data.statuses || data.statuses.length === 0) return;

        var container = document.getElementById('chart-viewing-status');
        container.innerHTML = '';
        var width = container.clientWidth || 400;
        var height = 280;
        var radius = Math.min(width, height) / 2 - 20;

        var svg = d3.select('#chart-viewing-status').append('svg')
            .attr('width', width).attr('height', height);
        var g = svg.append('g').attr('transform', 'translate(' + (width / 2) + ',' + (height / 2) + ')');

        var colors = ['#4fc3f7', '#4a7c59', '#ffd700', '#ff4466', '#a29bfe'];
        var color = d3.scaleOrdinal().range(colors);

        var pie = d3.pie().value(function(d) { return d.value; }).sort(null);
        var arc = d3.arc().innerRadius(radius * 0.55).outerRadius(radius);
        var arcHover = d3.arc().innerRadius(radius * 0.55).outerRadius(radius + 8);

        var arcs = g.selectAll('.arc').data(pie(data.statuses)).enter().append('g').attr('class', 'arc');

        arcs.append('path')
            .attr('d', arc)
            .attr('fill', function(d, i) { return colors[i]; })
            .attr('stroke', '#1a1a2e')
            .attr('stroke-width', 2)
            .style('cursor', 'pointer')
            .on('mouseover', function(event, d) {
                d3.select(this).transition().duration(200).attr('d', arcHover);
                tooltip.style('display', 'block')
                    .html(d.data.label_kr + ': ' + d.data.value.toLocaleString() + '명');
            })
            .on('mousemove', function(event) {
                tooltip.style('left', (event.offsetX + 10) + 'px')
                    .style('top', (event.offsetY - 30) + 'px');
            })
            .on('mouseout', function() {
                d3.select(this).transition().duration(200).attr('d', arc);
                tooltip.style('display', 'none');
            });

        // Center text
        g.append('text').attr('text-anchor', 'middle').attr('dy', '-0.2em')
            .attr('fill', '#fff').attr('font-size', '18px').attr('font-weight', 'bold')
            .text(data.total.toLocaleString());
        g.append('text').attr('text-anchor', 'middle').attr('dy', '1.2em')
            .attr('fill', '#aaa').attr('font-size', '12px').text('전체 유저');

        // Legend
        var legend = d3.select('#chart-viewing-status').append('div').attr('class', 'chart-legend');
        data.statuses.forEach(function(s, i) {
            var pct = data.total > 0 ? ((s.value / data.total) * 100).toFixed(1) : '0';
            legend.append('div').attr('class', 'chart-legend-item')
                .html('<span class="chart-legend-dot" style="background:' + colors[i] + '"></span>' +
                    s.label_kr + ' <span class="chart-legend-value">' + pct + '%</span>');
        });

        var tooltip = d3.select('#chart-viewing-status').append('div')
            .attr('class', 'chart-tooltip').style('display', 'none');

    } catch (e) {
        console.error('Viewing status chart failed:', e);
    }
}

/* === Character Popularity Horizontal Bar Chart === */
async function loadCharPopularityChart() {
    try {
        var data = await api('/api/analytics/characters?limit=20');
        if (!data.characters || data.characters.length === 0) return;

        var chars = data.characters.filter(function(c) { return c.favorites > 0; });
        if (chars.length === 0) return;

        var container = document.getElementById('chart-char-popularity');
        container.innerHTML = '';
        var width = container.clientWidth || 700;
        var barHeight = 28;
        var margin = {top: 10, right: 60, bottom: 20, left: 160};
        var height = chars.length * barHeight + margin.top + margin.bottom;

        var svg = d3.select('#chart-char-popularity').append('svg')
            .attr('width', width).attr('height', height);
        var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var w = width - margin.left - margin.right;
        var x = d3.scaleLinear().domain([0, d3.max(chars, function(d) { return d.favorites; })]).range([0, w]);
        var y = d3.scaleBand().domain(chars.map(function(d) { return d.name; }))
            .range([0, chars.length * barHeight]).padding(0.15);

        // Gradient fill
        var defs = svg.append('defs');
        var gradient = defs.append('linearGradient').attr('id', 'charGradient')
            .attr('x1', '0%').attr('y1', '0%').attr('x2', '100%').attr('y2', '0%');
        gradient.append('stop').attr('offset', '0%').attr('stop-color', '#4a7c59');
        gradient.append('stop').attr('offset', '100%').attr('stop-color', '#ffd700');

        g.selectAll('.bar').data(chars).enter().append('rect')
            .attr('x', 0)
            .attr('y', function(d) { return y(d.name); })
            .attr('width', function(d) { return x(d.favorites); })
            .attr('height', y.bandwidth())
            .attr('fill', 'url(#charGradient)')
            .attr('rx', 4);

        // Labels (character names)
        g.selectAll('.name-label').data(chars).enter().append('text')
            .attr('x', -8)
            .attr('y', function(d) { return y(d.name) + y.bandwidth() / 2; })
            .attr('text-anchor', 'end')
            .attr('dominant-baseline', 'middle')
            .attr('fill', '#ddd')
            .attr('font-size', '12px')
            .text(function(d) { return d.name; });

        // Value labels
        g.selectAll('.val-label').data(chars).enter().append('text')
            .attr('x', function(d) { return x(d.favorites) + 6; })
            .attr('y', function(d) { return y(d.name) + y.bandwidth() / 2; })
            .attr('dominant-baseline', 'middle')
            .attr('fill', '#ffd700')
            .attr('font-size', '11px')
            .attr('font-weight', 'bold')
            .text(function(d) { return d.favorites.toLocaleString(); });

        // Role badges
        g.selectAll('.role-badge').data(chars).enter().append('text')
            .attr('x', function(d) { return x(d.favorites) + 50; })
            .attr('y', function(d) { return y(d.name) + y.bandwidth() / 2; })
            .attr('dominant-baseline', 'middle')
            .attr('fill', function(d) { return d.role === 'Main' ? '#4fc3f7' : '#888'; })
            .attr('font-size', '9px')
            .text(function(d) { return d.role === 'Main' ? 'MAIN' : 'SUB'; });

    } catch (e) {
        console.error('Character popularity chart failed:', e);
    }
}

/* === Movie Comparison Grouped Bar Chart === */
async function loadMoviesChart() {
    try {
        var data = await api('/api/analytics/movies');
        if (!data.movies || data.movies.length === 0) {
            document.getElementById('chart-movies').innerHTML = '<p class="analytics-empty-text">극장판 데이터 없음</p>';
            return;
        }

        var movies = data.movies;
        var container = document.getElementById('chart-movies');
        container.innerHTML = '';
        var width = container.clientWidth || 600;
        var height = 300;
        var margin = {top: 20, right: 30, bottom: 80, left: 50};
        var w = width - margin.left - margin.right;
        var h = height - margin.top - margin.bottom;

        var svg = d3.select('#chart-movies').append('svg')
            .attr('width', width).attr('height', height);
        var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var x = d3.scaleBand().domain(movies.map(function(d) {
            return d.title_english || d.title;
        })).range([0, w]).padding(0.3);

        var y = d3.scaleLinear().domain([0, 10]).range([h, 0]);

        // Bars
        g.selectAll('.bar').data(movies).enter().append('rect')
            .attr('x', function(d) { return x(d.title_english || d.title); })
            .attr('y', function(d) { return d.score ? y(d.score) : h; })
            .attr('width', x.bandwidth())
            .attr('height', function(d) { return d.score ? h - y(d.score) : 0; })
            .attr('fill', function(d, i) {
                var colors = ['#4a7c59', '#4fc3f7', '#ffd700', '#ff9f43', '#a29bfe'];
                return colors[i % colors.length];
            })
            .attr('rx', 4);

        // Score labels
        g.selectAll('.score-label').data(movies).enter().append('text')
            .attr('x', function(d) { return x(d.title_english || d.title) + x.bandwidth() / 2; })
            .attr('y', function(d) { return d.score ? y(d.score) - 6 : h; })
            .attr('text-anchor', 'middle')
            .attr('fill', '#ffd700')
            .attr('font-size', '13px')
            .attr('font-weight', 'bold')
            .text(function(d) { return d.score ? d.score.toFixed(2) : 'N/A'; });

        // X axis
        g.append('g').attr('transform', 'translate(0,' + h + ')')
            .call(d3.axisBottom(x))
            .selectAll('text')
            .attr('fill', '#aaa')
            .attr('font-size', '10px')
            .attr('transform', 'rotate(-25)')
            .attr('text-anchor', 'end');
        g.selectAll('.domain, .tick line').attr('stroke', '#555');

        // Y axis
        g.append('g').call(d3.axisLeft(y).ticks(5))
            .selectAll('text').attr('fill', '#aaa');

        // Members count below bars
        g.selectAll('.members-label').data(movies).enter().append('text')
            .attr('x', function(d) { return x(d.title_english || d.title) + x.bandwidth() / 2; })
            .attr('y', h + 14)
            .attr('text-anchor', 'middle')
            .attr('fill', '#888')
            .attr('font-size', '9px')
            .text(function(d) { return d.members ? d.members.toLocaleString() + '명' : ''; });

    } catch (e) {
        console.error('Movies chart failed:', e);
    }
}

/* === Episode Rating Trend Line Chart === */
async function loadEpisodeTrendChart() {
    try {
        var data = await api('/api/analytics/episodes');
        if (!data.episodes || data.episodes.length === 0) return;

        // Filter episodes with scores and sort by mal_id
        var episodes = data.episodes.filter(function(ep) { return ep.score && ep.score > 0; })
            .sort(function(a, b) { return a.mal_id - b.mal_id; });
        if (episodes.length === 0) {
            document.getElementById('chart-episode-trend').innerHTML = '<p class="analytics-empty-text">에피소드 평점 데이터 없음</p>';
            return;
        }

        var container = document.getElementById('chart-episode-trend');
        container.innerHTML = '';
        var width = container.clientWidth || 800;
        var height = 350;
        var margin = {top: 20, right: 30, bottom: 50, left: 45};
        var w = width - margin.left - margin.right;
        var h = height - margin.top - margin.bottom;

        var svg = d3.select('#chart-episode-trend').append('svg')
            .attr('width', width).attr('height', height);
        var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var x = d3.scaleLinear().domain([1, d3.max(episodes, function(d) { return d.mal_id; })]).range([0, w]);
        var y = d3.scaleLinear().domain([
            d3.min(episodes, function(d) { return d.score; }) - 0.5,
            d3.max(episodes, function(d) { return d.score; }) + 0.3
        ]).range([h, 0]);

        // Season backgrounds
        var seasons = [
            {start: 1, end: 51, label: 'S1', color: 'rgba(74,124,89,0.1)'},
            {start: 52, end: 103, label: 'S2', color: 'rgba(79,195,247,0.1)'},
            {start: 104, end: 155, label: 'S3', color: 'rgba(255,215,0,0.1)'},
            {start: 156, end: 206, label: 'S4', color: 'rgba(255,159,67,0.1)'},
            {start: 207, end: 256, label: 'S5', color: 'rgba(162,155,254,0.1)'},
            {start: 257, end: 307, label: 'S6', color: 'rgba(253,121,168,0.1)'},
            {start: 308, end: 358, label: 'S7', color: 'rgba(85,239,196,0.1)'},
        ];
        seasons.forEach(function(s) {
            g.append('rect')
                .attr('x', x(s.start)).attr('y', 0)
                .attr('width', x(s.end) - x(s.start)).attr('height', h)
                .attr('fill', s.color);
            g.append('text')
                .attr('x', x((s.start + s.end) / 2))
                .attr('y', 14)
                .attr('text-anchor', 'middle')
                .attr('fill', '#666')
                .attr('font-size', '11px')
                .attr('font-weight', 'bold')
                .text(s.label);
        });

        // Moving average line (window=10)
        var windowSize = 10;
        var avgData = [];
        for (var i = 0; i < episodes.length; i++) {
            var start = Math.max(0, i - Math.floor(windowSize / 2));
            var end = Math.min(episodes.length, i + Math.ceil(windowSize / 2));
            var slice = episodes.slice(start, end);
            var avg = d3.mean(slice, function(d) { return d.score; });
            avgData.push({mal_id: episodes[i].mal_id, score: avg});
        }

        // Area under the average line
        var area = d3.area()
            .x(function(d) { return x(d.mal_id); })
            .y0(h)
            .y1(function(d) { return y(d.score); })
            .curve(d3.curveMonotoneX);
        g.append('path').datum(avgData)
            .attr('d', area)
            .attr('fill', 'rgba(74,124,89,0.15)');

        // Scatter dots for individual episodes
        g.selectAll('.ep-dot').data(episodes).enter().append('circle')
            .attr('class', 'ep-dot')
            .attr('cx', function(d) { return x(d.mal_id); })
            .attr('cy', function(d) { return y(d.score); })
            .attr('r', 2.5)
            .attr('fill', function(d) {
                if (d.filler) return '#ff9f43';
                if (d.recap) return '#ff4466';
                return 'rgba(106,173,122,0.6)';
            })
            .style('cursor', 'pointer')
            .on('mouseover', function(event, d) {
                d3.select(this).attr('r', 5).attr('fill', '#ffd700');
                tooltip.style('display', 'block')
                    .html('EP ' + d.mal_id + ': ' + esc(d.title || d.title_japanese || '') +
                        '<br>Score: ' + (d.score ? d.score.toFixed(2) : 'N/A') +
                        (d.filler ? '<br><span style="color:#ff9f43">FILLER</span>' : '') +
                        (d.recap ? '<br><span style="color:#ff4466">RECAP</span>' : ''));
            })
            .on('mousemove', function(event) {
                tooltip.style('left', (event.offsetX + 15) + 'px')
                    .style('top', (event.offsetY - 40) + 'px');
            })
            .on('mouseout', function(event, d) {
                d3.select(this).attr('r', 2.5)
                    .attr('fill', d.filler ? '#ff9f43' : (d.recap ? '#ff4466' : 'rgba(106,173,122,0.6)'));
                tooltip.style('display', 'none');
            });

        // Moving average line
        var line = d3.line()
            .x(function(d) { return x(d.mal_id); })
            .y(function(d) { return y(d.score); })
            .curve(d3.curveMonotoneX);
        g.append('path').datum(avgData)
            .attr('d', line)
            .attr('fill', 'none')
            .attr('stroke', '#4a7c59')
            .attr('stroke-width', 2.5);

        // Axes
        g.append('g').attr('transform', 'translate(0,' + h + ')')
            .call(d3.axisBottom(x).ticks(15).tickFormat(function(d) { return 'EP' + d; }))
            .selectAll('text').attr('fill', '#aaa').attr('font-size', '9px')
            .attr('transform', 'rotate(-30)').attr('text-anchor', 'end');
        g.selectAll('.domain, .tick line').attr('stroke', '#555');

        g.append('g').call(d3.axisLeft(y).ticks(6))
            .selectAll('text').attr('fill', '#aaa');

        // Legend
        var legendG = svg.append('g').attr('transform', 'translate(' + (margin.left + 10) + ',' + (height - 15) + ')');
        var legendItems = [
            {color: 'rgba(106,173,122,0.6)', label: '일반'},
            {color: '#ff9f43', label: '필러'},
            {color: '#ff4466', label: '총집편'},
            {color: '#4a7c59', label: '이동평균'},
        ];
        legendItems.forEach(function(item, i) {
            legendG.append('circle').attr('cx', i * 80).attr('cy', 0).attr('r', 4).attr('fill', item.color);
            legendG.append('text').attr('x', i * 80 + 8).attr('y', 4)
                .attr('fill', '#aaa').attr('font-size', '10px').text(item.label);
        });

        var tooltip = d3.select('#chart-episode-trend').append('div')
            .attr('class', 'chart-tooltip').style('display', 'none');

    } catch (e) {
        console.error('Episode trend chart failed:', e);
    }
}

/* === Review Scores Distribution === */
async function loadReviewScoresChart() {
    try {
        var data = await api('/api/analytics/review-scores');
        if (!data.scores || data.scores.length === 0) {
            document.getElementById('chart-review-scores').innerHTML =
                '<p class="analytics-empty-text">리뷰 데이터 없음</p>';
            return;
        }

        var container = document.getElementById('chart-review-scores');
        container.innerHTML = '';
        var width = container.clientWidth || 350;
        var height = 250;
        var margin = {top: 20, right: 20, bottom: 40, left: 40};
        var w = width - margin.left - margin.right;
        var h = height - margin.top - margin.bottom;

        var svg = d3.select('#chart-review-scores').append('svg')
            .attr('width', width).attr('height', height);
        var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var scores = data.scores;
        var x = d3.scaleBand().domain(scores.map(function(d) { return d.score; }))
            .range([0, w]).padding(0.25);
        var y = d3.scaleLinear().domain([0, d3.max(scores, function(d) { return d.count; })])
            .nice().range([h, 0]);

        g.selectAll('.bar').data(scores).enter().append('rect')
            .attr('x', function(d) { return x(d.score); })
            .attr('y', function(d) { return y(d.count); })
            .attr('width', x.bandwidth())
            .attr('height', function(d) { return h - y(d.count); })
            .attr('fill', '#a29bfe')
            .attr('rx', 3);

        g.selectAll('.count-label').data(scores).enter().append('text')
            .attr('x', function(d) { return x(d.score) + x.bandwidth() / 2; })
            .attr('y', function(d) { return y(d.count) - 4; })
            .attr('text-anchor', 'middle')
            .attr('fill', '#ddd')
            .attr('font-size', '11px')
            .text(function(d) { return d.count; });

        g.append('g').attr('transform', 'translate(0,' + h + ')')
            .call(d3.axisBottom(x))
            .selectAll('text').attr('fill', '#aaa');
        g.selectAll('.domain, .tick line').attr('stroke', '#555');

        g.append('g').call(d3.axisLeft(y).ticks(5))
            .selectAll('text').attr('fill', '#aaa');

    } catch (e) {
        console.error('Review scores chart failed:', e);
    }
}

/* === Recommendations List === */
async function loadRecommendationsList() {
    try {
        var data = await api('/api/analytics/recommendations?limit=10');
        if (!data.recommendations || data.recommendations.length === 0) {
            document.getElementById('list-recommendations').innerHTML =
                '<p class="analytics-empty-text">추천 데이터 없음</p>';
            return;
        }

        var html = '';
        data.recommendations.forEach(function(rec, i) {
            html += '<div class="rec-item">' +
                '<span class="rec-rank">' + (i + 1) + '</span>' +
                '<img class="rec-img" src="' + esc(rec.image_url) + '" alt="' + esc(rec.title) + '" loading="lazy" onerror="this.style.display=\'none\'">' +
                '<div class="rec-info">' +
                '<span class="rec-title">' + esc(rec.title) + '</span>' +
                '<span class="rec-votes">' + rec.votes + ' votes</span>' +
                '</div>' +
                '</div>';
        });

        document.getElementById('list-recommendations').innerHTML = html;
    } catch (e) {
        console.error('Recommendations list failed:', e);
    }
}

/* === Staff Position Distribution Chart === */
async function loadStaffChart() {
    try {
        var data = await api('/api/analytics/staff');
        if (!data.position_counts || data.position_counts.length === 0) return;

        var container = document.getElementById('chart-staff');
        if (!container) return;
        container.innerHTML = '';

        var counts = data.position_counts.slice(0, 15);
        var width = container.clientWidth || 600;
        var barHeight = 26;
        var margin = {top: 10, right: 60, bottom: 20, left: 180};
        var height = counts.length * barHeight + margin.top + margin.bottom;

        var svg = d3.select('#chart-staff').append('svg')
            .attr('width', width).attr('height', height);
        var g = svg.append('g').attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var w = width - margin.left - margin.right;
        var x = d3.scaleLinear().domain([0, d3.max(counts, function(d) { return d[1]; })]).range([0, w]);
        var y = d3.scaleBand().domain(counts.map(function(d) { return d[0]; }))
            .range([0, counts.length * barHeight]).padding(0.15);

        g.selectAll('.bar').data(counts).enter().append('rect')
            .attr('x', 0)
            .attr('y', function(d) { return y(d[0]); })
            .attr('width', function(d) { return x(d[1]); })
            .attr('height', y.bandwidth())
            .attr('fill', '#a29bfe')
            .attr('rx', 4);

        g.selectAll('.name-label').data(counts).enter().append('text')
            .attr('x', -8).attr('y', function(d) { return y(d[0]) + y.bandwidth() / 2; })
            .attr('text-anchor', 'end').attr('dominant-baseline', 'middle')
            .attr('fill', '#ddd').attr('font-size', '11px')
            .text(function(d) { return d[0]; });

        g.selectAll('.val-label').data(counts).enter().append('text')
            .attr('x', function(d) { return x(d[1]) + 6; })
            .attr('y', function(d) { return y(d[0]) + y.bandwidth() / 2; })
            .attr('dominant-baseline', 'middle')
            .attr('fill', '#a29bfe').attr('font-size', '11px').attr('font-weight', 'bold')
            .text(function(d) { return d[1] + '명'; });

    } catch (e) {
        console.error('Staff chart failed:', e);
    }
}

/* === Franchise Map (Related Works) === */
async function loadFranchiseMap() {
    try {
        var data = await api('/api/analytics/relations');
        if (!data.relations || data.relations.length === 0) return;

        var container = document.getElementById('chart-franchise');
        if (!container) return;
        container.innerHTML = '';

        var relationColors = {
            'Sequel': '#4fc3f7', 'Prequel': '#4fc3f7',
            'Side story': '#ffd700', 'Alternative version': '#ff9f43',
            'Adaptation': '#4a7c59', 'Summary': '#a29bfe',
            'Spin-off': '#fd79a8', 'Other': '#888',
            'Character': '#55efc4', 'Full story': '#e17055',
        };

        // Group by type
        var grouped = data.grouped || {};
        var html = '<div class="franchise-grid">';

        // Center node
        html += '<div class="franchise-center">' +
            '<div class="franchise-node franchise-node--main">' +
            '<span class="franchise-node-type">TV</span>' +
            '<span class="franchise-node-title">Keroro Gunsou</span>' +
            '<span class="franchise-node-detail">358 eps (2004-2011)</span>' +
            '</div></div>';

        // Related works
        html += '<div class="franchise-branches">';
        Object.keys(grouped).forEach(function(relType) {
            var items = grouped[relType];
            var color = relationColors[relType] || '#888';
            html += '<div class="franchise-branch">';
            html += '<div class="franchise-branch-label" style="border-color:' + color + '">' + relType + ' (' + items.length + ')</div>';
            items.forEach(function(item) {
                var typeIcon = item.type === 'anime' ? '&#x1F4FA;' : '&#x1F4D6;';
                html += '<div class="franchise-node" style="border-left: 3px solid ' + color + '">' +
                    '<span class="franchise-node-type">' + typeIcon + ' ' + esc(item.type) + '</span>' +
                    '<span class="franchise-node-title">' + esc(item.name) + '</span>' +
                    '</div>';
            });
            html += '</div>';
        });
        html += '</div></div>';

        container.innerHTML = html;

    } catch (e) {
        console.error('Franchise map failed:', e);
    }
}

/* === Manga vs Anime Comparison === */
async function loadMangaComparison() {
    try {
        var data = await api('/api/analytics/manga');
        if (!data.available) return;

        var container = document.getElementById('chart-manga');
        if (!container) return;

        var manga = data.manga;
        var html = '<div class="manga-comparison">';

        // Manga info card
        html += '<div class="manga-info-card">';
        if (manga.image_url) {
            html += '<img class="manga-cover" src="' + esc(manga.image_url) + '" alt="manga cover" loading="lazy">';
        }
        html += '<div class="manga-details">' +
            '<h4 class="manga-title">' + esc(manga.title_japanese || manga.title) + '</h4>' +
            '<div class="manga-meta">' +
            '<span>Score: <strong style="color:#ffd700">' + (manga.score || 'N/A') + '</strong></span>' +
            '<span>Chapters: <strong>' + (manga.chapters || '300+') + '</strong></span>' +
            '<span>Volumes: <strong>' + (manga.volumes || '30+') + '</strong></span>' +
            '<span>Members: <strong>' + (manga.members || 0).toLocaleString() + '</strong></span>' +
            '</div>' +
            '<div class="manga-meta">' +
            '<span>Authors: ' + esc(manga.authors || '') + '</span>' +
            '<span>Status: ' + esc(manga.status || '') + '</span>' +
            '</div>' +
            '</div></div>';

        // Anime vs Manga score comparison bar
        html += '<div class="manga-vs-anime">' +
            '<h4>Anime vs Manga</h4>' +
            '<div class="compare-bars">' +
            '<div class="compare-row"><span class="compare-label">Anime</span>' +
            '<div class="compare-bar-wrap"><div class="compare-bar" style="width:' + ((7.71 / 10) * 100) + '%;background:#4a7c59"></div></div>' +
            '<span class="compare-value">7.71</span></div>' +
            '<div class="compare-row"><span class="compare-label">Manga</span>' +
            '<div class="compare-bar-wrap"><div class="compare-bar" style="width:' + (((manga.score || 0) / 10) * 100) + '%;background:#ffd700"></div></div>' +
            '<span class="compare-value">' + (manga.score || 'N/A') + '</span></div>' +
            '</div></div>';

        // Manga characters
        if (data.characters && data.characters.length > 0) {
            html += '<div class="manga-chars"><h4>Manga Characters (' + data.character_count + ')</h4><div class="manga-chars-grid">';
            data.characters.slice(0, 20).forEach(function(c) {
                html += '<div class="manga-char-item">' +
                    '<img class="manga-char-img" src="' + esc(c.image_url || '') + '" alt="' + esc(c.name) + '" loading="lazy" onerror="this.style.display=\'none\'">' +
                    '<span class="manga-char-name">' + esc(c.name) + '</span>' +
                    '<span class="manga-char-role ' + (c.role === 'Main' ? 'manga-char-role--main' : '') + '">' + c.role + '</span>' +
                    '</div>';
            });
            html += '</div></div>';
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (e) {
        console.error('Manga comparison failed:', e);
    }
}

/* === Platform Comparison (MAL vs AniList) === */
async function loadPlatformComparison() {
    try {
        var data = await api('/api/analytics/comparison');
        var container = document.getElementById('chart-platform');
        if (!container) return;

        var mal = data.mal;
        var anilist = data.anilist;
        if (!mal && !anilist) {
            container.innerHTML = '<p class="analytics-empty-text">비교 데이터 없음</p>';
            return;
        }

        // Build comparison table
        var html = '<div class="platform-comparison">';

        // Score comparison chart
        html += '<div class="platform-scores">';
        html += '<h4>Score Comparison</h4>';
        html += '<div class="platform-score-cards">';

        if (mal) {
            html += '<div class="platform-card platform-card--mal">' +
                '<div class="platform-card-logo">MAL</div>' +
                '<div class="platform-card-score">' + (mal.score || '--') + '<span>/10</span></div>' +
                '<div class="platform-card-detail">' + (mal.scored_by || 0).toLocaleString() + ' ratings</div>' +
                '<div class="platform-card-detail">Rank #' + (mal.rank || '--') + '</div>' +
                '<div class="platform-card-detail">Popularity #' + (mal.popularity || '--') + '</div>' +
                '<div class="platform-card-detail">' + (mal.members || 0).toLocaleString() + ' members</div>' +
                '</div>';
        }

        if (anilist) {
            html += '<div class="platform-card platform-card--anilist">' +
                '<div class="platform-card-logo">AniList</div>' +
                '<div class="platform-card-score">' + (anilist.average_score || '--') + '<span>/100</span></div>' +
                '<div class="platform-card-detail">Mean: ' + (anilist.mean_score || '--') + '</div>' +
                '<div class="platform-card-detail">Popularity #' + (anilist.popularity || '--').toLocaleString() + '</div>' +
                '<div class="platform-card-detail">' + (anilist.favourites || 0).toLocaleString() + ' favourites</div>' +
                '</div>';
        }

        if (data.manga) {
            html += '<div class="platform-card platform-card--manga">' +
                '<div class="platform-card-logo">Manga</div>' +
                '<div class="platform-card-score">' + (data.manga.score || '--') + '<span>/10</span></div>' +
                '<div class="platform-card-detail">' + (data.manga.scored_by || 0).toLocaleString() + ' ratings</div>' +
                '<div class="platform-card-detail">Rank #' + (data.manga.rank || '--') + '</div>' +
                '<div class="platform-card-detail">' + (data.manga.chapters || '300+') + ' chapters</div>' +
                '<div class="platform-card-detail">' + (data.manga.volumes || '30+') + ' volumes</div>' +
                '</div>';
        }

        html += '</div></div>';

        // Character popularity comparison
        if (data.character_comparison) {
            html += '<div class="platform-chars">';
            html += '<h4>Character Popularity: MAL vs AniList</h4>';
            html += '<div class="platform-chars-grid">';

            html += '<div class="platform-chars-col"><h5>MAL (Favorites)</h5>';
            (data.character_comparison.mal || []).forEach(function(c, i) {
                var hasImg = c.image_url && c.image_url.indexOf('questionmark') < 0;
                html += '<div class="platform-char-row">' +
                    '<span class="platform-char-rank">#' + (i + 1) + '</span>' +
                    (hasImg ? '<img class="platform-char-avatar" src="' + esc(c.image_url) + '" alt="' + esc(c.name) + '" loading="lazy" onerror="this.style.display=\'none\'">' : '') +
                    '<span class="platform-char-name">' + esc(c.name) + '</span>' +
                    '<span class="platform-char-value" style="color:#4a7c59">' + (c.favorites || 0).toLocaleString() + '</span>' +
                    '</div>';
            });
            html += '</div>';

            html += '<div class="platform-chars-col"><h5>AniList (Favourites)</h5>';
            (data.character_comparison.anilist || []).forEach(function(c, i) {
                var hasImg = c.image_url && c.image_url.indexOf('questionmark') < 0;
                html += '<div class="platform-char-row">' +
                    '<span class="platform-char-rank">#' + (i + 1) + '</span>' +
                    (hasImg ? '<img class="platform-char-avatar" src="' + esc(c.image_url) + '" alt="' + esc(c.name) + '" loading="lazy" onerror="this.style.display=\'none\'">' : '') +
                    '<span class="platform-char-name">' + esc(c.name) + '</span>' +
                    '<span class="platform-char-value" style="color:#4fc3f7">' + (c.favourites || 0).toLocaleString() + '</span>' +
                    '</div>';
            });
            html += '</div>';

            html += '</div></div>';
        }

        html += '</div>';
        container.innerHTML = html;

    } catch (e) {
        console.error('Platform comparison failed:', e);
    }
}

/* === Image Galleries (Banner, Posters, Characters, Staff) === */
async function loadImageGalleries() {
    try {
        var data = await api('/api/analytics/gallery');
        if (!data) return;

        // AniList Banner
        if (data.anilist_banner && data.anilist_banner.banner_image) {
            var bannerEl = document.getElementById('anilist-banner');
            if (bannerEl) {
                bannerEl.innerHTML =
                    '<div class="anilist-banner-img" style="background-image:url(\'' + esc(data.anilist_banner.banner_image) + '\')">' +
                    '<div class="anilist-banner-overlay">' +
                    '<img class="anilist-banner-cover" src="' + esc(data.anilist_banner.cover_image || '') + '" alt="cover" loading="lazy">' +
                    '<div class="anilist-banner-info">' +
                    '<h3>' + esc(data.anilist_banner.title_romaji || 'Keroro Gunsou') + '</h3>' +
                    '<p>' + data.total_images + '+ images from MAL & AniList</p>' +
                    '</div>' +
                    '</div>' +
                    '</div>';
            }
        }

        // Anime Poster Gallery
        if (data.anime_posters && data.anime_posters.length > 0) {
            var galleryEl = document.getElementById('anime-poster-gallery');
            if (galleryEl) {
                var html = '';
                data.anime_posters.forEach(function(a) {
                    if (!a.image_url) return;
                    var title = a.title_english || a.title || '';
                    var scoreStr = a.score ? a.score.toFixed(2) : 'N/A';
                    html += '<div class="poster-card">' +
                        '<img class="poster-img" src="' + esc(a.image_url) + '" alt="' + esc(title) + '" loading="lazy" onerror="this.parentElement.style.display=\'none\'">' +
                        '<div class="poster-info">' +
                        '<span class="poster-type">' + esc(a.type || a.key || '') + '</span>' +
                        '<span class="poster-title">' + esc(title) + '</span>' +
                        '<span class="poster-score">' + scoreStr + '</span>' +
                        (a.year ? '<span class="poster-year">' + a.year + '</span>' : '') +
                        '</div>' +
                        '</div>';
                });
                galleryEl.innerHTML = html;
            }
        }

        // MAL Character Image Gallery
        if (data.mal_characters && data.mal_characters.length > 0) {
            var malGallery = document.getElementById('mal-char-gallery');
            if (malGallery) {
                var html = '';
                data.mal_characters.forEach(function(c) {
                    if (!c.image_url || c.image_url.indexOf('questionmark') >= 0) return;
                    html += '<div class="char-gallery-item">' +
                        '<img class="char-gallery-img" src="' + esc(c.image_url) + '" alt="' + esc(c.name) + '" loading="lazy" onerror="this.parentElement.style.display=\'none\'">' +
                        '<div class="char-gallery-info">' +
                        '<span class="char-gallery-name">' + esc(c.name) + '</span>' +
                        '<span class="char-gallery-fav">' + (c.favorites || 0).toLocaleString() + ' fav</span>' +
                        '</div>' +
                        '</div>';
                });
                malGallery.innerHTML = html;
            }
        }

        // AniList Character Image Gallery
        if (data.anilist_characters && data.anilist_characters.length > 0) {
            var aniGallery = document.getElementById('anilist-char-gallery');
            if (aniGallery) {
                var html = '';
                data.anilist_characters.forEach(function(c) {
                    if (!c.image_url) return;
                    html += '<div class="char-gallery-item">' +
                        '<img class="char-gallery-img" src="' + esc(c.image_url) + '" alt="' + esc(c.name) + '" loading="lazy" onerror="this.parentElement.style.display=\'none\'">' +
                        '<div class="char-gallery-info">' +
                        '<span class="char-gallery-name">' + esc(c.name) + '</span>' +
                        (c.name_native ? '<span class="char-gallery-native">' + esc(c.name_native) + '</span>' : '') +
                        '<span class="char-gallery-fav">' + (c.favourites || 0).toLocaleString() + ' fav</span>' +
                        '</div>' +
                        '</div>';
                });
                aniGallery.innerHTML = html;
            }
        }

        // Staff Photo Gallery
        var staffData = await api('/api/analytics/staff');
        if (staffData && staffData.staff_with_images && staffData.staff_with_images.length > 0) {
            var staffGallery = document.getElementById('staff-photo-gallery');
            if (staffGallery) {
                var html = '<div class="staff-gallery-count">' + staffData.staff_with_images.length + '명의 제작진 사진</div>';
                html += '<div class="staff-gallery-grid">';
                staffData.staff_with_images.forEach(function(s) {
                    var positions = (s.positions || []).slice(0, 2).join(', ');
                    html += '<div class="staff-gallery-item">' +
                        '<img class="staff-gallery-img" src="' + esc(s.image_url) + '" alt="' + esc(s.name) + '" loading="lazy" onerror="this.parentElement.style.display=\'none\'">' +
                        '<div class="staff-gallery-info">' +
                        '<span class="staff-gallery-name">' + esc(s.name) + '</span>' +
                        '<span class="staff-gallery-role">' + esc(positions) + '</span>' +
                        '</div>' +
                        '</div>';
                });
                html += '</div>';
                staffGallery.innerHTML = html;
            }
        }

    } catch (e) {
        console.error('Image galleries failed:', e);
    }
}

/* === Recent Reviews === */
async function loadRecentReviews() {
    try {
        var data = await api('/api/analytics/reviews?limit=10');
        if (!data.reviews || data.reviews.length === 0) {
            document.getElementById('analytics-reviews').innerHTML =
                '<p class="analytics-empty-text">리뷰 데이터 없음</p>';
            return;
        }

        var html = '';
        data.reviews.forEach(function(rev) {
            var dateStr = rev.date ? new Date(rev.date).toLocaleDateString('ko-KR') : '';
            var tags = (rev.tags || []).join(', ');
            var scoreColor = rev.score >= 7 ? '#4a7c59' : (rev.score >= 5 ? '#ffd700' : '#ff4466');
            var reviewText = rev.review || '';
            if (reviewText.length > 300) reviewText = reviewText.substring(0, 300) + '...';

            html += '<div class="review-card">' +
                '<div class="review-header">' +
                '<span class="review-user">' + esc(rev.username) + '</span>' +
                '<span class="review-score" style="color:' + scoreColor + '">' + rev.score + '/10</span>' +
                '<span class="review-date">' + dateStr + '</span>' +
                (rev.is_spoiler ? '<span class="review-tag review-tag--spoiler">SPOILER</span>' : '') +
                (rev.is_preliminary ? '<span class="review-tag review-tag--prelim">PRELIMINARY</span>' : '') +
                '</div>' +
                (tags ? '<div class="review-tags">' + esc(tags) + '</div>' : '') +
                '<div class="review-text">' + esc(reviewText) + '</div>' +
                (rev.episodes_watched ? '<div class="review-eps">시청 에피소드: ' + rev.episodes_watched + '/358</div>' : '') +
                '</div>';
        });

        document.getElementById('analytics-reviews').innerHTML = html;
    } catch (e) {
        console.error('Recent reviews failed:', e);
    }
}
