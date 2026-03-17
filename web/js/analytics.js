/* === Keroro Archive - MAL Analytics (D3.js Charts) === */

function initAnalytics() {
    loadAnalyticsOverview();
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
