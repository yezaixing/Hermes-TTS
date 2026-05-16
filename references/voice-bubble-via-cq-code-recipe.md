# Voice Bubble via CQ Code Recipe

## Discovery Session (2026-05-15)

### The Problem

User asked for voice reply. The `gpt-sovits-tts-qq` skill existed but had two issues:

1. **API format wrong**: Skill said `{"method": "POST", "body": {"text": "..."}}` but actual API expects flat `{"text": "..."}`
2. **Wrong delivery method**: Sent audio as a downloadable file via `send_online_file` instead of as a voice bubble
3. **Wrong NapCat URL**: Used `localhost:3000` which resolved to IPv6 → NeteaseCloudMusicApiEnhanced (404). Must use `127.0.0.1:3000`.

The user specifically called out: "why didn't you use the `send_voice` method in the QQ adapter to send as 语音条?"

### Root Cause

The `send_online_file` NapCat API delivers the audio as a **file attachment** (the user has to save and open it). The correct approach is to send it as a **voice bubble** (tap to play, like a voice message).

### The Fix

Use `send_private_msg` with CQ code `[CQ:record,file=base64://<base64>]`:

```python
import base64

with open(audio_path, "rb") as f:
    b64_data = base64.b64encode(f.read()).decode("ascii")

cq_code = f"[CQ:record,file=base64://{b64_data}]"
payload = {"user_id": 3101049182, "message": cq_code}
```

**NapCat 地址必须用 `http://127.0.0.1:3000/`，不能用 `localhost`。**

### Key Learnings

- The QQ adapter's `send_voice(chat_id, audio_path, as_file=False)` method exists but is inaccessible from `execute_code` sandbox (gateway_runner_ref returns None)
- CQ code + base64 is the reliable workaround from sandboxed code
- WAV files can be large — monitor size to avoid QQ's file size limits
- The `/tts` endpoint accepts **only** `{"text": "..."}` — no character/emotion params
- **All NapCat HTTP API calls must use `127.0.0.1:3000` not `localhost:3000`** due to port sharing with NeteaseCloudMusicApiEnhanced on IPv6
