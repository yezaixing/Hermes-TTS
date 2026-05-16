---
name: gpt-sovits-tts-qq
description: GPT-SoVITS TTS + QQ语音发送。当用户要求语音回复时，调用本地GPT-SoVITS API生成语音并通过NapCat/QQ发送。直到用户要求文字回复为止。
version: 1.3.0
author: 主人
triggers:
  - 用户通过 QQ 渠道对话，要求语音/朗读/念出来
  - 用户要求特定角色的声音（如可莉、纳西妲等）
  - 用户要求"说人话"/"用嘴巴说"
---

# GPT-SoVITS TTS + QQ 语音发送

## 触发条件

当通过 **QQ（NapCat/OneBot）** 渠道与用户对话，且用户要求**语音/朗读/念出来/说话/出声**等语音相关表达时，启用此模式。

## 行为规则

### 硬性规则：语音模式一旦进入，必须持续

**用户对此有严格要求**：一旦用户表示要语音回复，在没有收到用户明确说"打字"/"文字"/"别念了"/"别说了"等文字模式指令之前，**所有后续回复都必须只发语音条，零文字**。

这条规则排在最高优先级。即使你觉得回复很短、或只是确认消息，也必须只用语音。**任何可见文字都会触发用户的纠正**。

### 文字输出规则（重要！用户确认过的）

这是用户明确同意的文字输出规则。语音模式下：

1. **主内容必须只有语音条**——通过 `execute_code` 调用 NapCat API 发送 CQ:record base64 语音条。
2. **平台要求助理回复非空时的妥协方案：只发一个 emoji**。用户明确说"语音之后你就发表情当做文字内容"。这意味着：
   - ✅ 可以写一个纯 emoji（如 🎤、😊、👌、😄、🙌、🎮、📄）作为平台回复
   - ✅ emoji 前面不能加任何文字、标点、括号
   - ✅ emoji 后面不能加任何文字、标点、括号
   - ❌ 不得写英文单词（OK/Done/Good/Sent/听听看/已发送）
   - ❌ 不得写括号注释（如"（语音已发送）""（已发语音）"）
   - ❌ 不得写中文文字（好的/嗯/知道了/明白了）
   - ❌ 不得写标点符号或组合文字+emoji
   - ❌ 不得写"我听懂了"、"收到了"等任何陈述——连"好的"都不行
   - ❌ 不得认为"很短的一句话没关系"——用户不接受任何文字
   - ❌ 不得认为 emoji 不够而补文字——emoji 本身就够了
3. **实际效果**: 在 `execute_code` 中发送完语音条后 → 助理回复中只写一个 emoji → 用户在 QQ 上只会看到语音条，文字 emoji 仅作为平台层面的占位符不引起注意。
4. **此规则从 2026-05-15 会话起严格生效**。用户多次纠正以下违规后最终给出了 emoji 方案：
   - 第一次违规：语音条后写英文名称和文字描述（如"听听看～🎤"）
   - 第二次违规：括号里写"（只发语音，不带文字 ✅）"
   - 第三次违规：认为"这个不送文字会出平台错误"而写解释性文字
   - 用户最终说"语音之后你就发表情当做文字内容"——这就是规则来源
5. 常见违规模式（用户每次都会纠正）：
   - 语音条发完后补一句描述性文字
   - 括号里写"（语音已发送）"
   - 写英文单词如 "OK" / "Done"
   - 写"好的""嗯""明白了"
   - 认为自己"只写了很短一句话没关系"

### 状态管理
- **语音模式**：首次用户要求语音时进入，持续使用语音回复
- **文字模式**：用户要求"打字"/"文字"/"别念了"/"别说了"等时退出语音模式，切回纯文字
- 使用 memory 记录当前会话的语音模式状态，key 为 `tts_mode:<chat_id>`
- **注意 memory 满时**：如果 memory 已满（接近 2,200 字符限制），跳过保存——不要为了腾空间而替换其他有用条目。语音模式状态在这个会话上下文内自然维持。
- **常见违规场景**：确认消息、简短回复、说明性内容——这些也需要语音且不能附带任何文字。不要觉得"这么短不用念"。

## 语音发送流程

### 方案 A：不带角色（默认语音）

直接调用 `/tts` 端点：

```python
import urllib.request, json

payload = {"text": "要朗读的文本"}
req = urllib.request.Request(
    "http://127.0.0.1:5000/tts",
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=60)
audio_data = resp.read()  # 直接返回 WAV 二进制
```

**请求格式说明**：直接传 `{"text": "..."}` 即可。**不要**使用 `{"method": "POST", "body": {"text": ...}}` 这种包装格式——API 会返回 `"Text is empty"`。

**注意**：该 `/tts` 端点有时会返回 500 Internal Server Error（即使服务正常运行）。如果遇到，降级到方案 B（Gradio API）——传一个空 reference audio 和 default 角色也能生成默认语音。

### 方案 B：带角色（如可莉、纳西妲、流萤等）

必须使用 Gradio API 端点 `/gradio_api/call/get_audio`（GSVI v2.6.3 已验证），分两步：

**Step 1** — 提交任务获取 event_id：

```python
import urllib.request, json, time

payload = {
    "data": [
        "要朗读的文本",    # text
        "流萤",            # character — 从 character_list 获取
        "default",         # emotion
        None,              # ref_audio (留空)
        None,              # ref_text (留空)
        "auto",            # ref_audio language
        1.0,               # speed
        "auto",            # text language
        "auto_cut",        # cut method
        50,                # max cut length
        10,                # batch size
        -1,                # seed (-1 = random)
        True,              # parallel inference
        5,                 # top_k
        0.8,               # top_p
        0.8,               # temperature
        1.35               # repetition penalty
    ]
}

req = urllib.request.Request(
    "http://127.0.0.1:5000/gradio_api/call/get_audio",
    data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=60)
event_id = json.loads(resp.read())["event_id"]
```

**Step 2** — 轮询获取结果（解析 SSE 事件提取音频路径）：

```python
audio_path = None
for i in range(60):
    req = urllib.request.Request(
        f"http://127.0.0.1:5000/gradio_api/call/get_audio/{event_id}"
    )
    resp = urllib.request.urlopen(req, timeout=30)
    chunk = resp.read().decode('utf-8')
    if "complete" in chunk:
        for line in chunk.split('\n'):
            if line.startswith('data: '):
                data_str = line[6:]
                try:
                    data_json = json.loads(data_str)
                    if isinstance(data_json, list) and len(data_json) > 0:
                        audio_path = data_json[0].get("path")
                except:
                    pass
        if audio_path:
            break
    time.sleep(1)

if not audio_path:
    raise Exception(f"TTS generation failed, last SSE: {chunk[:500]}")
```

**实际表现**：模型已加载时，轮询通常在 1-3 次（约 3 秒）内返回 `complete` 事件。

#### 保存音频文件

```python
import os, time
out_dir = os.path.expanduser(r"~/AppData/Local/hermes/audio_cache")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, f"tts_{int(time.time())}.wav")
import shutil
shutil.copy2(audio_path, out_path)
```

#### 可用角色列表

通过 `GET http://127.0.0.1:5000/character_list` 获取最新列表。

当前可用角色（截至 2026年5月）：
| 角色 | 说明 |
|------|------|
| Hutao | 胡桃 |
| 可莉 | 可莉（原神） |
| 枫原万叶 | 枫原万叶（原神） |
| 流萤 | 流萤（星穹铁道） |
| 爱莉希雅 | 爱莉希雅（崩坏3） |
| 甘雨 | 甘雨（原神） |
| 知更鸟 | 知更鸟（星穹铁道） |
| 纳西妲 | 纳西妲（原神） |
| 雷电将军 | 雷电将军（原神） |

**注意**：如果用户指定不存在/未加载的角色，API 会返回 `"找不到模型文件"` 或 `"size mismatch"` 错误。此时建议用户切换其他角色或使用无角色模式。

### ⚠️ Gradio 角色语音首次调用可能返回 null

**会话验证（2026-05-15，GSVI 2.6.3）**：首次调用 Gradio API `/gradio_api/call/get_audio` 切换角色（如 可莉）时，`complete` 事件可能返回 `data: [null]` 而非音频路径。**这不是错误**，而是角色模型加载过程的一部分。

**处理方式**：直接重试一次（重新提交 Step 1 + Step 2），第二次调用会成功返回音频路径。实测第二次调用只需 1-3 秒即可完成。

**代码模式：**

```python
def try_tts(text, character, max_attempts=2):
    for attempt in range(max_attempts):
        event_id = submit_gradio_task(text, character)
        audio_path = poll_for_result(event_id)
        if audio_path:
            return audio_path
        print(f"Attempt {attempt+1} returned null, retrying...")
    raise Exception(f"Failed after {max_attempts} attempts for character '{character}'")
```

后续轮询 SSE 响应示例（成功时）：
```
event: generating
data: [{"path": "C:\\Users\\...\\audio.wav", "url": "http://...", ...}]

event: complete
data: [{"path": "C:\\Users\\...\\audio.wav", ...}]
```

解析方法：逐行扫描 SSE 的 `complete` 事件，从 `data:` 行 JSON 解析 `path` 字段。

### 通过 QQ 发送语音

**重要**：不能用 `send_message` 的 MEDIA 标签发到 QQ（QQ 不支持 MEDIA delivery）。必须直接调用 NapCat HTTP API。

**目标：发送为语音条（可点击播放）而非文件**。

#### 方式 A：CQ 码 + base64（最可靠，适用于 execute_code 沙箱）

**私聊：**

```python
import json, urllib.request, base64

with open(out_path, "rb") as f:
    b64_data = base64.b64encode(f.read()).decode("ascii")

cq_code = f"[CQ:record,file=base64://{b64_data}]"
payload = {"user_id": 3101049182, "message": cq_code}
req = urllib.request.Request(
    "http://127.0.0.1:3000/send_private_msg",
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)
resp = urllib.request.urlopen(req, timeout=30)
result = json.loads(resp.read())
```

**群聊：**

```python
payload = {"group_id": 450092690, "message": cq_code}
req = urllib.request.Request(
    "http://127.0.0.1:3000/send_group_msg",
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)
```

**注意**：WAV 文件 base64 后体积增加约 33%。如果 WAV > 5MB 可能发送失败。本次会话实测 295KB WAV（base64 后 ~394KB）发送成功，耗时约 1 秒。

#### 方式 B：通过 QQ 适配器的 `send_voice` 方法

```python
# 仅当在 main agent 循环中（不在 execute_code 沙箱中）可用
from gateway.run import _gateway_runner_ref
async def send_voice_bubble():
    runner = _gateway_runner_ref()
    for platform, adapter in runner.adapters.items():
        if 'qq' in str(platform.value if hasattr(platform, 'value') else platform).lower():
            return await adapter.send_voice(
                chat_id="3101049182",  # 私聊用 QQ 号，群聊用 group:<group_id>
                audio_path=out_path,
                as_file=False
            )
```

**限制**：`execute_code` 沙箱中无法访问 `_gateway_runner_ref()`。

#### 方式 C：作为文件发送（仅当语音条不可用时的备选）

**私聊：** `POST /send_online_file` 参见 `qq-platform` skill。
**群聊：** `POST /upload_group_file` 参见 `qq-platform` skill。

### 切换到文字模式

当用户明确要求文字回复时：
1. 停止调用 TTS API
2. 用 memory 清除 `tts_mode:<chat_id>` 状态
3. 后续回复全部用纯文字

## API 调用失败时的处理

- `/tts` 端点返回 500：降级到方案 B（Gradio API 带 default 角色），或告知用户语音暂时不可用，以文字形式发送
- 角色模型未加载（`"找不到模型文件"` 或 `"size mismatch"`）：告知用户该角色模型未加载，建议切换其他角色或使用无角色模式
- Gradio API 超时/无响应：可能是服务需要重启，告知用户语音暂时不可用

## 注意事项

- GPT-SoVITS 服务地址：`http://127.0.0.1:5000`
- 无角色模式（方案 A）使用默认 base 模型，速度更快，但可能返回 500
- 角色模式（方案 B）经过 GSVI 2.6.3 在 流萤 角色上验证通过（本会话 2026-05-15），约 3 秒返回
- 音频格式默认 WAV
- NapCat HTTP API 地址：`http://127.0.0.1:3000`，无 auth token
- **必须用 `127.0.0.1` 而不是 `localhost`**——localhost 走 IPv6（::1）会连到本机同时运行的 NeteaseCloudMusicApiEnhanced 而非 NapCat
- 长文本建议分批调用 TTS API（每批 1-2 句话）
- QQ 语音消息有大小限制，超大音频可能发送失败

## 已确认的 Pitfalls（用户纠正过）

1. **语音条后附带任何文字**：发完 CQ:record 语音条后，在助理回复中写任何文字（含括号注释、英文、符号）都会被纠正。正确做法：silent 执行 execute_code，只发语音。
2. **把短回复当特例**：用户说"真的吗"这种简短反馈也必须用语音回复，不能认为"太短了不值得用语音"。
3. **平台限制与用户期望冲突**：平台要求助理回复非空，但用户要求零文字可见输出。优先满足用户期望。
4. **发送成功后写确认文字**：语音发送成功后，不要写"已发送"/"好了"/"听听看"等。用户自己能收到语音条。

## 参考

- QQ 文件发送详细说明：`skill_view('qq-platform')`
- 语音条 CQ 码详情：`skill_view('gpt-sovits-tts-qq', 'references/voice-bubble-via-cq-code-recipe.md')`
- Gradio API 细节：`skill_view('gpt-sovits-tts-qq', 'references/gradio-api-details.md')`
