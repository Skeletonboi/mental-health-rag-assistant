import re
import requests
# from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright
import asyncio
import json
import traceback
from urllib.parse import urlparse, parse_qs


async def intercept_get_transcript_params(video_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--mute-audio'])
        context = await browser.new_context()
        page = await context.new_page()

        captured_request = {}
        
        async def handle_request(route, request):
            if "get_transcript" in request.url:
                captured_request["url"] = request.url
                captured_request["headers"] = request.headers
                captured_request["post_data"] = request.post_data
            await route.continue_()

        try:
            await page.route("**/*", handle_request)
            await page.goto(video_url)

            # Expand description
            await page.wait_for_selector('#expand', timeout=5000)
            await page.click('#expand')

            # Wait for transcript button to appear
            await page.wait_for_selector('text=Show transcript', timeout=5000)
            await page.click('text=Show transcript')

            await page.wait_for_timeout(500)
            await browser.close()

        except Exception as e:
            raise RuntimeError(f"Playwright failure: {e}")
        if not captured_request:
            raise RuntimeError("Failed to intercept get_transcript request.")

        return captured_request

def replay_get_transcript_request(captured_request):
    url = captured_request["url"]
    headers = captured_request["headers"]
    post_data = json.loads(captured_request["post_data"])
    
    try:
        response = requests.post(url, headers=headers, json=post_data)
    except Exception as e:
        raise RuntimeError(f"Failed to POST transcript url, error: {e}")
    response.raise_for_status()

    return response.json()

def parse_transcript_json(json_data, vid_url):
    transcript = []
    try:
        data = json_data['actions'][0]['updateEngagementPanelAction']['content']\
                ['transcriptRenderer']['content']['transcriptSearchPanelRenderer']
        
        languages = data['footer']['transcriptFooterRenderer']['languageMenu']\
                    ['sortFilterSubMenuRenderer']['subMenuItems']
        selected_item = next((item for item in languages if item.get('selected')), None)
        if selected_item:
            active_lang = selected_item.get('title', 'Unknown')
        ts_lines = data['body']['transcriptSegmentListRenderer']['initialSegments']

        for line in ts_lines:
            if line.get('transcriptSegmentRenderer', None):
                if line['transcriptSegmentRenderer'].get('snippet', None):
                    txt = line['transcriptSegmentRenderer']['snippet']['runs'][0]['text']
                    transcript.append(txt)
    except Exception as e:
        raise RuntimeError(f"Failed to parse transcript JSON: {e} \n Vid URL: {vid_url}") from e

    return " ".join(transcript), "english" in active_lang.lower()

async def get_transcript(vid_id):
    vid_url = f"https://www.youtube.com/watch?v={vid_id}"
    
    try:
        req = await intercept_get_transcript_params(vid_url)
        response = replay_get_transcript_request(req)
        ts, is_english = parse_transcript_json(response, vid_url)
        return ts, vid_url, is_english
    except Exception as e:
        # traceback.print_exc()
        raise RuntimeError(e)
    

if __name__ == "__main__":
    # vid_id = "_ZVGXmafWqY"
    # vid_id = "3VsxjbpMTao"
    # vid_id = "pbxU_v5kR8A"
    # vid_id = "CX_ov9N91Sg"
    vid_id = "CooJi1I6V1E"
    try:
        ts, url, is_english = asyncio.run(get_transcript(vid_id))
        print(f"Transcript Excerpt: {ts[:50]}..., Vid URL: {url}, Is English: {is_english}")
    except Exception as e:
        print(f'Error: {e}, Vid ID: https://www.youtube.com/watch?v={vid_id}')

    