document.addEventListener('DOMContentLoaded', () => {
    const landingState = document.getElementById('landing-state');
    const dashboardState = document.getElementById('dashboard-state');
    const connectBtn = document.getElementById('connect-btn');

    // DOM Elements for Grids
    const topTracksGrid = document.getElementById('top-tracks-grid');
    const topArtistsGrid = document.getElementById('top-artists-grid');
    const recommendationsGrid = document.getElementById('recommendations-grid');

    // DOM Elements for Loading/Error
    const loadingTopTracks = document.getElementById('loading-top-tracks');
    const errorTopTracks = document.getElementById('error-top-tracks');
    
    const loadingTopArtists = document.getElementById('loading-top-artists');
    const errorTopArtists = document.getElementById('error-top-artists');
    
    const loadingRecommendations = document.getElementById('loading-recommendations');
    const errorRecommendations = document.getElementById('error-recommendations');

    // Connect Spotify Button
    connectBtn.addEventListener('click', () => {
        window.location.href = '/spotify/login';
    });

    // Helper: Create a basic card
    function createCard(title, subtitle) {
        const card = document.createElement('div');
        card.className = 'card';
        
        const h3 = document.createElement('h3');
        h3.textContent = title;
        
        const p = document.createElement('p');
        p.className = 'subtitle-text';
        p.textContent = subtitle;
        
        card.appendChild(h3);
        card.appendChild(p);
        
        return card;
    }

    // Helper: Create recommendation card with tags and score
    function createRecCard(track) {
        const card = createCard(track.name, `by ${track.artists.join(', ')}`);
        
        if (track.score !== undefined) {
            const scoreBadge = document.createElement('div');
            scoreBadge.className = 'score-badge';
            scoreBadge.textContent = track.score.toFixed(2);
            card.appendChild(scoreBadge);
            card.style.position = 'relative'; // For absolute positioning of badge
        }
        
        if (track.matched_genres && track.matched_genres.length > 0) {
            const tagsContainer = document.createElement('div');
            tagsContainer.className = 'tags-container';
            
            track.matched_genres.forEach(genre => {
                const tag = document.createElement('span');
                tag.className = 'tag';
                tag.textContent = genre;
                tagsContainer.appendChild(tag);
            });
            
            card.appendChild(tagsContainer);
        }
        
        return card;
    }

    // Fetch and render Top Tracks
    async function loadTopTracks() {
        try {
            const res = await fetch('/spotify/top-tracks');
            if (res.status === 401) {
                // Not authenticated
                return false;
            }
            if (!res.ok) throw new Error('Failed to fetch top tracks');
            
            const data = await res.json();
            loadingTopTracks.classList.add('hidden');
            
            if (data.top_tracks && data.top_tracks.length > 0) {
                data.top_tracks.forEach(track => {
                    const card = createCard(track.name, `by ${track.artists.join(', ')}`);
                    topTracksGrid.appendChild(card);
                });
            } else {
                topTracksGrid.innerHTML = '<p>No top tracks found.</p>';
            }
            return true;
        } catch (err) {
            loadingTopTracks.classList.add('hidden');
            errorTopTracks.textContent = err.message;
            errorTopTracks.classList.remove('hidden');
            return true; // Still authenticated, just an error
        }
    }

    // Fetch and render Top Artists
    async function loadTopArtists() {
        try {
            const res = await fetch('/spotify/top-artists');
            if (!res.ok) throw new Error('Failed to fetch top artists');
            
            const data = await res.json();
            loadingTopArtists.classList.add('hidden');
            
            if (data.top_artists && data.top_artists.length > 0) {
                data.top_artists.forEach(artist => {
                    const card = createCard(artist.name, artist.genres.slice(0, 3).join(', ') || 'No genres');
                    topArtistsGrid.appendChild(card);
                });
            } else {
                topArtistsGrid.innerHTML = '<p>No top artists found.</p>';
            }
        } catch (err) {
            loadingTopArtists.classList.add('hidden');
            errorTopArtists.textContent = err.message;
            errorTopArtists.classList.remove('hidden');
        }
    }

    // Fetch and render Recommendations
    async function loadRecommendations() {
        try {
            const res = await fetch('/spotify/recommendations?debug=true');
            if (!res.ok) throw new Error('Failed to fetch recommendations');
            
            const data = await res.json();
            loadingRecommendations.classList.add('hidden');
            
            if (data.recommendations && data.recommendations.length > 0) {
                data.recommendations.forEach(track => {
                    const card = createRecCard(track);
                    recommendationsGrid.appendChild(card);
                });
            } else {
                recommendationsGrid.innerHTML = '<p>No recommendations found based on your profile.</p>';
            }
        } catch (err) {
            loadingRecommendations.classList.add('hidden');
            errorRecommendations.textContent = err.message;
            errorRecommendations.classList.remove('hidden');
        }
    }

    // Initialize App
    async function init() {
        // We use top-tracks to check auth status
        const isAuthenticated = await loadTopTracks();
        
        if (isAuthenticated) {
            landingState.classList.remove('active');
            landingState.classList.add('hidden');
            
            dashboardState.classList.remove('hidden');
            dashboardState.classList.add('active');
            
            // Load the rest of the data
            loadTopArtists();
            loadRecommendations();
        }
    }

    init();
});
