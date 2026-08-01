import sys
import json
import urllib.request

def main():
    def fetch_instagram_media(url):
        try:
            req_data = json.dumps({"url": url}).encode('utf-8')
            req = urllib.request.Request(
                "https://insta.croto.in/api/download",
                data=req_data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_body = resp.read().decode('utf-8')
                data = json.loads(res_body)
                if data.get("success"):
                    return {
                        "success": True,
                        "media_count": len(data.get("files", [])),
                        "media_urls": [
                            {
                                "index": idx + 1,
                                "type": "video" if f.get("is_video") else "image",
                                "direct_url": f.get("url"),
                                "filename": f.get("filename")
                            }
                            for idx, f in enumerate(data.get("files", []))
                        ]
                    }
                else:
                    return {"success": False, "message": data.get("message", "Fetch failed")}
        except Exception as e:
            return {"success": False, "message": f"Failed to connect to insta.croto.in API: {str(e)}"}

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
