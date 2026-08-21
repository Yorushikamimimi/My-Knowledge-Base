# Anchor QA 审计 — Phase 2A-2a

> 审计对象：`docs/phase2/anchors/D01~D12-*.md`（123 个 section anchor）
> 审计方式：只读，逐一对照源文档 `Vault/Personal_Archive/10-Knowledge/backend/` 原文。
> 结论：未修改任何 anchor 文件；发现 **1 处确定错误 + 若干边界风险**，见 §2。

## 1. 总体统计

```text
HIGH   74   （适合直接出 Gold）
MEDIUM 45   （可用，但问题要谨慎限定）
LOW     4   （不建议第一版出题）
Total 123
```

## 2. 发现的锚点风险

### 2.1 确定错误（1 处，建议修正但需用户确认）

| Anchor | 问题 | 建议 |
|--------|------|------|
| D08 Section 8 分布式锁 — `concepts` 含 **Redisson** | D08 源文档全文 **0 次**出现 "Redisson"（已 grep 验证）。"Redisson Watchdog" 只存在于 D09 Section 8。这是从 D09 引入的跨文档概念污染。 | 从 D08 S8 concepts 删除 "Redisson"；Redisson 相关内容保留在 D09 S8。 |

### 2.2 概念锚定在"交互演示链接标题"上的风险（MEDIUM 级，不修改但需注意）

D03 S4、D07 S3 的 concepts/evidence 引用了 `../demos/*.html` 链接标题里的概念（锁升级、两阶段提交、Read View），但**正文并没有展开解释**。Gold 阶段若对这些概念出题，答案无法从正文 evidence 支撑，只能用"演示链接标题存在该概念"为证据，证据强度弱。

| Anchor | 链接标题概念 | 正文是否展开 |
|--------|-------------|-------------|
| D03 Section 4 synchronized | 无锁/偏向/轻量/重量锁升级 | 否（仅"答"一句+三个修饰位置） |
| D07 Section 3 MVCC | 版本链可见性/两阶段提交/隔离级别对比 | 否（正文仅 undo log+Read View+日志表） |

### 2.3 高频对比速记节（总结/过渡，不宜单独出题）

以下 anchor 是文档末尾的"高频对比速记"汇总表，本身是对前文的浓缩，不是独立证据。可作为**区别型问题的辅助 evidence**，但不应单独作为 expected source。

D01 S14、D02 S9、D03 S13、D04 S8、D05 S13、D07 S7、D08 S9、D10 S7、D11 S11（共 9 个，全部 MEDIUM）。

### 2.4 同一文档内概念重叠（注意去重）

| 文档 | 重叠 anchor | 说明 |
|------|------------|------|
| D01 | S1（==/equals）vs S8（hashCode/equals） | S1 侧重比较语义，S8 侧重 hashCode 契约，有重叠但可区分；出题时避免同题双锚 |
| D05 | S3（AOP）vs S10（JDK 代理 vs CGLIB） | S10 是 S3 的展开，代理对比题建议只锚 S10 |
| D09 | S7（缓存三大问题）vs D08 S5 | 跨文档刻意重叠（Cluster B），不是缺陷 |

### 2.5 section 过宽，Gold 需限定 evidence 子集

以下 anchor 单节包含多个可独立成题的子主题，Gold 必须限定到其中一部分 evidence，否则"该 section 是否命中"判定会模糊。

| Anchor | 过宽内容 | Gold 建议 |
|--------|----------|-----------|
| D03 Section 9 线程池 | 参数/流程/拒绝策略/Executors 陷阱/execute vs submit 5 个子主题 | 按子主题拆题（参数、流程、拒绝策略、为什么不用 Executors） |
| D05 Section 9 @Transactional | 默认回滚/失效场景表/传播行为 3 组 | 按组拆题（默认回滚规则、失效场景、传播） |
| D07 Section 1 索引 | B+Tree/聚簇非聚簇/覆盖/最左前缀/失效 5 组 | 按组拆题，每题只锚一个子主题 |
| D08 Section 8 分布式锁 | SETNX/解锁 Lua/风险/场景 4 组 | 按组拆题 |
| D09 Section 8 Watchdog | 主从不安全/续期/Fencing Token/降风险 4 组 | 按组拆题 |
| D06 Section 5 事务 | 与 D05 S9 高度重叠 | 跨文档题优先锚 D05 S9（更结构化），D06 S5 作次要 source |

### 2.6 D12 noise 文档的锚点定位

D12 是用户确认的 noise/hard 文档。其 S2 高并发六大问题、S4 ABA、S5/S6 MySQL 索引/锁与 D03/D07/D09 交叉。**D12 不应成为 positive 首选**，Gold 阶段它的价值是：①检索时被错误命中的干扰源；②跨文档区分题（同概念在 D12 与 D03/D07 哪个更权威）。

## 3. 逐篇评级明细

### D01 Java基础（14 sections: 7 HIGH / 7 MEDIUM / 0 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 == 和 equals() | HIGH | 语义明确，可出区别型 |
| S2 重载 vs 重写 | HIGH | |
| S3 String/StringBuilder/StringBuffer | HIGH | 选型题佳 |
| S4 基本类型 vs 包装类型 | HIGH | Integer 缓存实例具体 |
| S5 final/finally/finalize | MEDIUM | 易混，可出区别型，但三词并列答案集中 |
| S6 接口 vs 抽象类 | HIGH | |
| S7 异常体系 | HIGH | checked/unchecked + throw/throws |
| S8 hashCode() 和 equals() | MEDIUM | 与 S1 部分重叠 |
| S9 Java 参数传递 | MEDIUM | 单点结论，答案短 |
| S10 深拷贝 vs 浅拷贝 | MEDIUM | 单点结论 |
| S11 泛型 | MEDIUM | 要点短 |
| S12 反射 | MEDIUM | 要点短 |
| S13 NPE | HIGH | 有真实实例，场景题佳 |
| S14 高频对比速记 | MEDIUM | 汇总表，辅助用 |

### D02 集合（9: 3 HIGH / 5 MEDIUM / 1 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 List/Set/Map | MEDIUM | 概述，答案集中 |
| S2 ArrayList vs LinkedList | HIGH | 对比表+扩容 |
| S3 HashMap | HIGH | put 流程/树化/1.7vs1.8 密集 |
| S4 ConcurrentHashMap | HIGH | 1.7vs1.8/与 synchronizedMap 对比 |
| S5 HashSet | MEDIUM | 底层 HashMap 一句话 |
| S6 fail-fast | MEDIUM | modCount 单点 |
| S7 其他集合 | LOW | COW/LinkedHashMap/TreeMap 各一句，太散 |
| S8 选型速查 | MEDIUM | 表格式选型，可出场景题 |
| S9 高频对比速记 | MEDIUM | 汇总表 |

### D03 并发（13: 9 HIGH / 4 MEDIUM / 0 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 进程 vs 线程 | HIGH | 与 D10 S6 构成跨文档对 |
| S2 创建线程方式 | MEDIUM | 列举型 |
| S3 sleep() vs wait() | HIGH | 对比表佳 |
| S4 synchronized | MEDIUM | 正文短；锁升级仅链接标题 |
| S5 volatile | HIGH | 可见性/原子性边界明确 |
| S6 CAS | HIGH | 含 ABA 风险，与 D12 S4 交叉 |
| S7 乐观锁 vs 悲观锁 | HIGH | |
| S8 synchronized vs Lock | HIGH | |
| S9 线程池 | HIGH | 内容最丰富，需按子主题拆 |
| S10 死锁 | HIGH | 四条件+避免+排查 |
| S11 ThreadLocal | HIGH | 场景+泄漏风险，与 D06 S4 交叉 |
| S12 AtomicInteger | MEDIUM | 单点 |
| S13 高频对比速记 | MEDIUM | 汇总表 |

### D04 JVM（8: 5 HIGH / 3 MEDIUM / 0 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 JVM 内存区域 | HIGH | 五区域 |
| S2 堆 vs 栈 | HIGH | |
| S3 对象创建过程 | MEDIUM | 流程列举 |
| S4 垃圾回收 | HIGH | 可达性/算法/Minor vs Full |
| S5 类加载 | HIGH | 双亲委派完整 |
| S6 常见垃圾回收器 | MEDIUM | Serial/CMS/G1 各一句 |
| S7 OOM vs StackOverflow | HIGH | |
| S8 高频对比速记 | MEDIUM | 汇总表 |

### D05 Spring（13: 7 HIGH / 6 MEDIUM / 0 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 Spring 是什么 | MEDIUM | 概述 |
| S2 IoC / DI | HIGH | 与 D06 S2 交叉 |
| S3 AOP | HIGH | 代理底层，与 D06 S3 交叉 |
| S4 Bean 生命周期 | HIGH | |
| S5 常用注解 | MEDIUM | 表格式罗列 |
| S6 Spring MVC 执行流程 | HIGH | |
| S7 @SpringBootApplication | MEDIUM | 组合注解单点 |
| S8 Spring Boot 自动配置 | MEDIUM | 单点概念 |
| S9 @Transactional | HIGH | 最核心；失效场景表+传播 |
| S10 JDK 动态代理 vs CGLIB | HIGH | 与 S3 有重叠，代理对比题锚此 |
| S11 BeanFactory vs ApplicationContext | HIGH | |
| S12 Spring vs Spring Boot | MEDIUM | |
| S13 高频对比速记 | MEDIUM | 汇总表 |

### D06 微服务资料（13: 10 HIGH / 2 MEDIUM / 1 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 Servlet to Spring MVC | HIGH | |
| S2 IoC & DI | HIGH | 含循环依赖，比 D05 S2 更细 |
| S3 AOP | HIGH | 失效场景明确 |
| S4 ThreadLocal | HIGH | SecurityContextHolder 实例 |
| S5 声明式事务 | HIGH | 与 D05 S9 高度重叠 |
| S6 消息队列 MQ | HIGH | 幂等/ACK/DLQ 完整 |
| S7 Redis缓存 | HIGH | 与 D08 交叉 |
| S8 服务发现与RPC | HIGH | |
| S9 API Gateway | HIGH | |
| S10 分布式事务 | HIGH | Seata vs MQ 对比 |
| S11 Docker容器化 | MEDIUM | 部署域，与四大领域弱相关 |
| S12 CI/CD | MEDIUM | 部署域 |
| S13 架构全景图 | LOW | 总结/过渡节 |

### D07 MySQL（7: 6 HIGH / 1 MEDIUM / 0 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 索引 | HIGH | 内容最丰富，需按子主题拆 |
| S2 事务 | HIGH | ACID+隔离级别表 |
| S3 MVCC | HIGH | 快照/undo/Read View |
| S4 InnoDB vs MyISAM | HIGH | |
| S5 慢查询排查 | HIGH | EXPLAIN 字段 |
| S6 深分页 | HIGH | 优化方案具体 |
| S7 高频对比速记 | MEDIUM | 汇总表 |

### D08 Redis（9: 7 HIGH / 2 MEDIUM / 0 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 Redis 为什么快 | MEDIUM | 单点结论 |
| S2 数据类型与场景 | HIGH | 五类型表 |
| S3 RDB vs AOF | HIGH | |
| S4 过期删除 vs 内存淘汰 | HIGH | |
| S5 缓存穿透/击穿/雪崩 | HIGH | 与 D09 S7 重叠（Cluster B） |
| S6 BigKey / HotKey | HIGH | |
| S7 缓存一致性 | HIGH | Cache Aside 完整 |
| S8 分布式锁 | HIGH | **concepts 含 Redisson = 确定错误** |
| S9 高频对比速记 | MEDIUM | 汇总表 |

### D09 集训（12: 10 HIGH / 1 MEDIUM / 1 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 超卖问题分析 | HIGH | |
| S2 30分钟止血方案 | HIGH | 场景题佳 |
| S3 MySQL vs Redis 方案 | HIGH | |
| S4 三种一致性 | HIGH | |
| S5 Redis + Lua | HIGH | |
| S6 Key 设计 | HIGH | |
| S7 缓存三大问题 | HIGH | 与 D08 S5 重叠（Cluster B） |
| S8 分布式锁 Watchdog | HIGH | Redisson 在此处（正确） |
| S9 热点Key治理 | HIGH | |
| S10 秒杀完整链路 | HIGH | |
| S11 高分面试答法模板 | LOW | 话术模板，非事实证据 |
| S12 生产避坑清单 | MEDIUM | 清单式，可辅助场景题 |

### D10 操作系统（7: 4 HIGH / 3 MEDIUM / 0 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 用户态 vs 内核态 | HIGH | |
| S2 阻塞 IO vs 非阻塞 IO | HIGH | |
| S3 IO 多路复用 | MEDIUM | 一句话 |
| S4 select / poll / epoll | HIGH | 对比表 |
| S5 零拷贝 | HIGH | |
| S6 进程 vs 线程 | MEDIUM | 与 D03 S1 重复度高 |
| S7 高频对比速记 | MEDIUM | 汇总表 |

### D11 计算机网络（11: 4 HIGH / 6 MEDIUM / 1 LOW）
| Section | 评级 | 说明 |
|---------|------|------|
| S1 TCP vs UDP | HIGH | |
| S2 三次握手 | HIGH | |
| S3 四次挥手 | HIGH | |
| S4 HTTP vs HTTPS | MEDIUM | 单点结论 |
| S5 GET vs POST | MEDIUM | 语义+参数位置 |
| S6 Cookie/Session/Token | HIGH | |
| S7 URL 到页面返回 | MEDIUM | 流程列举 |
| S8 HTTP 状态码 | MEDIUM | 表格式记忆 |
| S9 HTTP/1.1 vs HTTP/2 | MEDIUM | 单点结论 |
| S10 长连接 vs 短连接 | LOW | 一句话 |
| S11 高频对比速记 | MEDIUM | 汇总表 |

### D12 知识概念（7: 2 HIGH / 5 MEDIUM / 0 LOW）— noise 文档
| Section | 评级 | 说明 |
|---------|------|------|
| S1 性能指标 | MEDIUM | RT/P99 定义 |
| S2 高并发六大问题 | HIGH | 与 D09 交叉，但 D12 是 noise 不作为首选 |
| S3 后端分层架构 | MEDIUM | |
| S4 ABA 问题 | HIGH | 与 D03 S6 交叉 |
| S5 MySQL 索引相关 | MEDIUM | 与 D07 S1 交叉 |
| S6 MySQL 锁 | MEDIUM | 与 D07 交叉 |
| S7 其他概念 | MEDIUM | 碎片 |

## 4. 推荐用于 Gold V1 的 anchor shortlist

### 4.1 首选 HIGH（每文档按价值排序，出题优先）

```text
D05 S9 @Transactional          ← 全库最高价值（失效场景+传播）
D07 S1 索引                    ← 子主题丰富（拆题）
D03 S9 线程池                  ← 子主题丰富（拆题）
D08 S7 缓存一致性 / D08 S8 分布式锁
D09 S8 分布式锁 Watchdog
D07 S2 事务 / D07 S3 MVCC
D05 S3 AOP / D05 S10 代理对比
D08 S5 缓存三问 / D09 S7 缓存三问（成对出题）
D03 S5 volatile / D03 S6 CAS / D03 S11 ThreadLocal
D01 S13 NPE（场景题）
D06 S4 ThreadLocal / D06 S5 事务 / D06 S6 MQ
```

### 4.2 成对/跨文档锚定（Cluster 题必用）

| Cluster | 首选 anchor 对 |
|---------|---------------|
| A Spring Proxy/Tx | D05 S9 ↔ D06 S5；D05 S10 ↔ D06 S3 |
| B Redis Cache/Lock | D08 S5 ↔ D09 S7；D08 S8 ↔ D09 S8 |
| C MySQL 内部 | D07 S1/S2/S3 内部互锚 + D12 S5/S6（区分题） |
| D Java 并发/集合 | D02 S4 ↔ D03 S8；D03 S6 ↔ D12 S4 |
| E JVM/线程 | D03 S1 ↔ D04 S2 |
| F 并发/OS | D03 S1 ↔ D10 S6 |

### 4.3 不建议第一版出题

D02 S7、D09 S11、D06 S13、D11 S10（LOW）+ 全部 9 个"高频对比速记"节（仅辅助）。
