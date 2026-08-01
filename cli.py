import sys
import os
import re
import instaloader
import requests

L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

def extract_shortcode(url):
    match = re.search(r'/(?:p|reel|reels)/([A-Za-z0-9_-]+)', url)
    return match.group(1) if match else None

def download_instagram_media(url, output_folder="downloads"):
    os.makedirs(output_folder, exist_ok=True)
    shortcode = extract_shortcode(url)
    if not shortcode:
        print("[-] Invalid Instagram URL. Example format: https://www.instagram.com/p/SHORTCODE/")
        return

    print(f"\n[+] Extracting media for shortcode: {shortcode}")
    
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        media_items = []

        if post.typename == 'GraphSidecar':
            for idx, node in enumerate(post.get_sidecar_nodes(), 1):
                is_vid = node.is_video
                m_url = node.video_url if is_vid else node.display_url
                media_items.append((m_url, is_vid, f"{shortcode}_carousel_{idx}"))
        else:
            is_vid = post.is_video
            m_url = post.video_url if is_vid else post.url
            media_items.append((m_url, is_vid, f"{shortcode}"))

        print(f"[+] Found {len(media_items)} media file(s). Downloading...\n")
        
        for idx, (m_url, is_vid, prefix) in enumerate(media_items, 1):
            ext = 'mp4' if is_vid else 'jpg'
            filename = f"{prefix}.{ext}"
            filepath = os.path.join(output_folder, filename)
            
            print(f" -> Downloading [{idx}/{len(media_items)}]: {filename}...")
            r = requests.get(m_url, stream=True)
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f" [OK] Saved to: {filepath}")
            
        print(f"\n[DONE] Finished downloading all files to: '{os.path.abspath(output_folder)}'\n")

    except Exception as e:
        print(f"[-] Error downloading media: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        url_arg = sys.argv[1]
    else:
        url_arg = input("Paste Instagram Post or Reel URL: ").strip()
    
    if url_arg:
        download_instagram_media(url_arg)
    else:
        print("No URL provided.")
