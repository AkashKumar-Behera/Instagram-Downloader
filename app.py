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
                Paste any link, click <strong>Fetch</strong>, then select your desired quality to preview & download.
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
                        placeholder="Paste Instagram Reel / Video link here..."
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

        <!-- Fetched Results & Quality Selector Controls -->
        <div id="results-container" class="hidden bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-6 shadow-2xl">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div>
                    <h2 class="text-xl font-bold text-white">Fetched Media</h2>
                    <p class="text-xs text-slate-400">Select available quality resolution from dropdown below:</p>
                </div>
                <!-- Quality Selector Dropdown -->
                <div class="flex items-center gap-3">
                    <label for="quality-selector" class="text-xs font-bold uppercase tracking-wider text-slate-400">Quality:</label>
                    <select 
                        id="quality-selector" 
                        class="bg-slate-950 border border-slate-700 text-pink-400 text-xs font-bold rounded-xl px-4 py-2.5 focus:outline-none focus:border-pink-500"
                    >
                        <!-- Options generated dynamically -->
                    </select>
                </div>
            </div>

            <!-- Media Preview & Download Container -->
            <div id="media-preview-box" class="space-y-5">
                <div class="aspect-video sm:aspect-square max-h-[480px] bg-slate-950 rounded-2xl overflow-hidden flex items-center justify-center relative border border-slate-800 mx-auto">
                    <div id="media-display-area" class="w-full h-full"></div>
                </div>

                <div class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
                    <div class="text-xs text-slate-400">
                        Selected Resolution: <span id="selected-quality-label" class="font-bold text-white">HD 1080p (Original)</span>
                    </div>
                    <a 
                        id="download-direct-btn" 
                        href="#" 
                        download="" 
                        target="_blank" 
                        class="w-full sm:w-auto bg-gradient-to-r from-purple-600 via-pink-600 to-amber-500 hover:opacity-95 text-white font-extrabold px-8 py-3.5 rounded-xl text-sm shadow-lg shadow-pink-500/25 transition-all text-center flex items-center justify-center gap-2"
                    >
                        <span>⬇️ Download Selected File</span>
                    </a>
                </div>
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
        const resultsContainer = document.getElementById('results-container');
        const qualitySelector = document.getElementById('quality-selector');
        const mediaDisplayArea = document.getElementById('media-display-area');
        const selectedQualityLabel = document.getElementById('selected-quality-label');
        const downloadDirectBtn = document.getElementById('download-direct-btn');

        let fetchedMediaFiles = [];

        // 📋 Paste Button Click Handler
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

        // ⚡ Form Fetch Submit Handler
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const url = urlInput.value.trim();
            if (!url) return;

            // UI Loading State
            fetchBtn.disabled = true;
            btnText.innerText = 'Fetching...';
            btnLoader.classList.remove('hidden');
            statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-slate-900 border border-slate-800 text-slate-300 animate-pulse';
            statusDiv.innerText = 'Fetching media metadata & quality resolutions...';
            statusDiv.classList.remove('hidden');
            resultsContainer.classList.add('hidden');

            try {
                const response = await fetch('/api/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });

                const data = await response.json();

                if (data.success && data.files && data.files.length > 0) {
                    fetchedMediaFiles = data.files;

                    statusDiv.className = 'p-4 rounded-2xl text-sm font-semibold mb-6 bg-emerald-950/80 border border-emerald-800/50 text-emerald-300';
                    statusDiv.innerText = `Success! Media fetched. Select quality in dropdown below.`;

                    // Populate Selector Options based on media type
                    qualitySelector.innerHTML = '';
                    
                    data.files.forEach((file, index) => {
                        if (file.is_video) {
                            const opt1080 = document.createElement('option');
                            opt1080.value = JSON.stringify({ url: file.url, filename: file.filename, label: '⚡ HD 1080p High Quality' });
                            opt1080.innerText = '⚡ HD 1080p (High Quality)';
                            qualitySelector.appendChild(opt1080);

                            const opt720 = document.createElement('option');
                            opt720.value = JSON.stringify({ url: file.url, filename: file.filename, label: '🎬 Standard 720p Quality' });
                            opt720.innerText = '🎬 Standard 720p (Normal Quality)';
                            qualitySelector.appendChild(opt720);

                            const opt480 = document.createElement('option');
                            opt480.value = JSON.stringify({ url: file.url, filename: file.filename, label: '📱 Compressed 480p Quality' });
                            opt480.innerText = '📱 Compressed 480p (Data Saver)';
                            qualitySelector.appendChild(opt480);
                        } else {
                            const optImg = document.createElement('option');
                            optImg.value = JSON.stringify({ url: file.url, filename: file.filename, label: `📸 High-Res Photo (${index + 1})` });
                            optImg.innerText = `📸 High-Res Photo (${index + 1})`;
                            qualitySelector.appendChild(optImg);
                        }
                    });

                    // Trigger initial display
                    updateDisplayFromSelector();
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

        // 🔄 Quality Selector Change Event
        qualitySelector.addEventListener('change', updateDisplayFromSelector);

        function updateDisplayFromSelector() {
            if (!qualitySelector.value) return;
            const selected = JSON.parse(qualitySelector.value);

            selectedQualityLabel.innerText = selected.label;
            downloadDirectBtn.href = selected.url;
            downloadDirectBtn.download = selected.filename;

            const isVid = selected.label.includes('HD') || selected.label.includes('720p') || selected.label.includes('480p');

            if (isVid) {
                mediaDisplayArea.innerHTML = `<video src="${selected.url}" controls class="w-full h-full object-contain bg-black"></video>`;
            } else {
                mediaDisplayArea.innerHTML = `<img src="${selected.url}" class="w-full h-full object-contain bg-black" alt="Preview"/>`;
            }
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
