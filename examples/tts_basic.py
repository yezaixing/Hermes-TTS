"""GPT-SoVITS 基础 TTS 调用示例"""
import urllib.request, json, os

SERVER = "http://127.0.0.1:5000"
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def tts_basic(text: str, output: str = "output.wav"):
    """方案A：基础语音合成（无角色）"""
    payload = {"text": text}
    req = urllib.request.Request(
        f"{SERVER}/tts",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=60)
    audio = resp.read()
    out_path = os.path.join(OUTPUT_DIR, output)
    with open(out_path, "wb") as f:
        f.write(audio)
    print(f"✅ 保存成功：{out_path} ({len(audio)} bytes)")


if __name__ == "__main__":
    tts_basic("你好，欢迎使用 GPT-SoVITS 语音合成系统")
