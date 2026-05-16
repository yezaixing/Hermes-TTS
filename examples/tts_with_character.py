"""GPT-SoVITS 角色语音合成示例（Gradio API）"""
import urllib.request, json, time, os, shutil

SERVER = "http://127.0.0.1:5000"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# 参数说明见 references/gradio-api-details.md
DEFAULT_PARAMS = {
    "emotion": "default",
    "ref_audio": None,
    "ref_text": None,
    "ref_audio_lang": "auto",
    "speed": 1.0,
    "text_lang": "auto",
    "cut_method": "auto_cut",
    "max_cut_len": 50,
    "batch_size": 10,
    "seed": -1,
    "parallel": True,
    "top_k": 5,
    "top_p": 0.8,
    "temperature": 0.8,
    "repetition_penalty": 1.35,
}


def tts_with_character(text: str, character: str, max_attempts: int = 2) -> str:
    """方案B：带角色的语音合成

    Args:
        text: 要朗读的文本
        character: 角色名（如 Hutao, 可莉, 流萤, 纳西妲 等）
        max_attempts: 最大重试次数（首次调用可能返回 null）

    Returns:
        生成的 WAV 文件路径
    """
    params = DEFAULT_PARAMS.copy()
    # Gradio API 接收 17 个参数的数组
    data = [
        text,
        character,
        params["emotion"],
        params["ref_audio"],
        params["ref_text"],
        params["ref_audio_lang"],
        params["speed"],
        params["text_lang"],
        params["cut_method"],
        params["max_cut_len"],
        params["batch_size"],
        params["seed"],
        params["parallel"],
        params["top_k"],
        params["top_p"],
        params["temperature"],
        params["repetition_penalty"],
    ]

    for attempt in range(max_attempts):
        # Step 1: 提交任务
        payload = {"data": data}
        req = urllib.request.Request(
            f"{SERVER}/gradio_api/call/get_audio",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=60)
        event_id = json.loads(resp.read())["event_id"]

        # Step 2: 轮询结果
        audio_path = None
        for i in range(30):
            req = urllib.request.Request(
                f"{SERVER}/gradio_api/call/get_audio/{event_id}"
            )
            resp = urllib.request.urlopen(req, timeout=30)
            chunk = resp.read().decode("utf-8")
            if "complete" in chunk:
                for line in chunk.split("\n"):
                    if line.startswith("data: "):
                        data_json = json.loads(line[6:])
                        if isinstance(data_json, list) and len(data_json) > 0:
                            audio_path = data_json[0].get("path")
                if audio_path:
                    break
            time.sleep(1)

        if audio_path:
            out_path = os.path.join(
                OUTPUT_DIR, f"tts_{character}_{int(time.time())}.wav"
            )
            shutil.copy2(audio_path, out_path)
            print(f"✅ 角色 [{character}] 语音生成成功：{out_path}")
            return out_path

        print(f"⚠️  第 {attempt+1} 次尝试返回 null，重试...")

    raise RuntimeError(f"角色 [{character}] 语音生成失败（重试 {max_attempts} 次）")


def get_character_list() -> list:
    """获取可用角色列表"""
    req = urllib.request.Request(f"{SERVER}/character_list")
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())


if __name__ == "__main__":
    chars = get_character_list()
    print(f"📋 可用角色：{chars}")

    if chars:
        # 用第一个角色测试
        tts_with_character("你好，这是角色语音测试", chars[0])
