# Gold Draft V1 人工审核表

> 对应文件：`docs/phase2/gold-draft-v1.json`（30 条）
> 用途：人工逐条复核。每条列出 question / behavior / difficulty / cluster / expected sources / evidence / benchmark 价值 / 风险。
> 判定口径：`source_match=any`，命中任意 expected source 即 Retrieval Hit；Gold 只以 Vault 实际内容为准。

---

## Q001
- Question: 在同一个类里，一个方法直接调用另一个标注了 @Transactional 的方法，为什么事务可能不生效？
- Behavior: answer | Difficulty: medium | Cluster: A
- Expected Source(s): D05 「9. @Transactional」
- Evidence Summary: D05 S9 失效场景表第一行：同类内部调用 this.xxx() 绕过代理。
- Why this is a useful benchmark case: 与历史 synthetic Test A 同题（Baseline 0.7203），可对照真实 Corpus 表现；原理型。
- Risk / ambiguity: 低。答案锚定单一 section，证据直接。

## Q002
- Question: Spring 事务传播行为里 REQUIRED 和 REQUIRES_NEW 有什么区别？
- Behavior: answer | Difficulty: easy | Cluster: A
- Expected Source(s): D05 「9. @Transactional」
- Evidence Summary: D05 S9 传播行为两行：REQUIRED 有则加入无则新建；REQUIRES_NEW 强制新开。
- Why this is a useful benchmark case: 区别型，属于面试高频；D05 唯一权威源。
- Risk / ambiguity: 低。REQUIRES_NEW 语义明确。

## Q003
- Question: Spring AOP 的底层动态代理在什么情况下会用 JDK 动态代理，什么情况下会用 CGLIB？
- Behavior: answer | Difficulty: medium | Cluster: A
- Expected Source(s): D05 「3. AOP」; D05 「10. JDK 动态代理 vs CGLIB」
- Evidence Summary: S3 给原则（有接口 JDK、无接口 CGLIB）；S10 给完整对比表。
- Why this is a useful benchmark case: 同文档双 section，测试检索是否把"原则"与"对比表"都召回。
- Risk / ambiguity: 中。两 section 是"概括 vs 展开"关系，any 判定下任一命中即 Hit，能区分是否过度依赖表格。

## Q004
- Question: 方法里用 try/catch 把异常吞掉之后，为什么 @Transactional 可能不会回滚？
- Behavior: answer | Difficulty: hard | Cluster: A
- Expected Source(s): D05 「9. @Transactional」; D06 「5. 声明式事务 @Transactional」
- Evidence Summary: D05 失效场景表"catch 吞掉"；D06 S5 try-catch 陷阱（需 throw 或 setRollbackOnly）。
- Why this is a useful benchmark case: Cluster A 跨文档：同一概念两文档表述不同，测检索能否双命中。
- Risk / ambiguity: 低-中。两 section 各自独立足够（D05 S9 "Spring 感知不到异常"；D06 S5 "catch 住异常不抛出+修复方式"），any 判定下任一命中即 Hit，非 compound。

## Q005
- Question: 缓存穿透是什么问题，一般怎么解决？
- Behavior: answer | Difficulty: easy | Cluster: B
- Expected Source(s): D08 「5. 缓存穿透 / 击穿 / 雪崩」
- Evidence Summary: D08 S5 表格：穿透=查不存在数据每次打 DB；解法缓存空值/布隆/参数校验。
- Why this is a useful benchmark case: 事实型基础题；与 D09 S7 同概念，可观察检索是否串到深度版。
- Risk / ambiguity: 低。

## Q006
- Question: 缓存击穿和缓存雪崩本质上的区别是什么？
- Behavior: answer | Difficulty: medium | Cluster: B
- Expected Source(s): D08 「5. 缓存穿透 / 击穿 / 雪崩」; D09 「7. 缓存三大问题」
- Evidence Summary: 击穿=单热点失效；雪崩=大量 key 同时失效。D08/D09 均覆盖。
- Why this is a useful benchmark case: 区别型 + 跨文档；D08 简洁版 vs D09 生产版，测检索深度匹配。
- Risk / ambiguity: 中。两文档都有答案，any 判定宽松；人工确认"本质区别"表述两处一致。

## Q007
- Question: Redis 分布式锁为什么释放锁的时候要用 Lua 脚本？
- Behavior: answer | Difficulty: medium | Cluster: B
- Expected Source(s): D08 「8. 分布式锁」
- Evidence Summary: D08 S8：解锁用 Lua「判断 value+删除 key」必须原子。
- Why this is a useful benchmark case: 原理型；锚定 D08（已修正 Redisson 污染后概念边界干净）。
- Risk / ambiguity: 低。evidence 核对：D09 S8 全文无 Lua 解锁机制（仅主从切换/Watchdog/Fencing Token），确认不加入 source；D08 S8 单独足够。

## Q008
- Question: 拿到分布式锁之后直接执行 DEL 释放，为什么可能会误删别人的锁？
- Behavior: answer | Difficulty: hard | Cluster: B
- Expected Source(s): D08 「8. 分布式锁」
- Evidence Summary: D08：value 存 UUID 解锁前校验，直接 DEL 无法区分持锁人。
- Why this is a useful benchmark case: 场景型；要求理解"锁标记与持锁人"关系，非背诵。
- Risk / ambiguity: 低。D09 S8 主从切换是"锁丢失"相邻概念、非 DEL 误删机制，已从 source 删除；D08 S8 单独足够。

## Q009
- Question: 什么是覆盖索引，它为什么能避免回表？
- Behavior: answer | Difficulty: easy | Cluster: C
- Expected Source(s): D07 「1. 索引」
- Evidence Summary: D07 S1：查询字段都在索引里→直接返回，不需要回表。
- Why this is a useful benchmark case: 事实型；MySQL 域基础。
- Risk / ambiguity: 低。

## Q010
- Question: InnoDB 的聚簇索引和非聚簇索引在叶子节点上存的内容有什么区别？
- Behavior: answer | Difficulty: medium | Cluster: C
- Expected Source(s): D07 「1. 索引」
- Evidence Summary: D07 S1：聚簇叶子存整行、非聚簇叶子存主键值需回表。
- Why this is a useful benchmark case: 区别型；与回表/覆盖索引语义纠缠，测检索精度。
- Risk / ambiguity: 低-中。D12 S5 也提及回表/覆盖——检索可能误命中 D12（noise 文档），正是设计意图。

## Q011
- Question: MySQL 默认的事务隔离级别是什么，它解决了哪些问题？
- Behavior: answer | Difficulty: easy | Cluster: C
- Expected Source(s): D07 「2. 事务」
- Evidence Summary: D07 S2 隔离级别表：RR 是 MySQL 默认；不可重复读无、幻读 InnoDB 部分解决。
- Why this is a useful benchmark case: 事实型；含"部分解决"边界表述，测检索是否抓全。
- Risk / ambiguity: 中。答案隐含"幻读部分解决"，若只答"RR"算部分正确——人工确认判定粒度。

## Q012
- Question: MVCC 为什么能让普通 SELECT 读不阻塞写操作？
- Behavior: answer | Difficulty: hard | Cluster: C
- Expected Source(s): D07 「3. MVCC」
- Evidence Summary: D07 S3：普通 SELECT 读一致性快照不阻塞写；依赖 undo log + Read View。
- Why this is a useful benchmark case: 原理型；MySQL 域最难锚点之一。
- Risk / ambiguity: 中。正文未展开"版本链"细节（链接标题有），答案以正文快照+undo+Read View 为限。

## Q013
- Question: HashMap 为什么在多线程环境下不安全？
- Behavior: answer | Difficulty: easy | Cluster: D
- Expected Source(s): D02 「3. HashMap」
- Evidence Summary: D02 S3：无同步控制，并发 put/resize 数据覆盖/丢失/结构异常。
- Why this is a useful benchmark case: 事实型；Java 集合域基础。
- Risk / ambiguity: 低。

## Q014
- Question: ConcurrentHashMap 在 JDK 1.7 和 1.8 的实现有什么区别？
- Behavior: answer | Difficulty: medium | Cluster: D
- Expected Source(s): D02 「4. ConcurrentHashMap」
- Evidence Summary: D02 S4：1.7 Segment 分段锁；1.8 CAS+synchronized 数组+链表+红黑树。
- Why this is a useful benchmark case: 区别型；版本对比题，检索需定位正确文档（D03 也有 CAS）。
- Risk / ambiguity: 中。CAS 概念在 D03 S6 也出现，检索可能误命中 D03——Cluster D 设计意图。

## Q015
- Question: 线程池场景下使用 ThreadLocal 为什么可能造成内存泄漏？
- Behavior: answer | Difficulty: hard | Cluster: D
- Expected Source(s): D03 「11. ThreadLocal」
- Evidence Summary: D03 S11 风险：线程池不及时 remove→内存泄漏、数据污染。
- Why this is a useful benchmark case: 原理型；单 section 完整支撑"内存泄漏"。
- Risk / ambiguity: 低。D06 S4 讲的是"串号/数据泄露"非"内存泄漏"，单独不足，已从 source 删除；非 compound。

## Q016
- Question: Minor GC 和 Full GC 有什么区别？
- Behavior: answer | Difficulty: easy | Cluster: E
- Expected Source(s): D04 「4. 垃圾回收」
- Evidence Summary: D04 S4：Minor 回收新生代频率高成本小；Full 涉及老年代暂停长。
- Why this is a useful benchmark case: 区别型；JVM 域基础。
- Risk / ambiguity: 低。

## Q017
- Question: 双亲委派机制解决了什么问题，它是怎么工作的？
- Behavior: answer | Difficulty: medium | Cluster: E
- Expected Source(s): D04 「5. 类加载」
- Evidence Summary: D04 S5：先让父加载器尝试；作用避免重复加载+保护核心库；三层结构。
- Why this is a useful benchmark case: 原理型；类加载完整锚点。
- Risk / ambiguity: 低。

## Q018
- Question: 进程和线程的根本区别是什么？
- Behavior: answer | Difficulty: easy | Cluster: F
- Expected Source(s): D03 「1. 进程 vs 线程」; D10 「6. 进程 vs 线程（OS 视角）」
- Evidence Summary: D03 S1 与 D10 S6 均给出：资源分配单位 vs CPU 调度单位、共享资源。
- Why this is a useful benchmark case: 跨视角（Java vs OS）同概念；测检索是否双命中。
- Risk / ambiguity: 中。两 section 表述几乎相同——本质是"同概念两处"，any 判定宽松。

## Q019
- Question: epoll 相比 select 在高并发场景下为什么更高效？
- Behavior: answer | Difficulty: hard | Cluster: F
- Expected Source(s): D10 「4. select / poll / epoll」
- Evidence Summary: D10 S4：select 全量遍历+用户态拷贝；epoll 就绪通知内核管理。
- Why this is a useful benchmark case: 原理型；OS 域最丰富锚点。
- Risk / ambiguity: 低-中。答案多要点（fd 上限/遍历方式/数据传递），需检索召回完整 section。

## Q020
- Question: Java 中什么情况下会触发 NullPointerException，常见防御方式有哪些？
- Behavior: answer | Difficulty: easy | Cluster: (无)
- Expected Source(s): D01 「NPE（NullPointerException）」
- Evidence Summary: D01 S13：null 上调用方法触发；防御判空/Optional/日志；含真实实习实例。
- Why this is a useful benchmark case: 场景型；唯一带真实项目实例的 Java 基础锚点。
- Risk / ambiguity: 低。

## Q021
- Question: Cookie、Session 和 Token 三者有什么区别，各自的适用场景是什么？
- Behavior: answer | Difficulty: medium | Cluster: (无)
- Expected Source(s): D11 「6. Cookie / Session / Token」
- Evidence Summary: D11 S6 三者不在同一层面：Cookie 浏览器存储载体、Session 服务端会话状态、Token 客户端认证凭证；对比表（存储/适用）；前后端分离更常用 Token（无状态/易扩展/多端）。
- Why this is a useful benchmark case: D11 计算机网络域唯一 positive（原 D11 无任何题，召回能力无法测试）；区别型。
- Risk / ambiguity: 低。单 section 独立足够。（替换原 Cache Aside 题：D06 S7 只陈述"更新策略"不解释"为什么"，单独不足，且 B cluster 原题量最多。）

## Q022
- Question: MySQL 深分页（比如 LIMIT 100000, 10）为什么慢，有什么优化思路？
- Behavior: answer | Difficulty: medium | Cluster: C
- Expected Source(s): D07 「6. 深分页」
- Evidence Summary: D07 S6：先扫描丢弃前 10 万行；优化游标分页或先查 ID 再回表。
- Why this is a useful benchmark case: 场景型；生产常见问题。
- Risk / ambiguity: 低。

## Q023（negative / out-of-corpus）
- Question: Kafka ISR 的工作机制是什么？
- Behavior: refuse | Difficulty: hard | Cluster: (无)
- Expected Source(s): []（无）
- Evidence Summary: Corpus V1 无任何 Kafka 内容。
- Why refuse: 四大领域+后端基础文档均无 Kafka；历史 baseline 0.4781>0.35 曾被错误放行，是 Phase 2B 阈值实验基准 case。
- Likely false-positive source: 无强候选（D06 S6 MQ 最接近，但讨论 RabbitMQ 语义）。

## Q024（negative / out-of-corpus）
- Question: ZooKeeper 的 ZAB 协议是如何保证数据一致性的？
- Behavior: refuse | Difficulty: medium | Cluster: (无)
- Expected Source(s): []（无）
- Evidence Summary: Corpus V1 无 ZooKeeper/ZAB/共识协议任何内容。
- Why refuse: ZAB 协议机制完全不在 Corpus。
- Likely false-positive source: 无（零相邻概念）。（修订：原 gRPC/Thrift 序列化题因 D06 S8 存在 RPC/Feign/序列化相邻概念不够 clean，换题。）

## Q025（negative / out-of-corpus）
- Question: Kubernetes 的 Pod 是怎么被调度到节点的？
- Behavior: refuse | Difficulty: medium | Cluster: (无)
- Expected Source(s): []（无）
- Evidence Summary: D06 S11 只提 K8s 自动扩缩容/自愈一句话。
- Why refuse: Pod 调度（kube-scheduler 策略）不在 Corpus。
- Likely false-positive source: D06 「11. Docker容器化」。

## Q026（negative / out-of-corpus）
- Question: Prometheus 的拉取式指标采集和告警规则是怎么实现的？
- Behavior: refuse | Difficulty: hard | Cluster: (无)
- Expected Source(s): []（无）
- Evidence Summary: Corpus V1 无 Prometheus/监控/指标采集任何内容。
- Why refuse: Prometheus 拉取模型与告警规则完全不在 Corpus。
- Likely false-positive source: 无（零相邻概念）。（修订：原 Elasticsearch 题因 D12 S5 存在"倒排索引"字面相邻概念不够 clean，换题。）

## Q027（negative / hard）
- Question: G1 垃圾回收器里的 SATB 和 RSet 分别是怎么工作的？
- Behavior: refuse | Difficulty: hard | Cluster: E
- Expected Source(s): []（无）
- Evidence Summary: D04 S6 仅"G1 按 Region 划分堆、大堆更均衡"一句话。
- Why refuse: 无 SATB/RSet 实现细节；Corpus 不足以支撑机制回答。
- Likely false-positive source: D04 「6. 常见垃圾回收器」（G1 字面命中）——Retriever 极可能召回此 section。

## Q028（negative / hard）
- Question: ReentrantLock 的 AQS 等待队列具体是怎么实现公平锁和非公平锁的？
- Behavior: refuse | Difficulty: hard | Cluster: D
- Expected Source(s): []（无）
- Evidence Summary: D03 S8 有 ReentrantLock 对比表 + AQS 演示链接标题，但正文无队列/公平实现。
- Why refuse: 链接标题不算正文 evidence；公平锁实现不在 Corpus。
- Likely false-positive source: D03 「8. synchronized vs Lock」（ReentrantLock/AQS 字面命中）。

## Q029（negative / hard）
- Question: MySQL 在可重复读隔离级别下是怎么用 Next-Key Lock 解决幻读的？
- Behavior: refuse | Difficulty: hard | Cluster: C
- Expected Source(s): []（无）
- Evidence Summary: D07 S2 仅"RR 幻读 InnoDB 部分解决"，全文无 Next-Key Lock。
- Why refuse: Next-Key Lock/间隙锁机制不在 Corpus。
- Likely false-positive source: D07 「2. 事务」（幻读/隔离级别字面命中）。

## Q030（negative / hard）
- Question: Redis Sentinel 在主节点宕机后是怎么完成故障转移的？
- Behavior: refuse | Difficulty: hard | Cluster: B
- Expected Source(s): []（无）
- Evidence Summary: D08 S8/D09 S8 仅提"主从切换→锁可靠性风险"。
- Why refuse: Sentinel 选举/故障转移机制不在 Corpus。
- Likely false-positive source: D08 「8. 分布式锁」（主从切换字面命中）。
