"""将 WAV 音频作为语音条发送到 QQ（NapCat API）"""
import json, urllib.request, base64, os, sys

NAPCAT_API = "http://127.0.0.1:3000"  # ⚠️ 不能用 localhost


def send_voice_to_private(user_id: int, audio_path: str):
    """发送语音条到私聊"""
    with open(audio_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    cq_code = f"[CQ:record,file=base64://{b64}]"
    payload = {"user_id": user_id, "message": cq_code}

    req = urllib.request.Request(
        f"{NAPCAT_API}/send_private_msg",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    msg_id = (result.get("data") or {}).get("message_id")
    print(f"✅ 私聊语音发送成功，message_id={msg_id}")
    return result


def send_voice_to_group(group_id: int, audio_path: str):
    """发送语音条到群聊"""
    with open(audio_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    cq_code = f"[CQ:record,file=base64://{b64}]"
    payload = {"group_id": group_id, "message": cq_code}

    req = urllib.request.Request(
        f"{NAPCAT_API}/send_group_msg",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    msg_id = (result.get("data") or {}).get("message_id")
    print(f"✅ 群聊语音发送成功，message_id={msg_id}")
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：python send_to_qq.py <私聊|群聊> <QQ号|群号> <音频文件>")
        print("示例：python send_to_qq.py 私聊 3101049182 output.wav")
        print("示例：python send_to_qq.py 群聊 450092690 output.wav")
        sys.exit(1)

    mode = sys.argv[1]
    target = int(sys.argv[2])
    audio = sys.argv[3]

    if not os.path.exists(audio):
        print(f"❌ 文件不存在：{audio}")
        sys.exit(1)

    size_mb = os.path.getsize(audio) / (1024 * 1024)
    print(f"📊 音频大小：{size_mb:.1f} MB")

    if mode == "私聊":
        send_voice_to_private(target, audio)
    elif mode == "群聊":
        send_voice_to_group(target, audio)
    else:
        print(f"❌ 未知模式：{mode}")
