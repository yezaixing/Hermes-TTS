# GPT-SoVITS Gradio API 调用细节

## 服务器信息

- **地址**: `http://127.0.0.1:5000`
- **类型**: Gradio 6.14.0 应用 + 自定义 FastAPI 端点
- **Gradio API 基础路径**: `/gradio_api`

## 所有可用的 Gradio Named Endpoints

由 `GET /gradio_api/info` 返回。以下是经过验证的可用的关键端点：

### `/lambda` — 基础文本处理

- 参数: `x` (string) — 输入文本
- 用途: 简单的文本 echo，用于测试连接

### `/change_character_list` — 切换角色（Gradio 内部）

- 参数: `character` (string), `emotion` (string)
- 用途: Gradio UI 中切换角色下拉列表
- ⚠️ **这个端点不加载模型权重**，只更新 UI 下拉选项

### `/get_audio` — 生成角色语音 ✅ 核心端点

完整参数（17个）:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| param_0 | string | 默认文本 | 输入文本 |
| param_1 | string | "Hutao" | 角色名（见 character_list） |
| param_2 | string | "default" | 情感 |
| param_3 | FileData | null | 参考音频路径（可选，启用后忽略 emotion） |
| param_4 | string | null | 参考音频文本 |
| param_5 | string | "auto" | 参考音频语言 |
| param_6 | number | 1.0 | 语速 (0.5-2.0) |
| param_7 | string | "auto" | 文本语言 |
| param_8 | string | "auto_cut" | 文本切割方法 |
| param_9 | number | 50 | 切割最大长度 |
| param_10 | number | 10 | 批处理大小 |
| param_11 | number | -1 | 随机种子 (-1=随机) |
| param_12 | boolean | true | 并行推理 |
| param_13 | number | 5 | Top K (1-40) |
| param_14 | number | 0.8 | Top P (0.1-2.0) |
| param_15 | number | 0.8 | 温度 (0.1-2.0) |
| param_16 | number | 1.35 | 重复惩罚 (0.0-5.0) |

**调用方式（Gradio v2 接口）**:

```python
# POST /gradio_api/call/get_audio
# Body: {"data": [param_0, param_1, ..., param_16]}
# Response: {"event_id": "..."}

# GET /gradio_api/call/get_audio/{event_id}
# Response: SSE stream → final event has "data": [{"path": "...\\audio.wav", ...}]
```

### `/tts` — 直接 TTS 端点（自定义，非 Gradio）

不支持角色参数的简单模式：

```python
# POST /tts
# Body: {"text": "要朗读的文本"}
# Response: binary WAV audio
```

⚠️ 这个端点不接受 character/emotion 参数。加 character 会报 `"找不到模型文件"`。

## 角色加载注意事项

Gradio API 返回的角色列表包含那些名字，但**不一定**意味着对应的模型权重已经加载。

- 如果报 `"找不到模型文件"`：该角色的模型权重不在期望路径下
- 如果报 `"size mismatch"`：模型权重存在但架构不匹配（需重新训练/转换）
- 只有 Gradio UI 中用户手动点击"扫描人物列表"并成功加载后，角色才能使用

## SSE 响应格式

```python
event: generating
data: [{"path": "C:\\...\\audio.wav", "url": "http://...", ...}]

event: complete
data: [{"path": "C:\\...\\audio.wav", ...}]
```

audio.wav 生成在系统临时目录 `C:\Users\<user>\AppData\Local\Temp\gradio\<hash>\audio.wav`。
