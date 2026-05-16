# NapCat HTTP API 必须用 `127.0.0.1`

## 问题

所有通过 `http://localhost:3000` 调用 NapCat HTTP API 的请求都返回 404。

详见 `qq-platform` skill 中的 `references/localhost-vs-127-dot-0-dot-0-dot-1.md`。

## 原因

本机 3000 端口有两个服务竞争：
- **NapCat** 绑定 `127.0.0.1:3000` (PID 12512)
- **NeteaseCloudMusicApiEnhanced** 绑定 `0.0.0.0:3000` (PID 4696)

`localhost` 解析到 IPv6 `::1` 时会连到后者，只有 `127.0.0.1` 保证连到 NapCat。

## 规则

**所有 NapCat API URL 必须写 `http://127.0.0.1:3000/...`，不能用 `localhost`。**
