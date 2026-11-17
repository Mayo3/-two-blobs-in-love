"""Post the day's video to YouTube Shorts, Instagram Reels and Facebook Reels.

Usage:
  python -m shorts.crosspost path/to/meta.json [--only youtube,instagram,facebook] [--youtube-privacy unlisted]
  python -m shorts.crosspost login-youtube     one-time: prints the YT_* secrets (run on your own computer)
  python -m shorts.crosspost login-meta        one-time: prints the META_* / IG_* secrets

A platform whose secrets are missing is skipped, so you can switch them on one at a time. A failure on one
platform never stops the others or the daily job: the results go into meta.json ("posted"), into the last
history entry (for the engagement reviews) and into the phone notification.

TikTok is not here: its API posts only private videos until the app passes TikTok's audit, so TikTok stays
the one you post by hand (with a trending sound).

Secrets (GitHub: Settings -> Secrets and variables -> Actions):
  YouTube:   YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
  Instagram: META_PAGE_TOKEN, IG_USER_ID         (an Instagram professional account linked to the Facebook Page)
  Facebook:  META_PAGE_TOKEN, META_PAGE_ID
"""
import json
import os
import sys
import time

import requests

from .daily import load_history, save_history
from .produce import ROOT

PAUSED = os.path.join(ROOT, "state", "crosspost-paused")  # while this file exists, nothing is posted
GRAPH ="v24.0"
# What the Meta user token needs: Facebook Reels on the Page need pages_manage_posts (Instagram works without it,
# so a token lacking it fails only on Facebook with error #200).
META_SCOPES = ("pages_show_list", "pages_read_engagement", "pages_manage_posts",
               "instagram_basic", "instagram_content_publish", "business_management")  # Meta Graph API version; Meta retires each about two years after release
TIMEOUT = 120


def describe(meta):
    """The caption everywhere: the TikTok caption (question first, hashtags) plus the source line."""
    return f"{meta['caption']}\n\n{meta['comment']}"


def clip(meta):
    """The file to upload: the copy with background music when there is one (TikTok keeps the plain video)."""
    return meta.get("video_music") or meta["video"]


def need(*names):
    missing = [n for n in names if not os.environ.get(n)]
    return None if not missing else f"no secret {', '.join(missing)}"


def check(r):
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:400]}")
    return r.json() if r.content else {}


# ---- YouTube -----------------------------------------------------------------------------------------

YT_SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def youtube(meta, privacy="public"):
    token = check(requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=TIMEOUT))["access_token"]
    title = meta["title"].replace("*", "").replace("<", "").replace(">", "")
    title = (title[:90] + " #Shorts") if "#shorts" not in title.lower() else title[:100]
    body = {
        "snippet": {"title": title, "description": describe(meta)[:4900], "categoryId": "22",
                    "tags": [t.lstrip("#") for t in meta["caption"].split() if t.startswith("#")]},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    size = os.path.getsize(clip(meta))
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                               "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)},
                      json=body, timeout=TIMEOUT)
    check(r)
    with open(clip(meta), "rb") as f:
        video = check(requests.put(r.headers["Location"], data=f, timeout=600,
                                   headers={"Authorization": f"Bearer {token}", "Content-Type": "video/mp4"}))
    status = video.get("status", {}).get("privacyStatus")
    note = "" if status == privacy else f" (YouTube set it to {status}: the Google project may need YouTube's API audit)"
    return {"id": video["id"], "url": f"https://youtube.com/shorts/{video['id']}", "note": note.strip()}


def login_youtube():
    """Loopback OAuth for a Google 'Desktop app' client; prints the refresh token to store as a secret."""
    import http.server
    import secrets
    import urllib.parse
    import webbrowser

    cid = input("OAuth client ID: ").strip()
    secret = input("OAuth client secret: ").strip()
    state = secrets.token_urlsafe(16)
    got = {}

    class Catch(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            got.update(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Done. You can close this tab and go back to the terminal.".encode())

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Catch)
    redirect = f"http://127.0.0.1:{server.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": cid, "redirect_uri": redirect, "response_type": "code", "scope": YT_SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    print(f"Opening the browser. If it doesn't open, visit:\n{url}\n")
    webbrowser.open(url)
    while "code" not in got and "error" not in got:
        server.handle_request()
    if got.get("state", [""])[0] != state or "code" not in got:
        raise SystemExit(f"Login failed: {got.get('error', ['state mismatch'])[0]}")
    tok = check(requests.post("https://oauth2.googleapis.com/token", data={
        "code": got["code"][0], "client_id": cid, "client_secret": secret, "redirect_uri": redirect,
        "grant_type": "authorization_code"}, timeout=TIMEOUT))
    print("\nAdd these repository secrets:\n"
          f"  YT_CLIENT_ID     = {cid}\n  YT_CLIENT_SECRET = {secret}\n  YT_REFRESH_TOKEN = {tok['refresh_token']}")


# ---- Meta: Instagram Reels and Facebook Reels ----------------------------------------------------------

def _rupload(url, token, path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        return check(requests.post(url, data=f, timeout=600, headers={
            "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)}))


def instagram(meta):
    token, user = os.environ["META_PAGE_TOKEN"], os.environ["IG_USER_ID"]
    api = f"https://graph.facebook.com/{GRAPH}"
    box = check(requests.post(f"{api}/{user}/media", timeout=TIMEOUT, data={
        "media_type": "REELS", "upload_type": "resumable", "caption": describe(meta)[:2200],
        "share_to_feed": "true", "access_token": token}))
    _rupload(f"https://rupload.facebook.com/ig-api-upload/{GRAPH}/{box['id']}", token, clip(meta))
    for _ in range(60):  # Instagram processes the video before it can be published
        st = check(requests.get(f"{api}/{box['id']}", timeout=TIMEOUT,
                                params={"fields": "status_code,status", "access_token": token}))
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process the video: {st.get('status')}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram was still processing the video after 10 minutes")
    post = check(requests.post(f"{api}/{user}/media_publish", timeout=TIMEOUT,
                               data={"creation_id": box["id"], "access_token": token}))
    link = check(requests.get(f"{api}/{post['id']}", timeout=TIMEOUT,
                              params={"fields": "permalink", "access_token": token})).get("permalink", "")
    return {"id": post["id"], "url": link}


def facebook(meta):
    token, page = os.environ["META_PAGE_TOKEN"], os.environ["META_PAGE_ID"]
    api = f"https://graph.facebook.com/{GRAPH}/{page}/video_reels"
    r = requests.post(api, timeout=TIMEOUT, data={"upload_phase": "start", "access_token": token})
    if r.status_code == 403 and '"code":200' in r.text.replace(" ", ""):
        raise RuntimeError("HTTP 403 (#200): the Page token lacks pages_manage_posts. Make a new token with "
                           "python -m shorts.crosspost login-meta and update META_PAGE_TOKEN. " + r.text[:200])
    start = check(r)
    _rupload(start["upload_url"], token, clip(meta))
    check(requests.post(api, timeout=TIMEOUT, data={
        "upload_phase": "finish", "video_id": start["video_id"], "video_state": "PUBLISHED",
        "description": describe(meta), "access_token": token}))
    return {"id": start["video_id"], "url": f"https://www.facebook.com/reel/{start['video_id']}"}


def login_meta():
    """Turns a short-lived user token (from the Graph API Explorer) into a Page token that does not expire."""
    api = f"https://graph.facebook.com/{GRAPH}"
    print("In the Graph API Explorer, pick your app, 'Get User Access Token' and tick ALL of:\n  "
          + ", ".join(META_SCOPES) + "\n")
    token = input("User token (from the Graph API Explorer, or already extended in the Access Token Debugger): ").strip()
    app_id = input("Meta app ID (press Enter if the token is already extended): ").strip()
    if app_id:
        app_secret = input("Meta app secret: ").strip()
        token = check(requests.get(f"{api}/oauth/access_token", timeout=TIMEOUT, params={
            "grant_type": "fb_exchange_token", "client_id": app_id, "client_secret": app_secret,
            "fb_exchange_token": token}))["access_token"]
    long_user = token
    expires = check(requests.get(f"{api}/debug_token", timeout=TIMEOUT, params={
        "input_token": long_user, "access_token": long_user})).get("data", {}).get("expires_at", 0)
    if expires and expires - time.time() < 7 * 86400:
        raise SystemExit("That token is short-lived, so the Page token would expire too. Extend it first "
                         "(Access Token Debugger -> Extend Access Token) or give the app ID and secret.")
    granted = set(check(requests.get(f"{api}/debug_token", timeout=TIMEOUT, params={
        "input_token": long_user, "access_token": long_user})).get("data", {}).get("scopes", []))
    missing = [x for x in META_SCOPES if x not in granted]
    if missing:
        raise SystemExit("The token is missing these permissions: " + ", ".join(missing)
                         + "\nGenerate a new token in the Graph API Explorer with all of them ticked.")
    pages = check(requests.get(f"{api}/me/accounts", timeout=TIMEOUT, params={
        "fields": "id,name,access_token,instagram_business_account", "access_token": long_user}))["data"]
    if not pages:
        raise SystemExit("This account manages no Facebook Page (or the token lacks pages_show_list).")
    for i, p in enumerate(pages):
        print(f"  [{i}] {p['name']}")
    p = pages[int(input("Which Page? ").strip() or 0)]
    ig = (p.get("instagram_business_account") or {}).get("id")
    print("\nAdd these repository secrets:\n"
          f"  META_PAGE_ID    = {p['id']}\n  META_PAGE_TOKEN = {p['access_token']}")
    print(f"  IG_USER_ID      = {ig}" if ig else
          "  (no Instagram account is linked to this Page: link a professional Instagram account to it for Reels)")


# ---- the daily step ------------------------------------------------------------------------------------

PLATFORMS = {
    "youtube": (("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN"), youtube),
    "instagram": (("META_PAGE_TOKEN", "IG_USER_ID"), instagram),
    "facebook": (("META_PAGE_TOKEN", "META_PAGE_ID"), facebook),
}


def main(argv):
    if argv[:1] == ["login-youtube"]:
        return login_youtube()
    if argv[:1] == ["login-meta"]:
        return login_meta()
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("meta")
    ap.add_argument("--only", default=",".join(PLATFORMS))
    ap.add_argument("--youtube-privacy", default="public", choices=["public", "unlisted", "private"])
    args = ap.parse_args(argv)

    if os.path.exists(PAUSED):
        print(f"cross-posting paused: delete {os.path.relpath(PAUSED, ROOT)} to switch it back on")
        return
    meta = json.load(open(args.meta, encoding="utf-8"))
    posted = meta.get("posted", {})
    for name in args.only.split(","):
        secrets, post = PLATFORMS[name]
        if posted.get(name, {}).get("id"):
            print(f"{name}: already posted ({posted[name]['url']})")
            continue
        missing = need(*secrets)
        if missing:
            print(f"{name}: skipped ({missing})")
            continue
        try:
            res = post(meta, args.youtube_privacy) if name == "youtube" else post(meta)
            posted[name] = res
            print(f"{name}: {res['url']} {res.get('note', '')}".strip(), flush=True)
        except Exception as e:  # one platform failing must not stop the others
            posted[name] = {"error": str(e)[:300]}
            print(f"{name}: FAILED {e}", flush=True)

    meta["posted"] = posted
    with open(args.meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    history = load_history()
    for h in reversed(history):
        if h["date"] == meta["date"] and h["fact"] == meta["fact"]:
            h["posted"] = {k: v.get("id") or "failed" for k, v in posted.items()}
            save_history(history)
            break


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
