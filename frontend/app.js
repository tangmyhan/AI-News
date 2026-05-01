const API_BASE_URL = 'http://localhost:8000';
let impactChartInstance = null;

// DOM Elements
const els = {
    themeToggle: document.getElementById('theme-toggle'),
    statTotal: document.getElementById('stat-total'),
    statRelevantPct: document.getElementById('stat-relevant-pct'),
    statRelevantCount: document.getElementById('stat-relevant-count'),
    statNegativePct: document.getElementById('stat-negative-pct'),
    
    // Filters
    searchInput: document.getElementById('search-input'),
    impactFilter: document.getElementById('impact-filter'),
    relevanceFilter: document.getElementById('relevance-filter'),
    
    articleList: document.getElementById('article-list'),
    resultCount: document.getElementById('result-count'),
    
    // Modal
    modal: document.getElementById('article-modal'),
    closeModalBtn: document.getElementById('close-modal'),
    modalSource: document.getElementById('modal-source'),
    modalImpact: document.getElementById('modal-impact'),
    modalTitle: document.getElementById('modal-title'),
    modalSummarySection: document.getElementById('modal-summary-section'),
    modalSummaryList: document.getElementById('modal-summary-list'),
    modalReasonSection: document.getElementById('modal-reason-section'),
    modalReasonText: document.getElementById('modal-reason-text'),
    modalCategories: document.getElementById('modal-categories'),
    modalEntities: document.getElementById('modal-entities'),
    modalTopics: document.getElementById('modal-topics'),
    modalLink: document.getElementById('modal-link')
};

// State
let allArticles = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupThemeToggle();
    setupEventListeners();
    fetchData();
});

function setupThemeToggle() {
    const isDark = document.body.classList.contains('dark-mode');
    els.themeToggle.innerHTML = isDark ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    
    els.themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isNowDark = document.body.classList.contains('dark-mode');
        els.themeToggle.innerHTML = isNowDark ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
        if(impactChartInstance) renderChart(impactChartInstance.data.datasets[0].data);
    });
}

function setupEventListeners() {
    els.impactFilter.addEventListener('change', fetchNews);
    
    const delayedFetch = debounce(fetchNews, 500);
    els.searchInput.addEventListener('input', delayedFetch);
    els.relevanceFilter.addEventListener('input', delayedFetch);
    
    // Modal
    els.closeModalBtn.addEventListener('click', closeModal);
    els.modal.addEventListener('click', (e) => {
        if(e.target === els.modal) closeModal();
    });
}

async function fetchData() {
    fetchStats();
    fetchNews();
}

async function fetchStats() {
    try {
        const res = await fetch(`${API_BASE_URL}/stats`);
        const data = await res.json();
        
        els.statTotal.innerText = data.total_articles;
        els.statRelevantPct.innerText = `${data.pct_relevant}%`;
        els.statRelevantCount.innerText = `${data.relevant_articles} articles`;
        els.statNegativePct.innerText = `${data.pct_negative}%`;
        
        renderChart([data.positive, data.negative, data.neutral]);
    } catch (err) {
        console.error('Error fetching stats:', err);
    }
}

async function fetchNews() {
    els.articleList.innerHTML = '<div class="loading-state"><i class="fa-solid fa-circle-notch fa-spin"></i> Loading...</div>';
    
    try {
        const impact = els.impactFilter.value;
        const searchQ = els.searchInput.value.trim();
        const minRel = els.relevanceFilter.value;
        
        let url = `${API_BASE_URL}/news?limit=50`;
        if (impact !== 'All') url += `&impact_label=${impact}`;
        if (searchQ) url += `&search=${encodeURIComponent(searchQ)}`;
        if (minRel > 0) url += `&min_relevance=${minRel}`;
        
        const res = await fetch(url);
        allArticles = await res.json();
        
        renderArticles(allArticles);
    } catch (err) {
        console.error('Error fetching news:', err);
        els.articleList.innerHTML = '<div class="loading-state">Failed to load articles.</div>';
    }
}

function renderArticles(articles) {
    els.resultCount.innerText = `${articles.length} results`;
    els.articleList.innerHTML = '';
    
    if (articles.length === 0) {
        els.articleList.innerHTML = '<div class="loading-state">No articles match your filters.</div>';
        return;
    }
    
    articles.forEach(article => {
        const card = document.createElement('div');
        card.className = 'article-card';
        
        let impactClass = '';
        if (article.impact_label) {
            const labelLower = article.impact_label.toLowerCase();
            if (labelLower.includes('tích cực') || labelLower.includes('positive')) impactClass = 'impact-Positive';
            else if (labelLower.includes('tiêu cực') || labelLower.includes('negative')) impactClass = 'impact-Negative';
            else if (labelLower.includes('trung tính') || labelLower.includes('neutral')) impactClass = 'impact-Neutral';
        }
        
        const relScore = article.relevance_score ? Math.round(article.relevance_score * 100) : 0;
        
        const getTagStr = (item) => typeof item === 'object' && item !== null ? (item.name || JSON.stringify(item)) : item;
        
        const catHtml = article.categories && article.categories.length > 0 
            ? article.categories.map(c => `<span class="feed-tag">${getTagStr(c)}</span>`).join('') : '';
            
        const topicHtml = article.topics && article.topics.length > 0 
            ? article.topics.map(c => `<span class="feed-tag topic-tag">${getTagStr(c)}</span>`).join('') : '';

        card.innerHTML = `
            <div class="article-content">
                <div class="article-meta">
                    <span class="tag-source">${article.source || 'Unknown'}</span>
                    <span class="date"><i class="fa-regular fa-calendar"></i> ${article.published_date || ''}</span>
                </div>
                <h3 class="article-title">${article.title}</h3>
                ${(catHtml || topicHtml) ? `<div class="article-tags-feed">${catHtml}${topicHtml}</div>` : ''}
            </div>
            <div class="article-stats">
                <div style="text-align: right;">
                    <span class="impact-badge ${impactClass}">${article.impact_label || 'Unrated'}</span>
                    ${relScore > 0 ? `<div class="rel-score">Rel: ${relScore}%</div>` : ''}
                </div>
                <i class="fa-solid fa-chevron-right article-icon"></i>
            </div>
        `;
        
        card.addEventListener('click', () => openModal(article));
        els.articleList.appendChild(card);
    });
}

function openModal(article) {
    els.modalSource.innerText = article.source || 'Unknown';
    els.modalTitle.innerText = article.title;
    
    let impactClass = '';
    if (article.impact_label) {
        const labelLower = article.impact_label.toLowerCase();
        if (labelLower.includes('tích cực') || labelLower.includes('positive')) impactClass = 'impact-Positive';
        else if (labelLower.includes('tiêu cực') || labelLower.includes('negative')) impactClass = 'impact-Negative';
        else if (labelLower.includes('trung tính') || labelLower.includes('neutral')) impactClass = 'impact-Neutral';
    }
    els.modalImpact.className = `tag ${impactClass}`;
    els.modalImpact.innerText = `${article.impact_label || 'Unrated'} (${article.impact_score || 0})`;
    
    // Summary
    if (article.summary && article.summary.length > 0) {
        els.modalSummarySection.classList.remove('hidden');
        els.modalSummaryList.innerHTML = article.summary.map(s => `<li>${s}</li>`).join('');
    } else {
        els.modalSummarySection.classList.add('hidden');
    }
    
    // Impact Reason
    if (article.impact_reason) {
        els.modalReasonSection.classList.remove('hidden');
        els.modalReasonText.innerText = article.impact_reason;
    } else {
        els.modalReasonSection.classList.add('hidden');
    }
    
    // Helper to render tags
    const renderTags = (element, arr, fallback) => {
        element.innerHTML = '';
        if (arr && arr.length > 0) {
            arr.forEach(c => {
                const span = document.createElement('span');
                span.className = 'tag';
                span.innerText = typeof c === 'object' && c !== null ? (c.name || JSON.stringify(c)) : c;
                element.appendChild(span);
            });
        } else {
            element.innerHTML = `<span class="tag">${fallback}</span>`;
        }
    };
    
    renderTags(els.modalCategories, article.categories, 'Uncategorized');
    renderTags(els.modalEntities, article.entities, 'No entities');
    renderTags(els.modalTopics, article.topics, 'No topics');
    
    els.modalLink.href = article.url;
    
    els.modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // prevent scrolling
}

function closeModal() {
    els.modal.classList.remove('active');
    document.body.style.overflow = '';
}

function renderChart(dataArr) {
    const ctx = document.getElementById('impactChart').getContext('2d');
    
    if (impactChartInstance) {
        impactChartInstance.destroy();
    }
    
    const isDark = document.body.classList.contains('dark-mode');
    Chart.defaults.color = isDark ? '#94a3b8' : '#6b7280';
    
    impactChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative', 'Neutral'],
            datasets: [{
                data: dataArr,
                backgroundColor: [
                    '#10b981', // emerald
                    '#f43f5e', // rose
                    '#3b82f6'  // blue
                ],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

function debounce(func, timeout = 300){
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}
