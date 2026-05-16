# Hermes-TTS — GPT-SoVITS 语音合成 + QQ 语音发送

> 📎 关联项目：[Hermes-QQ](https://github.com/yezaixing/hermes-qq) — Hermes Agent QQ 原生平台适配器

通过本地 [GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) 服务实现文本转语音（TTS），并通过 NapCat/OneBot 发送到 QQ 作为可播放的语音条。
（需要支持qq语音条发送请点击关联项目链接https://github.com/yezaixing/hermes-qq）

支持**角色语音切换**（可莉、流萤、胡桃、纳西妲等），无需联网，完全本地运行。

## 功能

- ✅ 文字转语音（TTS）— 本地 GPT-SoVITS 服务
- ✅ 角色语音切换 — 支持多个二次元角色（原神、星穹铁道、崩坏3）
- ✅ QQ 语音条发送 — 通过 CQ:record base64 发送可点击播放的语音
- ✅ 双模式支持 — `/tts` 简单模式 + Gradio API 角色模式
- ✅ Hermes Agent 集成 — 作为 skill 自动加载

## 架构

```
用户 → QQ/NapCat → Hermes Agent
                       │
                       ├─ gpt-sovits-tts-qq skill
                       │     ├─ 方案A: /tts (基础语音)
                       │     └─ 方案B: Gradio API (角色语音)
                       │
                       ↓
                GPT-SoVITS 服务
                (http://127.0.0.1:5000)
                       │
                       ↓  WAV audio
                       │
                NapCat HTTP API
                (http://127.0.0.1:3000)
                       │
                       ↓ [CQ:record,file=base64://...]
                       QQ 语音条
```

## 前置条件

1. **GPT-SoVITS** 本地服务运行在 `http://127.0.0.1:5000`
   - 确保已开启 Gradio API（GSVI v2.6.3+）
   - 所需角色需要在 Gradio UI 中手动扫描加载

2. **NapCat** / OneBot HTTP API 运行在 `http://127.0.0.1:3000`
   - ⚠️ 必须用 `127.0.0.1` 而不是 `localhost`
   - 本机 3000 端口 NapCat 绑定 IPv4，NeteaseCloudMusicApiEnhanced 绑定 IPv6
   - `localhost` 可能解析到 IPv6 导致连到错误的服务

3. **Hermes Agent**（可选，仅作为 skill 集成时需要）
   - 安装 Hermes Agent 后，将本目录的 SKILL.md 放入 `skills/` 目录

## 快速开始

### 测试 TTS 服务

```python
import urllib.request, json

# 方案A：简单模式
payload = {"text": "你好，欢迎使用语音合成"}
req = urllib.request.Request(
    "http://127.0.0.1:5000/tts",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=60)
audio_data = resp.read()  # WAV 二进制

with open("output.wav", "wb") as f:
    f.write(audio_data)
print(f"Saved output.wav ({len(audio_data)} bytes)")
```

### 角色语音

```python
import urllib.request, json, time

# Step 1: 提交任务
payload = {
    "data": [
        "你好，我是胡桃",           # text
        "Hutao",                    # character
        "default",                  # emotion
        None,                       # ref_audio
        None,                       # ref_text
        "auto",                     # ref_audio_lang
        1.0,                        # speed
        "auto",                     # text_lang
        "auto_cut",                 # cut_method
        50,                         # max_cut_len
        10,                         # batch_size
        -1,                         # seed
        True,                       # parallel
        5,                          # top_k
        0.8,                        # top_p
        0.8,                        # temperature
        1.35                        # repetition_penalty
    ]
}

req = urllib.request.Request(
    "http://127.0.0.1:5000/gradio_api/call/get_audio",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=60)
event_id = json.loads(resp.read())["event_id"]

# Step 2: 轮询结果
for i in range(30):
    req = urllib.request.Request(
        f"http://127.0.0.1:5000/gradio_api/call/get_audio/{event_id}"
    )
    resp = urllib.request.urlopen(req, timeout=30)
    chunk = resp.read().decode("utf-8")
    if "complete" in chunk:
        for line in chunk.split("\n"):
            if line.startswith("data: "):
                data_json = json.loads(line[6:])
                if isinstance(data_json, list) and len(data_json) > 0:
                    audio_path = data_json[0].get("path")
                    print(f"Audio generated: {audio_path}")
                    import shutil
                    shutil.copy2(audio_path, "output_with_character.wav")
        break
    time.sleep(1)
```

### 发送到 QQ

```python
import json, urllib.request, base64

with open("output.wav", "rb") as f:
    b64_data = base64.b64encode(f.read()).decode("ascii")

cq_code = f"[CQ:record,file=base64://{b64_data}]"

# 私聊
payload = {"user_id": 3101049182, "message": cq_code}

# 群聊 改用:
# payload = {"group_id": 450092690, "message": cq_code}

req = urllib.request.Request(
    "http://127.0.0.1:3000/send_private_msg",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=30)
print(json.loads(resp.read()))
```

## 可用角色

| 角色 | 说明 |
|------|------|
| Hutao | 胡桃（原神） |
| 可莉 | 可莉（原神） |
| 枫原万叶 | 枫原万叶（原神） |
| 流萤 | 流萤（星穹铁道） |
| 爱莉希雅 | 爱莉希雅（崩坏3） |
| 甘雨 | 甘雨（原神） |
| 知更鸟 | 知更鸟（星穹铁道） |
| 纳西妲 | 纳西妲（原神） |
| 雷电将军 | 雷电将军（原神） |

> 通过 `GET http://127.0.0.1:5000/character_list` 获取最新可用角色列表。
> 注意：角色需要在 GPT-SoVITS Gradio UI 中手动扫描加载后才能使用。

## API 参考

### `POST /tts` — 基础语音合成

```json
// Request
{"text": "要朗读的文本"}

// Response: binary WAV audio
```

⚠️ 有时返回 500 Internal Server Error——降级到 Gradio API。

### `POST /gradio_api/call/get_audio` — 角色语音合成

17 参数数组，详见 [`references/gradio-api-details.md`](references/gradio-api-details.md)。

### SSE 响应格式

```
event: generating
data: [{"path": "C:\\...\\audio.wav", "url": "http://...", ...}]

event: complete
data: [{"path": "C:\\...\\audio.wav", ...}]
```

### 首次角色调用可能返回 null

首次切换角色时 `complete` 事件可能返回 `data: [null]`。**重试一次即可**。

## 文件结构

```
Hermes-TTS/
├── README.md                                    # 本文件
├── SKILL.md                                     # Hermes Agent skill 定义
├── .gitignore                                   # Git 忽略规则
├── references/
│   ├── gradio-api-details.md                    # Gradio API 完整参数说明
│   ├── napcat-http-addressing.md               # NapCat 地址注意事项
│   └── voice-bubble-via-cq-code-recipe.md      # QQ 语音条发送方法
└── examples/
    ├── tts_basic.py                             # 基础 TTS 示例
    ├── tts_with_character.py                    # 角色语音示例
    └── send_to_qq.py                            # QQ 发送示例
```

## 注意事项

- GPT-SoVITS 地址：`http://127.0.0.1:5000`
- NapCat API 地址：`http://127.0.0.1:3000`（**不是 localhost**）
- WAV 文件 base64 后体积增加约 33%，超大音频可能发送失败
- 长文本建议分批调用（每批 1-2 句）
- 模型未加载时角色 API 返回 `"找不到模型文件"` 或 `"size mismatch"`

## 许可证

MIT
