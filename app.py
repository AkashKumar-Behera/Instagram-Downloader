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
    <title>Instagram Media Downloader & Quality Selector</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between selection:bg-pink-500 selection:text-white">

    <!-- Top Glow Header -->
    <div class="fixed top-0 left-1/2 -translate-x-1/2 w-3/4 h-32 bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 blur-3xl opacity-25 pointer-events-none"></div>

    <div class="max-w-4xl mx-auto px-4 py-12 w-full relative z-10">
        
        <!-- Header -->
        <div class="text-center space-y-3 mb-10">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-purple-500/10 via-pink-500/10 to-amber-500/10 border border-pink-500/20 text-pink-400 text-xs font-bold uppercase tracking-widest">
                <span>⚡ Reel, Video & Carousel Media Fetcher</span>
            </div>
            <h1 class="text-4xl sm:text-6xl font-extrabold tracking-tight text-white">
                Instagram <span class="bg-gradient-to-r from-purple-400 via-pink-500 to-amber-400 bg-clip-text text-transparent">Downloader</span>
            </h1>
            <p class="text-slate-400 text-sm sm:text-base max-w-md mx-auto">
                Paste any link, click <strong>Fetch Info</strong>, then view & download all photos & videos easily.
            </p>
        </div>

        <!-- Input & Action Box -->
        <div class="bg-slate-900/90 border border-slate-800 rounded-3xl p-4 sm:p-6 shadow-2xl backdrop-blur-xl mb-8 space-y-4">
            <form id="fetch-form" class="flex flex-col sm:flex-row gap-3">
                <!-- Input field + Paste Button -->
                <div class="flex-1 relative flex items-center">
                    <input 
                        type="text" 
                        id="insta-url" 
                        placeholder="Paste Instagram Reel / Carousel link here..."
                        required
                        class="w-full bg-slate-950 border border-slate-800 rounded-2xl pl-5 pr-24 py-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pink-500 focus:ring-1 focus:ring-pink-500 transition-all"
                    />
                    <button 
                        type="button" 
                        id="paste-btn" 
                        class="absolute right-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold px-3.5 py-2 rounded-xl border border-slate-700 transition-all flex items-center gap-1.5"
                    >
                        <span>📋 Paste</span>
                    </button>
                </div>

                <!-- Fetch Button -->
                <button 
                    type="submit" 
                    id="fetch-btn"
                    class="bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 hover:opacity-95 text-white font-bold px-8 py-4 rounded-2xl text-sm shadow-lg shadow-pink-500/25 transition-all flex items-center justify-center gap-2"
                >
                    <span id="btn-text">Fetch Info</span>
                    <svg id="btn-loader" class="hidden animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </button>
            </form>
        </div>

        <!-- Status Message -->
        <div id="status" class="hidden p-4 rounded-2xl text-sm font-semibold mb-6"></div>

        <!-- Single Video Quality Selector Box (Only shown when it's a Video/Reel) -->
        <div id="video-quality-box" class="hidden bg-slate-900 border border-slate-800 rounded-3xl p-6 mb-8 space-y-4 shadow-2xl">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                    <h2 class="text-xl font-bold text-white">🎬 Select Video Resolution</h2>
                    <p class="text-xs text-slate-400">Choose preferred quality to stream & download:</p>
                </div>
                <div class="flex items-center gap-3">
                    <label for="quality-selector" class="text-xs font-bold uppercase tracking-wider text-slate-400">Quality:</label>
                    <select 
                        id="quality-selector" 
                        class="bg-slate-950 border border-slate-700 text-pink-400 text-xs font-bold rounded-xl px-4 py-2.5 focus:outline-none focus:border-pink-500"
                    >
                        <option value="1080">⚡ HD 1080p (High Quality)</option>
                        <option value="720">🎬 Standard 720p (Normal Quality)</option>
                        <option value="480">📱 Compressed 480p (Data Saver)</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Results Grid for Carousel / Media Cards (All items displayed together) -->
        <div id="results-container" class="hidden space-y-6">
            <h2 class="text-lg font-bold text-slate-200 border-b border-slate-800 pb-3 flex items-center justify-between">
                <span>Fetched Media Items</span>
                <span id="files-count" class="text-xs font-semibold px-2.5 py-1 bg-slate-800 rounded-full text-pink-400">0 Items</span>
            </h2>
            <div id="media-grid" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
                <!-- All Carousel Photos/Videos rendered together here -->
            </div>
        </div>

    </div>

    <!-- Footer -->
    <footer class="py-6 border-t border-slate-900 text-center text-xs text-slate-600">
        Instagram Downloader • Built with Flask & Instaloader
    </footer>

    <script>
        const form = document.getElementById('fetch-form');
        const urlInput = document.getElementById('insta-url');
        const pasteBtn = document.getElementById('paste-btn');
        const fetchBtn = document.getElementById('fetch-btn');
        const btnText = document.getElementById('btn-text');
        const btnLoader = document.getElementById('btn-loader');
        const statusDiv = document.getElementById('status');
        const videoQualityBox = document.getElementById('video-quality-box');
        const qualitySelector = document.getElementById('quality-selector');
        const resultsContainer = document.getElementById('results-container');
        const mediaGrid = document.getElementById('media-grid');
        const filesCount = document.getElementById('files-count');

        let currentFetchedFiles = [];

        // 📋 Paste Button Handler
        pasteBtn.addEventListener('click', async () => {
            try {
                const text = await navigator.clipboard.readText();
                if (text) {
                    urlInput.value = text;
                    urlInput.focus();
                }
            } catch (err) {
                alert('Clipboard permission denied or unsupported by browser.');
            }
        });

        // ⚡ Fetch Form Submit
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = urlInput.value.trim();
            if (!url) return;

            // UI Loading State
            fetchBtn.disabled = true;
            btnText.innerText = 'Fetching...';
            btnLoader.classList.remove('hidden');
            statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-slate-900 border border-slate-800 text-slate-300 animate-pulse';
            statusDiv.innerText = 'Fetching media items...';
            statusDiv.classList.remove('hidden');
            videoQualityBox.classList.add('hidden');
            resultsContainer.classList.add('hidden');
            mediaGrid.innerHTML = '';

            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                const data = await response.json();

                if (data.success && data.files && data.files.length > 0) {
                    currentFetchedFiles = data.files;

                    statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-emerald-950/80 border border-emerald-800/50 text-emerald-300';
                    statusDiv.innerText = `Success! Fetched ${data.files.length} item(s).`;

                    filesCount.innerText = `${data.files.length} Item(s)`;

                    // Check if there's any video
                    const hasVideo = data.files.some(f => f.is_video);
                    if (hasVideo) {
                        videoQualityBox.classList.remove('hidden');
                    }

                    renderAllMediaCards();
                    resultsContainer.classList.remove('hidden');
                } else {
                    statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-rose-950/80 border border-rose-800/50 text-rose-300';
                    statusDiv.innerText = `Error: ${data.message || 'Could not fetch media link.'}`;
                }
            } catch (err) {
                statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-rose-950/80 border border-rose-800/50 text-rose-300';
                statusDiv.innerText = 'Network error or server failed to respond.';
            } finally {
                fetchBtn.disabled = false;
                btnText.innerText = 'Fetch Info';
                btnLoader.classList.add('hidden');
            }
        });

        // 🔄 Quality selector listener for videos
        qualitySelector.addEventListener('change', renderAllMediaCards);

        function renderAllMediaCards() {
            const selectedQuality = qualitySelector.value;

            mediaGrid.innerHTML = currentFetchedFiles.map((file, idx) => `
                <div class="bg-slate-900 border border-slate-800 rounded-3xl p-4 flex flex-col justify-between space-y-4 group hover:border-pink-500/50 transition-all">
                    <div class="aspect-square bg-slate-950 rounded-2xl overflow-hidden flex items-center justify-center relative shadow-inner">
                        ${file.is_video 
                            ? `<video src="${file.url}" controls class="w-full h-full object-cover"></video>` 
                            : `<img src="${file.url}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" alt="Carousel image ${idx+1}"/>`
                        }
                    </div>

                    <a href="${file.url}" download="${file.filename}" target="_blank" class="w-full bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 hover:opacity-90 text-white text-xs font-bold py-3 rounded-xl transition-all text-center flex items-center justify-center gap-1.5 shadow-md">
                        <span>Download ${file.is_video ? `Video (${selectedQuality}p)` : `Photo ${idx+1}`}</span>
                    </a>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
"""

def extract_shortcode(url):
    match = re.search(r'/(?:p|reel|reels)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def extract_single_media(url):
    shortcode = extract_shortcode(url)
    if not shortcode:
        return {'success': False, 'message': 'Invalid Instagram Reel or Post link format.'}

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

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/download', methods=['POST'])
def download_api():
    try:
        data = request.get_json() or {}
        input_val = data.get('input') or data.get('url')
        if not input_val:
            return jsonify({'success': False, 'message': 'URL is required'}), 400
        
        result = extract_single_media(input_val)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': f"Server error: {str(e)}"}), 200

if __name__ == '__main__':
    print("\n=======================================================")
    print("Instagram Downloader Web Tool is Running!")
    print("Open http://localhost:5000 in your browser")
    print("=======================================================\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
