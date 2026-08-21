# Anchors: D09 — Redis与分布式中间件集训.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/速查/Redis与分布式中间件集训.md`
- domain: Redis（含 MySQL/MQ 对比）
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. 高并发超卖问题分析
- concepts: 真超卖, 感知超卖, MySQL CAS 局限, Retry Storm, 热点行, 线程池阻塞, 幂等
- evidence_summary: 两种超卖定义（真=DB 负库存；感知=用户看到成功被取消）；MySQL CAS 扛不住万级 QPS 四原因（只冲突检测不吸流量/热点行单点/失败重试放大/线程池阻塞）；应用层根因（同步直写无缓冲/重试失控/缺幂等/成功态过早）。

## Section: 2. 30分钟止血方案
- concepts: 前端防重, 网关限流, 关闭重试, 服务降级, 快速熔断, 后续升级
- evidence_summary: 立刻做：前端防重+网关限流+关闭重试+服务降级(排队中)+快速熔断；不是 30 分钟能上的：Redis 预热/Lua/MQ/分布式锁/库存分段。

## Section: 3. MySQL vs Redis方案对比
- concepts: MySQL CAS, Redis+Lua, 吞吐量, 一致性, 超卖风险, 复杂度, 故障恢复
- evidence_summary: 对比表：MySQL CAS 吞吐低一致性局部强超卖风险高实现简单；Redis+Lua 吞吐高一致性弱（跨存储无原子事务）超卖风险低实现/运维/恢复复杂；适用：中低并发 vs 秒杀抢券。

## Section: 4. 三种一致性
- concepts: 数据一致性, 业务状态一致性, 用户感知一致性, 强一致性, 最终一致性
- evidence_summary: 三种一致性定义+示例（数据=不同存储对不上、业务状态=库存扣了订单失败、用户感知=先成功后说没货）；强一致代价性能差（Seata 全局锁）、最终一致异步重试补偿收敛。

## Section: 5. Redis + Lua原子扣减
- concepts: Lua, 原子执行, 抢资格, MQ, 死信队列 DLQ, 补偿, 幂等
- evidence_summary: Lua 保证 Redis 内多命令原子（判断+扣减+写标记）不被插队；不能保证：MQ 一定发送成功/消费成功/DB 提交成功/崩溃不丢消息；典型链路 Lua 扣减→发 MQ→订单消费→失败补偿（重试/DLQ/回补库存）；核心要点：Redis+Lua 管"资格"不管"结果"。

## Section: 6. Redis Key设计（秒杀场景）
- concepts: Key 设计, seckill:activity, seckill:item, seckill:stock, 幂等 key, 读热点, 写热点
- evidence_summary: 秒杀 Key 表：活动配置/商品详情/库存（热点写）/用户幂等/结果查询/分布式锁，各带 TTL；热点识别：读热点（详情/配置→多级缓存）、写热点（库存→Lua/分段）。

## Section: 7. 缓存三大问题
- concepts: 缓存击穿, 缓存穿透, 缓存雪崩, 布隆过滤器, 缓存空值, TTL 抖动
- evidence_summary: 击穿=热点 Key 过期瞬间高并发打穿 DB→分布式锁 Mutex 只允许一个线程查 DB 回写；穿透=恶意不存在 Key→布隆过滤器或缓存空值短 TTL(5min)；雪崩=大量 Key 同时过期→TTL 随机抖动(2h±10min)。与 D08 Section 5 重叠（Cluster B）。

## Section: 8. 分布式锁与Redisson Watchdog
- concepts: 主从切换, 锁丢失, Redisson Watchdog, 续期, TTL 30 秒, Fencing Token, 幂等, CAS 乐观锁, 分段锁
- evidence_summary: 单 Redis 主从不安全场景五步（A 获锁→Master 宕→未同步 Slave→B 新 Master 获锁→双持锁）；Watchdog 每 10 秒自动续期（默认 30s TTL）解决业务超时；风险：进程假死时 Watchdog 无法续期但恢复后误以为持锁；Fencing Token=每次取锁递增 Token 存储层拒绝旧 Token；降风险：幂等/CAS version/分段锁/合理 TTL（业务 1s 锁 3s）。与 D08 Section 8 深度重叠（Cluster B 核心）。

## Section: 9. 热点Key治理
- concepts: 紧急限流, 读写分离, 本地缓存 Caffeine, 多级缓存 L1/L2/L3, 热点分片, 异步预热, 降级开关
- evidence_summary: 30 分钟止血：紧急限流/读写分离/本地缓存；长期：多级缓存（L1 Caffeine/L2 Redis/L3 DB）、热点分片（stock:{sku}:1~10 随机读 Lua 批量扣）、异步预热、降级开关。

## Section: 10. 秒杀系统完整链路
- concepts: 完整链路图, CDN, 网关限流, Redis Lua, MQ, 订单服务, DLQ, 补偿, 状态机
- evidence_summary: 完整链路：用户→CDN→网关限流(令牌桶/漏桶)→Redis Lua 扣库存(幂等)→发 MQ→订单消费→MySQL 写订单(本地事务)→失败进 DLQ→补偿回滚；关键配置：限流 10k QPS、MQ 重试最多 3 次 1s/5s/15s、幂等 TTL 24h。

## Section: 11. 高分面试答法模板
- concepts: 面试答法, hotspot contention, retry storm, 30分钟止血, 长期升级
- evidence_summary: 面试套话模板：超卖本质=hotspot contention 引发 DB bottleneck 被 retry storm 放大；MySQL CAS 局限四句；Redis+Lua 解法两句；30 分钟止血重点；长期架构升级清单。

## Section: 12. 生产避坑清单
- concepts: Redis/MQ/一致性/性能避坑, Lua 不能发 MQ, Canal 不作为主补偿, 消息带上下文, 库存分段
- evidence_summary: 避坑清单：Lua 不能直接发 MQ、单主从锁不绝对安全、同 TTL 雪崩、幂等键 userId+skuId+activityId、Lua 返回值设计(0/1/2/-1)、Canal 不做主补偿、消息带完整上下文、补偿前加锁、订单状态机 INIT→RESERVED→CREATED→PAID→CANCELLED、库存分段 10 段。
