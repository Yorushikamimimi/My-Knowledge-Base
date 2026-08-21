# Anchors: D08 — Redis 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/Redis 八股文.md`
- domain: Redis
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. Redis 为什么快
- concepts: 内存, 单线程, 锁竞争, 上下文切换, IO 模型
- evidence_summary: 基于内存+单线程减少锁竞争和上下文切换+高效数据结构和 IO 模型；最根本是内存，单线程只是减少额外开销。

## Section: 2. 数据类型与场景
- concepts: String, List, Hash, Set, ZSet, 场景
- evidence_summary: 五类型表：String（缓存/计数器/分布式锁标记/Session）、Hash（用户信息/商品详情/配置）、List（消息队列/最新动态）、Set（去重/共同好友/标签）、ZSet（排行榜/热搜/延迟任务）。

## Section: 3. RDB vs AOF
- concepts: RDB, AOF, 定时快照, 追加日志, 恢复
- evidence_summary: RDB 定时快照文件小恢复快可能丢最近数据；AOF 追加写命令日志更安全丢失少但文件大恢复慢；一句话：RDB 记结果，AOF 记过程。

## Section: 4. 过期删除 vs 内存淘汰
- concepts: 惰性删除, 定期删除, 内存淘汰, noeviction, allkeys-lru, volatile-lru, volatile-ttl
- evidence_summary: 过期删除针对已到期 key（惰性访问时清+定期后台抽查清）；内存淘汰内存满时触发，策略：noeviction 报错、allkeys-lru 所有 key 淘汰 LRU、volatile-lru 只淘汰有过期时间的、volatile-ttl 优先淘汰快过期的。

## Section: 5. 缓存穿透 / 击穿 / 雪崩
- concepts: 缓存穿透, 缓存击穿, 缓存雪崩, 布隆过滤器, 互斥锁, 逻辑过期, TTL 随机
- evidence_summary: 三问题表：穿透=查不存在数据每次打 DB→缓存空值/布隆/参数校验；击穿=热点 key 失效瞬时压力→互斥锁/逻辑过期/预热；雪崩=大量 key 同时失效或 Redis 挂→过期随机值/限流降级/高可用。

## Section: 6. BigKey / HotKey
- concepts: BigKey, HotKey, 本地缓存, 多副本, 限流
- evidence_summary: BigKey=value 太大或集合元素多→传输慢/删除阻塞/内存不均；HotKey=访问极高→单节点压力大失效引发击穿；解决：本地缓存/多副本分散/热点不立即过期/限流。

## Section: 7. 缓存一致性
- concepts: Cache Aside, 先更新 DB 再删缓存, 延迟双删, 按需重建
- evidence_summary: 先更新数据库再删缓存（Cache Aside）；不先删缓存：中间读请求会把旧数据加载回来；不更新缓存：按需重建更简单、主动更新引入失败点；双删策略了解：延迟再删一次降低旧数据回填风险。

## Section: 8. 分布式锁
- concepts: SET NX EX, UUID, Lua 脚本, 死锁, 误删, 锁过期, 主从切换
- evidence_summary: `SET key value NX EX seconds` NX 互斥 EX 防死锁；value 存唯一标识解锁前校验；解锁用 Lua「判断 value+删除 key」必须原子；不能拆开加锁设过期（中间宕机死锁）；不能直接 DEL（误删别人的锁）；风险：业务超锁超时提前过期（续期机制）、主从切换锁可靠性；适用：防重复下单/分布式定时任务互斥/库存扣减。与 D09 Section 8 深度重叠（Cluster B）。

## Section: 高频对比速记
- concepts: 对比汇总（RDB/AOF、过期删除/内存淘汰、穿透/击穿/雪崩、BigKey/HotKey）
- evidence_summary: 表格汇总本文件核心对比；缓存三问/分布式锁与 D09 集训、D06 Section 7、D12 构成 Cluster B 证据区。
