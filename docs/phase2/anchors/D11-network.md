# Anchors: D11 — 计算机网络 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/计算机网络 八股文.md`
- domain: 后端基础（计算机网络）
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. TCP vs UDP
- concepts: TCP, UDP, 面向连接, 可靠传输, 确认应答, 流量控制, 拥塞控制
- evidence_summary: TCP 面向连接可靠（确认应答+重传+流控+拥塞控制）、UDP 无连接不保证可靠但快；场景：TCP=HTTP/MySQL/Redis、UDP=音视频/直播/DNS；一句话：TCP 求稳 UDP 求快。

## Section: 2. 三次握手
- concepts: 三次握手, SYN, ACK, 确认收发能力, 为什么不是两次
- evidence_summary: 目的确认双方收发能力；流程 SYN→SYN+ACK→ACK；不是两次：两次无法让服务端确认客户端接收能力；附时序演示链接。

## Section: 3. 四次挥手
- concepts: 四次挥手, FIN, ACK, TIME_WAIT, CLOSE_WAIT, 全双工
- evidence_summary: TCP 全双工双方关闭分开确认：FIN→ACK→FIN→ACK；不是三次：收到 FIN 一方可能还有数据没发完，ACK 和 FIN 不能合并；附 TIME_WAIT/CLOSE_WAIT 演示链接。

## Section: 4. HTTP vs HTTPS
- concepts: HTTP, HTTPS, TLS/SSL, 加密, 证书, 防篡改
- evidence_summary: HTTP 明文；HTTPS=HTTP+TLS/SSL，加密+证书身份校验+防篡改。

## Section: 5. GET vs POST
- concepts: GET, POST, 语义, 参数位置, 安全性
- evidence_summary: 语义不同：GET 偏查询 POST 偏提交；GET 参数在 URL、POST 在请求体；安全性取决于 HTTP/HTTPS 不是方法本身；GET 参数更易暴露在 URL/日志/历史。

## Section: 6. Cookie / Session / Token
- concepts: Cookie, Session, Token, 浏览器存储, 服务端状态, 无状态认证
- evidence_summary: 三者不在同一层面：Cookie 浏览器存储载体、Session 服务端会话状态、Token 客户端认证凭证；对比表（存储/适用）；前后端分离更常用 Token：无状态利于扩展多端接入。

## Section: 7. 输入 URL 到页面返回
- concepts: DNS, TCP, TLS, HTTP, 渲染
- evidence_summary: 流程：DNS 解析→TCP 连接→(HTTPS TLS 握手)→发 HTTP 请求→服务端处理响应→浏览器解析渲染。

## Section: 8. HTTP 常见状态码
- concepts: 200, 301/302, 304, 400, 401, 403, 404, 500, 502/504
- evidence_summary: 状态码表：200 成功、301/302 重定向、304 未修改走缓存、400 参数错误、401 未认证、403 无权限、404 不存在、500 服务器错误、502/504 网关错误/超时。

## Section: 9. HTTP/1.1 vs HTTP/2
- concepts: HTTP/1.1, HTTP/2, 多路复用, 头部压缩, 二进制分帧
- evidence_summary: HTTP/2 核心改进：多路复用、头部压缩、二进制分帧，一个连接更高效。

## Section: 10. 长连接 vs 短连接
- concepts: 长连接, 短连接, HTTP/1.1 默认长连接
- evidence_summary: 短连接一次请求后断开、长连接可复用多次；HTTP/1.1 默认长连接。

## Section: 高频对比速记
- concepts: 对比汇总（TCP/UDP、三次/四次挥手、HTTP/HTTPS、GET/POST、Cookie/Session/Token、401/403、HTTP/1.1 vs HTTP/2）
- evidence_summary: 表格汇总本文件核心对比；TCP/连接语义与 D07/D08 底层传输弱关联（Cluster 外）。
