import sys
import json
import re
import instaloader

def main():
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

    def fetch_instagram_media(url):
        shortcode = extract_shortcode(url)
        if not shortcode:
            return {"success": False, "message": "Invalid Instagram URL format. Must contain /p/ or /reel/"}

        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            media_urls = []

            if post.typename == 'GraphSidecar':
                for idx, node in enumerate(post.get_sidecar_nodes(), 1):
                    is_vid = node.is_video
                    media_url = node.video_url if is_vid else node.display_url
                    media_urls.append({
                        "index": idx,
                        "type": "video" if is_vid else "image",
                        "direct_url": media_url,
                        "filename": f"{shortcode}_carousel_{idx}.{'mp4' if is_vid else 'jpg'}"
                    })
            else:
                is_vid = post.is_video
                media_url = post.video_url if is_vid else post.url
                media_urls.append({
                    "index": 1,
                    "type": "video" if is_vid else "image",
                    "direct_url": media_url,
                    "filename": f"{shortcode}.{'mp4' if is_vid else 'jpg'}"
                })

            return {
                "success": True,
                "shortcode": shortcode,
                "caption": post.caption or "",
                "owner_username": post.owner_username,
                "media_count": len(media_urls),
                "media_urls": media_urls
            }
        except Exception as e:
            return {"success": False, "message": f"Failed to fetch media: {str(e)}"}

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "instagram-media-downloader",
                            "version": "1.0.0"
                        }
                    }
                }
                print(json.dumps(response), flush=True)

            elif method == "notifications/initialized":
                pass  # Client notification

            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "fetch_instagram_media",
                                "description": "Fetches direct CDN image and video URLs from any public Instagram Post, Reel, or Carousel link.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "url": {
                                            "type": "string",
                                            "description": "Public Instagram Post or Reel URL (e.g. https://www.instagram.com/p/DUYU6GOCS_P/ or https://www.instagram.com/reel/DbbE46AqdrT/)"
                                        }
                                    },
                                    "required": ["url"]
                                }
                            }
                        ]
                    }
                }
                print(json.dumps(response), flush=True)

            elif method == "tools/call":
                params = request.get("params", {})
                name = params.get("name")
                args = params.get("arguments", {})

                if name == "fetch_instagram_media":
                    url = args.get("url", "")
                    res_data = fetch_instagram_media(url)
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(res_data, indent=2)
                                }
                            ]
                        }
                    }
                    print(json.dumps(response), flush=True)
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{name}' not found"
                        }
                    }
                    print(json.dumps(response), flush=True)

        except Exception as err:
            sys.stderr.write(f"Error handling JSON-RPC: {str(err)}\n")
            sys.stderr.flush()

if __name__ == "__main__":
    main()
