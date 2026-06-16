# CSRF 防护设计文档

## 一、背景与威胁分析

### 1.1 CSRF（跨站请求伪造）攻击原理

攻击者诱导已登录用户在不知情的情况下，从第三方网站向目标站点发起恶意请求。由于浏览器会自动附带 Cookie 等身份凭证，目标站点难以区分请求来源是否合法。

典型的 CSRF 攻击场景：

```
用户登录 lab.example.com（获得会话凭证）
    ↓
用户访问攻击者网站 evil.com（含有隐藏表单/自动提交脚本）
    ↓
evil.com 的脚本向 lab.example.com/api/users/delete 发起 POST 请求
    ↓
浏览器自动附带 Cookie → 服务器误认为是用户主动操作 → 攻击成功
```

### 1.2 本系统的特殊性与防护选择

本系统采用 **SPA + JWT 鉴权**架构，身份凭证（JWT Token）存储在 `Authorization: Bearer` 请求头中，而非 Cookie。浏览器并**不会**自动附带自定义请求头，因此 CSRF 攻击在传统意义上对本系统的威胁已大幅降低。

然而，作为课设安全设计，我们仍需考虑以下边缘风险：

| 风险场景 | 描述 |
|----------|------|
| **WebView / 混合应用** | 部分浏览器内核允许跨域请求携带自定义头 |
| **浏览器 0-day** | 无法预知的浏览器安全漏洞 |
| **内网攻击** | 同源策略在特定内网环境下可能被绕过 |
| **纵深防御** | 单层防护总是不足的，多层次校验是安全设计基本原则 |

基于以上分析，我们选择了 **自定义请求头校验法**——前端在写请求中携带 `X-CSRF-Token` 头，后端对所有非简单请求强制校验该 Token 的有效性。这是对现有 JWT 鉴权的**纵深加固**，而非与 Cookie 双提交等传统方案类比。

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (Vue3 SPA)                       │
│                                                             │
│  登录成功                                                     │
│    ↓                                                        │
│  GET /api/auth/csrf-token ──────────→ 获取 CSRF Token        │
│    ↓                                                        │
│  存入内存 (auth.js: _csrfToken)                                │
│    ↓                                                        │
│  写请求拦截器自动附加 X-CSRF-Token 头                           │
│    │                                                        │
│    ├── CSRF 403? ──→ 自动刷新 Token → 重试一次                  │
│    │                                                        │
│  页面刷新? ──→ Layout.vue onMounted 重新获取                    │
│  退出登录? ──→ clearCsrfToken() 清除内存                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (Flask)                            │
│                                                             │
│  before_request 中间件拦截                                     │
│    ↓                                                        │
│  GET/HEAD/OPTIONS? ──→ 放行（读请求不校验）                     │
│    ↓                                                        │
│  白名单(POST 登录/注册/验证码)? ──→ 放行                         │
│    ↓                                                        │
│  未登录? ──→ 放行（由权限装饰器返回 401）                        │
│    ↓                                                        │
│  提取 X-CSRF-Token 头 ──→ 为空? ──→ 403 "缺少 CSRF Token"      │
│    ↓                                                        │
│  与 Redis 中 csrf:{user_id} 比对                              │
│    ↓                                                        │
│  不匹配? ──→ 403 "CSRF Token 无效或已过期"                     │
│    ↓                                                        │
│  匹配 → 刷新 TTL → 放行                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、后端实现详解

### 3.1 CSRF Token 的生成与存储

**文件**：`backend/app/utils/csrf.py`

```python
import secrets
from flask import current_app
from app.extensions import redis_client

def generate_csrf_token(user_id: int) -> str:
    """为指定用户生成新 CSRF Token，写入 Redis 并返回。"""
    token = secrets.token_hex(32)               # 64 字符 hex，256 位熵
    ttl = current_app.config["CSRF_TOKEN_EXPIRE_SECONDS"]  # 默认 7200 秒
    redis_client.setex(f"csrf:{user_id}", ttl, token)      # key = csrf:用户ID
    return token
```

**设计亮点**：

1. **密钥强度**：`secrets.token_hex(32)` 生成 256 位熵的随机数，远超暴力枚举能力范围。不使用 `random` 模块或时间戳等可预测的种子，符合 CSPRNG 标准。

2. **服务端存储（非 Cookie 双提交）**：Token 仅存储在 Redis 中，客户端内存持有副本。与"Cookie 中存 Token + 请求头回传"的双提交方案相比：
   - 不依赖 Cookie 机制，避免 `HttpOnly`/`Secure`/`SameSite` 等 Cookie 属性的配置复杂性和浏览器兼容性问题
   - Token 生命周期完全由服务端控制，可随时撤销
   - 不与 JWT 的 `Bearer` 方案产生设计冲突

3. **按用户隔离**：Redis key 设计为 `csrf:{user_id}`，每个用户独立一个 Token。一个用户的 Token 泄露不会影响其他用户。

4. **自动过期**：`SETEX` 命令确保 Token 在指定时间后自动清理。默认 7200 秒（2 小时），与 JWT 默认有效期一致，配置项化便于调整。

### 3.2 CSRF Token 的校验

```python
def validate_csrf_token(user_id: int, token: str) -> bool:
    """常量时间比较，防止时序攻击。"""
    stored = redis_client.get(f"csrf:{user_id}")
    if not stored or not token:
        return False
    return secrets.compare_digest(stored, token)  # 非 short-circuit 比较
```

**设计亮点**：

- **常量时间比较**：使用 `secrets.compare_digest()` 而非 `==` 运算符。普通字符串 `==` 在 Python 中是短路比较（逐字符比较，第一个不同即返回），攻击者可通过精确测量响应时间逐位猜测 Token 值（时序侧信道攻击）。`compare_digest` 无论内容是否匹配，都遍历完整长度，消除了时序差异。

### 3.3 全局 CSRF 校验中间件

**文件**：`backend/app/__init__.py`

```python
from .utils.csrf import check_csrf

@app.before_request
def _csrf_check():
    result = check_csrf()
    if result is not None:
        return result
```

中间件的**放行逻辑**（`check_csrf()` 函数内部）：

| 条件 | 处理 | 理由 |
|------|------|------|
| `method in (GET, HEAD, OPTIONS)` | 放行 | 读请求不改变状态，CSRF 攻击目标永远是写操作 |
| 路径在 `WHITELIST`（登录/注册/验证码/CSRF-Token/健康检查） | 放行 | 这些接口是获取 CSRF Token 的前提条件，不能形成死锁 |
| 用户未登录（`g.current_user_id == None`） | 放行 | 由 `@require_permission` 装饰器兜底返回 401，职责分离 |
| `X-CSRF-Token` 头缺失 | 返回 403 | 拒绝没有防护的写请求 |
| Token 与 Redis 不匹配 | 返回 403 | Token 过期/伪造 |
| 校验通过 | 刷新 Redis TTL，放行 | 避免用户操作过程中 Token 过期 |

**设计亮点**：

1. **写操作全覆盖**：中间件注册为 `before_request` 钩子，对所有进入 Flask 的写请求做 CSRF 校验，不存在路由遗漏风险。开发期间新增路由自动受保护。

2. **白名单机制防死锁**：登录接口本身是 POST 请求，必须写在白名单中，否则用户永远无法获取 CSRF Token。

3. **TTL 滑动刷新**：每次校验通过后自动刷新 Redis 过期时间，确保活跃用户不会在使用中撞到过期。只有长期不操作的用户才需要重新获取。

4. **职责分离**：认证（JWT）和 CSRF 防护是两个独立层。CSRF 中间件不关心用户是否登录（交给权限装饰器），只关心已登录用户的写请求是否带了有效 Token。

### 3.4 CSRF Token 下发端点

**文件**：`backend/app/api/auth.py`

```python
@auth_bp.get("/csrf-token")
def get_csrf_token():
    """登录后获取 CSRF Token。需携带有效 JWT，仅限已登录用户调用。"""
    user_id = _current_user_id()
    if not user_id:
        return error("请先登录", code=401, http_status=401)

    from app.utils.csrf import generate_csrf_token
    token = generate_csrf_token(user_id)
    return success({"csrf_token": token})
```

端点设计为 `GET` 方法——读取操作本身不需要 CSRF 校验，且需要被 CSRF 中间件的白名单豁免。

### 3.5 配置项

**文件**：`backend/app/config.py`

```python
CSRF_TOKEN_EXPIRE_SECONDS = int(os.getenv("CSRF_TOKEN_EXPIRE_SECONDS", "7200"))
```

---

## 四、前端实现详解

### 4.1 内存存储（不持久化）

**文件**：`frontend/src/utils/auth.js`

```javascript
let _csrfToken = null  // 仅内存变量，不写入 localStorage

export function setCsrfToken(token) { _csrfToken = token }
export function getCsrfToken()       { return _csrfToken }
export function clearCsrfToken()     { _csrfToken = null }
```

**设计亮点**：

- **仅内存存储**：CSRF Token 不写入 `localStorage` 或 `sessionStorage`。这意味着：
  - XSS 攻击无法通过读取 `localStorage` 窃取（`localStorage` 是 XSS 的首要窃取目标）
  - 页面刷新后 Token 自动消失，由 `Layout.vue` 的 `onMounted` 重新获取
  - 关闭标签页后 Token 彻底清除，不留残留

- **Token ≠ 持久身份凭证**：JWT 已存储在 `localStorage` 中负责身份识别，CSRF Token 只负责"当前页面会话的写操作合法性"，两者的生命周期和存储策略解耦。

### 4.2 自动携带与过期重试

**文件**：`frontend/src/utils/request.js`

```javascript
// 请求拦截：写请求自动带 X-CSRF-Token
request.interceptors.request.use(config => {
    const method = (config.method || '').toLowerCase()
    if (['post', 'put', 'delete', 'patch'].includes(method)) {
        const csrf = getCsrfToken()
        if (csrf) {
            config.headers['X-CSRF-Token'] = csrf
        }
    }
    return config
})
```

**过期自动重试机制**：

```javascript
let _csrfRefreshing = null  // 并发锁

async function refreshCsrfToken() {
    if (_csrfRefreshing) return _csrfRefreshing  // 已有刷新进行中则等待
    _csrfRefreshing = request.get('/auth/csrf-token').then(res => {
        if (res.code === 0 && res.data?.csrf_token) {
            setCsrfToken(res.data.csrf_token)
        }
    }).finally(() => { _csrfRefreshing = null })
    return _csrfRefreshing
}

// 响应拦截中
if (msg.includes('CSRF') && !error.config._csrfRetried) {
    error.config._csrfRetried = true
    await refreshCsrfToken()
    return request(error.config)  // 用新 Token 重试
}
```

**设计亮点**：

1. **自动刷新 + 单次重试**：当 CSRF Token 过期导致 403 时，前端**自动**调用 `csrf-token` 接口获取新 Token，然后用新 Token **重试**原请求。整个过程对用户透明，无需手动刷新页面。

2. **并发请求防抖**：多个 API 请求同时收到 CSRF 403 时，`_csrfRefreshing` Promise 锁确保只发起**一次** Token 刷新，所有等待中的请求共享结果——避免雪崩效应。

3. **防无限重试**：`_csrfRetried` 标记确保每个请求只重试一次。如果刷新后的 Token 仍然失败（比如 JWT 也过期了），不会进入死循环。

### 4.3 登录时获取 Token

**文件**：`frontend/src/views/Login.vue`

```javascript
await request.post('/auth/login', { ... })
setToken(res.data.access_token)
// ... 设置用户信息 ...
await initCsrfToken()  // 登录成功后立即获取 CSRF Token
ElMessage.success('登录成功')
router.push(redirect)
```

**文件**：`frontend/src/views/Layout.vue`

```javascript
onMounted(() => {
    initCsrfToken()  // 刷新页面后补回 CSRF Token
})
```

两个获取时机配合：登录时主动获取，页面刷新时被动补回。

---

## 五、安全分析

### 5.1 攻击者视角：我们的 CSRF 方案阻止了哪些攻击？

| 攻击向量 | 防御机制 | 有效性 |
|----------|----------|--------|
| 第三方页面伪造 POST 请求 | 攻击者无法得知 `X-CSRF-Token` 的值（存于受害者浏览器内存，非 Cookie），请求被后端拒绝 | ✅ 完全防御 |
| 攻击者伪造 CSRF Token 值 | `secrets.token_hex(32)` 生成 256 位随机 Token，不可预测 | ✅ 完全防御 |
| 时序侧信道猜测 Token | `secrets.compare_digest()` 常量时间比较 | ✅ 完全防御 |
| XSS 窃取 CSRF Token | Token 仅存于 JavaScript 闭包变量中，不写入 `localStorage`/`sessionStorage` | ⚠️ 部分防御（XSS 仍可能 Hook Axios 拦截器） |
| CSRF Token 被重放 | Redis `SETEX` 自动过期 + 后端不使用一次性 Token（持久化更实用） | ⚠️ 依赖过期策略 |

### 5.2 与常见 CSRF 方案的对比

| 方案 | 原理 | 优点 | 缺点 | 本项目选择 |
|------|------|------|------|-----------|
| **Cookie 双提交** | 服务端在 Cookie 中设置随机 Token，前端从 Cookie 读取后通过请求头回传，服务端比对 | 无状态，无需服务端存储 | 依赖 Cookie 机制；SameSite/跨域配置复杂；需要额外防 `Set-Cookie` 劫持 | ❌ |
| **Synchronizer Token** | 服务端生成 Token 嵌入表单隐藏域 `<input type="hidden">`，提交时回传校验 | 经典方案，理论成熟 | 对 SPA 不友好（无传统表单）；需要服务端维护 Token 映射表 | ❌ |
| **Origin/Referer 校验** | 检查请求头中的 Origin/Referer 是否在白名单域名内 | 零前端改动，纯后端逻辑 | 部分浏览器/代理不发送 Referer；SPA 路由下 Referer 可能不完整 | ❌ |
| **SameSite Cookie** | Cookie 设置 `SameSite=Strict/Lax`，跨站请求不发送 Cookie | 浏览器原生支持，标准化 | 本系统不用 Cookie 做身份鉴权（JWT），此方案不适用 | ❌ |
| **自定义请求头校验（本项目方案）** | 服务端下发随机 Token → 前端写入内存 → 写请求通过 `X-CSRF-Token` 头回传 → 服务端 Redis 比对 | 适配 JWT + SPA 架构；不依赖 Cookie；内存存储抗 XSS 窃取；自动过期刷新 | 额外一次网络请求获取 Token | ✅ |

---

## 六、设计创新点总结

1. **架构适配创新**：摒弃了传统 CSRF 方案对 Cookie 的依赖，设计了一套完全适配 JWT + SPA 架构的 CSRF 防护方案。Token 的生成、存储、校验、刷新全程不触及 Cookie 机制，与现有 JWT 鉴权体系正交共存。

2. **纵深防御理念**：即便浏览器同源策略 + JWT Header 认证已阻挡了大部分 CSRF 攻击，仍部署此层防护。多层不重复的防护覆盖单一机制失效的角落——这是安全设计的核心原则。

3. **用户体验无损**：过期自动刷新 + 并发锁 + 单次重试，用户完全感知不到 CSRF 防护的存在。没有额外的"刷新页面"或"重新登录"提示。

4. **内存隔离存储**：CSRF Token 仅存于 JavaScript 变量，不持久化到 `localStorage`。即便发生 XSS，攻击者也需要在特定时机 Hook 变量而非简单地 `localStorage.getItem()` 批量窃取。

5. **时序攻击防护**：使用 `secrets.compare_digest()` 做常量时间比较，消除 Token 校验环节的侧信道信息泄露。

6. **可配置的过期策略**：TTL 可配置，且每次校验通过自动滑动刷新——不活跃用户自然过期，活跃用户无感使用。
