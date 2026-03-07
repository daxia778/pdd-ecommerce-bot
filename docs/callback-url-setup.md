# PDD 回调地址解决方案 — Cloudflare Tunnel

## 背景

PDD 开放平台申请应用时，必须填写一个公网可访问的 HTTP/HTTPS 回调地址（Redirect URI），
用于 OAuth 授权完成后把 `code` 回传给我们的服务。本机默认没有公网 IP，需要用隧道方案解决。

**推荐方案：Cloudflare Tunnel（免费、永久域名、无需信用卡）**

---

## 方案一：Cloudflare Tunnel（推荐，长期使用）

### 安装 cloudflared

```bash
# macOS (Homebrew)
brew install cloudflare/cloudflare/cloudflared

# 或者直接下载二进制
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz | tar xz
sudo mv cloudflared /usr/local/bin/
```

### 登录 Cloudflare（需要一个免费账号）

```bash
cloudflared tunnel login
# 浏览器会打开 Cloudflare 登录页，完成授权后回到终端
```

### 创建隧道

```bash
# 创建一个永久隧道
cloudflared tunnel create pdd-ecommerce-bot

# 查看生成的隧道 ID（格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
cloudflared tunnel list
```

### 配置文件

创建 `~/.cloudflared/config.yml`：

```yaml
tunnel: <你的隧道ID>
credentials-file: /Users/admin/.cloudflared/<你的隧道ID>.json

ingress:
  - hostname: pdd-bot.yourdomain.com   # 需要你在 Cloudflare 管理的域名
    service: http://localhost:8100
  - service: http_status:404
```

> ⚠️ 如果没有自己的域名，可以先用**方案二（临时隧道）**得到一个 trycloudflare.com 子域名测试。

### 启动隧道

```bash
cloudflared tunnel run pdd-ecommerce-bot
```

终端会显示隧道地址，例如 `https://pdd-bot.yourdomain.com`

### 填入 PDD 申请表的回调地址

```
https://pdd-bot.yourdomain.com/api/v1/oauth/callback
```

---

## 方案二：Cloudflare 快速隧道（临时，无需登录，测试用）

```bash
# 无需账号，一行命令
cloudflared tunnel --url http://localhost:8100

# 控制台会输出类似：
# https://random-name-abc123.trycloudflare.com
```

> ⚠️ 临时地址每次重启后都会变化，不适合填入 PDD 正式申请。但用于测试 Webhook 接收很方便。

---

## 方案三：ngrok（备选）

```bash
# 安装
brew install ngrok

# 启动（注意免费版每次重启地址会变）
ngrok http 8100

# 地址格式：https://xxxx.ngrok.io
```

---

## 项目中需要追加配置的 .env 字段

添加到 `.env` 文件：

```env
# PDD OAuth 回调地址（填入从 Cloudflare Tunnel 或 ngrok 获取的公网 URL）
PDD_WEBHOOK_CALLBACK_URL=https://你的域名/api/v1/oauth/callback
PDD_WEBHOOK_SECRET=  # 可选，用于 Webhook HMAC 签名校验
```

---

## 完整回调流程（供参考）

```
买家在 PDD 平台授权
    ↓
PDD 将 code 回调到:
    https://你的域名/api/v1/oauth/callback?code=xxxx
    ↓
Cloudflare Tunnel 转发到本机:
    http://localhost:8100/api/v1/oauth/callback?code=xxxx
    ↓
我们用 code + app_secret 换取 access_token
    ↓
存入 .env 或数据库，激活 PDD API 客户端
```

---

## 申请材料中填写建议

| 字段 | 建议填写 |
|---|---|
| 回调地址（Redirect URI） | `https://你的域名/api/v1/oauth/callback` |
| 服务器公网 IP | 可填 Cloudflare 的节点 IP（留空也可以，以回调地址为准） |
| 是否测试环境 | 是（申请初期） |
