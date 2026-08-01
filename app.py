import os
import re
import instaloader
import requests
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# Configure Instaloader
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Instagram Media & Profile Downloader</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between selection:bg-pink-500 selection:text-white">

    <!-- Top Glow Header -->
    <div class="fixed top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 blur-3xl opacity-25 pointer-events-none"></div>

    <div class="max-w-5xl mx-auto px-4 py-10 w-full relative z-10">
        
        <!-- Header -->
        <div class="text-center space-y-3 mb-8">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-amber-500/10 border border-pink-500/20 text-pink-400 text-xs font-bold uppercase tracking-widest">
                <span>⚡ Posts, Reels & Full Profile Downloader</span>
            </div>
            <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-white">
                Instagram <span class="bg-gradient-to-r from-purple-400 via-pink-500 to-amber-400 bg-clip-text text-transparent">Downloader</span>
            </h1>
            <p class="text-slate-400 text-sm sm:text-base max-w-lg mx-auto">
                Download single Post/Reels OR fetch all public posts from any Instagram profile/account easily.
            </p>
        </div>

        <!-- Mode Selector Tabs -->
        <div class="flex justify-center mb-6">
            <div class="bg-slate-900/90 p-1.5 rounded-2xl border border-slate-800 flex gap-2">
                <button id="tab-single" class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg">
                    🎬 Single Post / Reel / Carousel
                </button>
                <button id="tab-profile" class="px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all text-slate-400 hover:text-white">
                    👤 Whole Profile / Account Posts
                </button>
            </div>
        </div>

        <!-- Input Box -->
        <div class="bg-slate-900/90 border border-slate-800 rounded-3xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl mb-8">
            <form id="download-form" class="flex flex-col sm:flex-row gap-3">
                <div class="flex-1 relative">
                    <input 
                        type="text" 
                        id="insta-input" 
                        placeholder="Paste Instagram Post/Reel URL (e.g. https://www.instagram.com/p/DUYW53OCe2y/)"
                        required
                        class="w-full bg-slate-950 border border-slate-800 rounded-2xl px-5 py-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all"
                    />
                </div>
                <button 
                    type="submit" 
                    id="submit-btn"
                    class="bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 hover:opacity-95 text-white font-bold px-8 py-4 rounded-2xl text-sm shadow-lg shadow-pink-500/25 transition-all flex items-center justify-center gap-2"
                >
                    <span id="btn-text">Download</span>
                    <svg id="btn-loader" class="hidden animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </button>
            </form>
        </div>

        <!-- Status Message -->
        <div id="status" class="hidden p-4 rounded-2xl text-sm font-semibold mb-6"></div>

        <!-- Profile Metadata (Rendered if Profile mode) -->
        <div id="profile-card" class="hidden bg-slate-900 border border-slate-800 rounded-3xl p-6 mb-8 flex flex-col sm:flex-row items-center gap-6">
            <img id="profile-pic" class="w-24 h-24 rounded-full border-2 border-pink-500/50 object-cover" src="" alt="Profile Pic"/>
            <div class="text-center sm:text-left space-y-1">
                <h3 id="profile-username" class="text-2xl font-bold text-white"></h3>
                <p id="profile-name" class="text-sm text-slate-400 font-medium"></p>
                <div class="flex items-center justify-center sm:justify-start gap-4 pt-2 text-xs font-semibold text-slate-300">
                    <span id="profile-posts-count" class="bg-slate-800 px-3 py-1 rounded-lg"></span>
                    <span id="profile-followers" class="bg-slate-800 px-3 py-1 rounded-lg"></span>
                </div>
            </div>
        </div>

        <!-- Results Grid -->
        <div id="results-container" class="hidden space-y-6">
            <h2 class="text-lg font-bold text-slate-200 border-b border-slate-800 pb-3 flex items-center justify-between">
                <span id="results-title">Downloaded Media Files</span>
                <span id="files-count" class="text-xs font-semibold px-2.5 py-1 bg-slate-800 rounded-full text-pink-400">0 Items</span>
            </h2>
            <div id="media-grid" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                <!-- Media Cards Rendered Here -->
            </div>
        </div>

    </div>

    <!-- Footer -->
    <footer class="py-6 border-t border-slate-900 text-center text-xs text-slate-600">
        Instagram Downloader • Built with Flask & Instaloader
    </footer>

    <script>
        let currentMode = 'single'; // 'single' or 'profile'

        const tabSingle = document.getElementById('tab-single');
        const tabProfile = document.getElementById('tab-profile');
        const inputField = document.getElementById('insta-input');
        const form = document.getElementById('download-form');
        const submitBtn = document.getElementById('submit-btn');
        const btnText = document.getElementById('btn-text');
        const btnLoader = document.getElementById('btn-loader');
        const statusDiv = document.getElementById('status');
        const profileCard = document.getElementById('profile-card');
        const profilePic = document.getElementById('profile-pic');
        const profileUsername = document.getElementById('profile-username');
        const profileName = document.getElementById('profile-name');
        const profilePostsCount = document.getElementById('profile-posts-count');
        const profileFollowers = document.getElementById('profile-followers');
        const resultsContainer = document.getElementById('results-container');
        const mediaGrid = document.getElementById('media-grid');
        const filesCount = document.getElementById('files-count');
        const resultsTitle = document.getElementById('results-title');

        tabSingle.addEventListener('click', () => {
            currentMode = 'single';
            tabSingle.className = 'px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg';
            tabProfile.className = 'px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all text-slate-400 hover:text-white';
            inputField.placeholder = 'Paste Instagram Post/Reel URL (e.g. https://www.instagram.com/p/DUYW53OCe2y/)';
        });

        tabProfile.addEventListener('click', () => {
            currentMode = 'profile';
            tabProfile.className = 'px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg';
            tabSingle.className = 'px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all text-slate-400 hover:text-white';
            inputField.placeholder = 'Enter Username or Profile URL (e.g. theabbiestore.in or https://instagram.com/theabbiestore.in)';
        });

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const inputVal = inputField.value.trim();
            if (!inputVal) return;

            // UI Loading State
            submitBtn.disabled = true;
            btnText.innerText = currentMode === 'profile' ? 'Fetching Account...' : 'Extracting...';
            btnLoader.classList.remove('hidden');
            statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-slate-900 border border-slate-800 text-slate-300 animate-pulse';
            statusDiv.innerText = currentMode === 'profile' 
                ? 'Fetching profile posts and media links... (This may take a moment)'
                : 'Fetching post metadata and media URLs from Instagram...';
            statusDiv.classList.remove('hidden');
            profileCard.classList.add('hidden');
            resultsContainer.classList.add('hidden');
            mediaGrid.innerHTML = '';

            const endpoint = currentMode === 'profile' ? '/api/profile' : '/api/download';

            try {
                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ input: inputVal })
                });

                const data = await response.json();

                if (data.success) {
                    statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-emerald-950/80 border border-emerald-800/50 text-emerald-300';
                    statusDiv.innerText = `Success! Fetched ${data.files.length} media item(s).`;

                    if (currentMode === 'profile' && data.profile) {
                        profilePic.src = data.profile.profile_pic;
                        profileUsername.innerText = `@${data.profile.username}`;
                        profileName.innerText = data.profile.full_name || '';
                        profilePostsCount.innerText = `📸 ${data.profile.total_posts} Total Posts`;
                        profileFollowers.innerText = `👥 ${data.profile.followers} Followers`;
                        profileCard.classList.remove('hidden');
                        resultsTitle.innerText = `Recent Account Posts (${data.files.length})`;
                    } else {
                        resultsTitle.innerText = 'Downloaded Media Files';
                    }

                    filesCount.innerText = `${data.files.length} Item(s)`;
                    mediaGrid.innerHTML = data.files.map((file, idx) => `
                        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-3 flex flex-col justify-between space-y-3 group hover:border-pink-500/50 transition-all">
                            <div class="aspect-square bg-slate-950 rounded-xl overflow-hidden flex items-center justify-center relative">
                                ${file.is_video 
                                    ? `<video src="${file.url}" controls class="w-full h-full object-cover"></video>` 
                                    : `<img src="${file.url}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" alt="Instagram media ${idx+1}"/>`
                                }
                            </div>
                            <a href="${file.url}" download="${file.filename}" target="_blank" class="w-full bg-slate-800 hover:bg-pink-600 text-white text-xs font-bold py-2.5 rounded-xl transition-colors text-center flex items-center justify-center gap-1.5">
                                <span>Download ${file.is_video ? 'Video' : 'Image'}</span>
                            </a>
                        </div>
                    `).join('');

                    resultsContainer.classList.remove('hidden');
                } else {
                    statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-rose-950/80 border border-rose-800/50 text-rose-300';
                    statusDiv.innerText = `Error: ${data.message}`;
                }
            } catch (err) {
                statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-rose-950/80 border border-rose-800/50 text-rose-300';
                statusDiv.innerText = 'Network error or server failed to respond.';
            } finally {
                submitBtn.disabled = false;
                btnText.innerText = 'Download';
                btnLoader.classList.add('hidden');
            }
        });
    </script>
</body>
</html>
"""

def extract_shortcode(url):
    match = re.search(r'/(?:p|reel|reels)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def extract_username(input_str):
    # If full URL given, extract username
    match = re.search(r'instagram\.com/([A-Za-z0-9_.-]+)', input_str)
    if match:
        username = match.group(1).rstrip('/')
        # Exclude reserved paths
        if username in ['p', 'reel', 'reels', 'stories', 'explore']:
            return None
        return username
    # Otherwise treat as raw username string
    clean_username = input_str.strip('@/ ')
    return clean_username if clean_username else None

def extract_single_media(url):
    shortcode = extract_shortcode(url)
    if not shortcode:
        return {'success': False, 'message': 'Invalid Instagram Post/Reel URL format. Please paste a valid post link.'}

    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        media_list = []

        if post.typename == 'GraphSidecar':
            for idx, node in enumerate(post.get_sidecar_nodes(), 1):
                is_vid = node.is_video
                media_url = node.video_url if is_vid else node.display_url
                media_list.append({
                    'url': media_url,
                    'is_video': is_vid,
                    'filename': f"{shortcode}_carousel_{idx}.{'mp4' if is_vid else 'jpg'}"
                })
        else:
            is_vid = post.is_video
            media_url = post.video_url if is_vid else post.url
            media_list.append({
                'url': media_url,
                'is_video': is_vid,
                'filename': f"{shortcode}.{'mp4' if is_vid else 'jpg'}"
            })

        return {'success': True, 'files': media_list}

    except Exception as e:
        return {'success': False, 'message': f"Could not fetch Instagram post: {str(e)}"}

def extract_profile_media(input_str, max_posts=12):
    username = extract_username(input_str)
    if not username:
        return {'success': False, 'message': 'Invalid Instagram Username or Profile URL.'}

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        
        if profile.is_private:
            return {'success': False, 'message': f"Account @{username} is private. Cannot download media from private profiles."}

        profile_info = {
            'username': profile.username,
            'full_name': profile.full_name,
            'profile_pic': profile.profile_pic_url,
            'total_posts': profile.mediacount,
            'followers': profile.followers
        }

        media_list = []
        count = 0

        for post in profile.get_posts():
            if count >= max_posts:
                break

            shortcode = post.shortcode
            if post.typename == 'GraphSidecar':
                for idx, node in enumerate(post.get_sidecar_nodes(), 1):
                    is_vid = node.is_video
                    media_url = node.video_url if is_vid else node.display_url
                    media_list.append({
                        'url': media_url,
                        'is_video': is_vid,
                        'filename': f"{username}_{shortcode}_{idx}.{'mp4' if is_vid else 'jpg'}"
                    })
            else:
                is_vid = post.is_video
                media_url = post.video_url if is_vid else post.url
                media_list.append({
                    'url': media_url,
                    'is_video': is_vid,
                    'filename': f"{username}_{shortcode}.{'mp4' if is_vid else 'jpg'}"
                })
            
            count += 1

        return {
            'success': True,
            'profile': profile_info,
            'files': media_list
        }

    except Exception as e:
        return {'success': False, 'message': f"Could not fetch profile @{username}: {str(e)}"}

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/download', methods=['POST'])
def download_api():
    data = request.get_json() or {}
    input_val = data.get('input') or data.get('url')
    if not input_val:
        return jsonify({'success': False, 'message': 'URL is required'}), 400
    
    result = extract_single_media(input_val)
    return jsonify(result)

@app.route('/api/profile', methods=['POST'])
def profile_api():
    data = request.get_json() or {}
    input_val = data.get('input')
    if not input_val:
        return jsonify({'success': False, 'message': 'Username or Profile URL is required'}), 400
    
    result = extract_profile_media(input_val, max_posts=12)
    return jsonify(result)

if __name__ == '__main__':
    print("\n=======================================================")
    print("Instagram Downloader Web Tool is Running!")
    print("Open http://localhost:5000 in your browser")
    print("=======================================================\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
