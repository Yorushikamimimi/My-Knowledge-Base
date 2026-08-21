# Corpus V1 — 真实技术笔记语料集（固化清单）

> Phase 2A-1 输出：从 Obsidian Vault 筛选出的第一批 Retrieval Benchmark 语料。
> 状态：**已由用户确认（5/5 确认点）**，进入锚点层阶段。
> 本文件只记录"哪些文档入选、为什么"，**不包含任何 Gold Question**。

## 1. 来源与路径

- Vault 根：`/Users/yang/Vaults/main-vault/Obsidian_repo`
- 技术区：`Vault/Personal_Archive/10-Knowledge/backend/`
- 本文件中的所有路径均为**相对 Vault 根目录**。

## 2. Corpus V1 清单（12 篇）

| Corpus ID | Domain | File（相对 Vault 根） | Main Topic | Why Included |
|-----------|--------|------|-------------|--------------|
| D01 | Java | `Vault/Personal_Archive/10-Knowledge/backend/八股/Java基础 八股文.md` | Java 语言基础（==/equals、String、异常、泛型、反射、NPE） | 主题明确、可问性强；与 D02/D03 构成 Java 域 cluster |
| D02 | Java | `Vault/Personal_Archive/10-Knowledge/backend/八股/集合 八股文.md` | HashMap/CHM/ArrayList 与选型 | 与 D03(JUC) 有 CHM/CAS/锁语义重叠，测试检索区分 |
| D03 | Java | `Vault/Personal_Archive/10-Knowledge/backend/八股/并发 八股文.md` | 线程池、synchronized、volatile、CAS、ThreadLocal、死锁 | 高密度原理+场景题来源；与 D02/D04/D10 多向交叉 |
| D04 | Java | `Vault/Personal_Archive/10-Knowledge/backend/八股/JVM 八股文.md` | 内存区、GC、类加载、OOM | 与 D03 线程/栈交叉；补足 Java 域 |
| D05 | Spring | `Vault/Personal_Archive/10-Knowledge/backend/八股/Spring ， Spring Boot 八股文.md` | IoC/AOP/@Transactional/代理/MVC | 核心 Spring 文档；事务失效表是 Gold 金矿；与 D06 构成 cluster |
| D06 | Spring | `Vault/Personal_Archive/10-Knowledge/backend/速查/全流程后端微服务资料.md` | Spring MVC/IoC/AOP/事务 + MQ/缓存 | 与 D05 语义高度重叠（proxy/@Transactional），刻意制造混淆；1-7 节为 Spring 域，8-12 节为微服务域 |
| D07 | MySQL | `Vault/Personal_Archive/10-Knowledge/backend/八股/MySQL 八股文.md` | 索引/B+Tree、事务隔离、MVCC、日志、深分页 | 唯一独立 MySQL 笔记；文档内 cluster 天然存在 |
| D08 | Redis | `Vault/Personal_Archive/10-Knowledge/backend/八股/Redis 八股文.md` | 数据结构、RDB/AOF、缓存三问、分布式锁 | 核心 Redis 文档；与 D09 构成 Redis cluster |
| D09 | Redis | `Vault/Personal_Archive/10-Knowledge/backend/速查/Redis与分布式中间件集训.md` | 缓存三问、分布式锁、Lua、秒杀链路 | 与 D08 重叠但深度不同（生产向）；测试"同一概念两种深度" |
| D10 | 后端 | `Vault/Personal_Archive/10-Knowledge/backend/八股/操作系统 八股文.md` | 线程/进程、IO 多路复用、epoll、零拷贝 | 与 D03(线程/锁)交叉；补后端基础 |
| D11 | 后端 | `Vault/Personal_Archive/10-Knowledge/backend/八股/计算机网络 八股文.md` | TCP/UDP、握手、HTTP/HTTPS、Cookie/Session/Token | 补后端基础；与 D07/D08 的连接语义弱关联 |
| D12 | 混合(noise/hard) | `Vault/Personal_Archive/10-Knowledge/backend/速查/知识概念.md` | 高并发六问、MySQL 索引/锁、Redis SETNX | 用户确认作为 noise/hard document：跨域混合碎片，测试检索器不被带偏 |

## 3. 用户确认记录（2026-08-21）

1. **MySQL 单篇**：接受 D07 单篇，不人为拆分 → 确认
2. **D06 混合微服务资料**：接受纳入（1-7 节 Spring 域 + 8-12 节微服务域）→ 确认
3. **D10/D11/D12**：全部纳入；**D12 明确作为 noise/hard document** → 确认
4. **Corpus V1 固定 12 篇**：不为了凑 15 篇强行扩充 → 确认
5. **八股速记风格**：接受；**Gold 只以文档实际内容为准** → 确认

## 4. 领域分布

```text
Java   4 篇   (D01-D04)
Spring 2 篇   (D05-D06)
MySQL  1 篇   (D07)
Redis  2 篇   (D08-D09)
后端基础 3 篇  (D10-D12，其中 D12 为 noise/hard)
Total  12 篇
```

## 5. Confusion Clusters（锚点层必须支持跨文档锚定）

| Cluster | 文档 | 容易混淆的语义 |
|---------|------|----------------|
| A — Spring Proxy/Transaction | D05 × D06 | proxy、@Transactional 失效、AOP、Bean、注入 |
| B — Redis Cache/Lock | D08 × D09 | 缓存穿透/击穿/雪崩、分布式锁、SETNX/Lua、过期淘汰 |
| C — MySQL 内部概念 | D07 内部 + D12 | B+Tree/回表/覆盖索引、隔离级别/Read View、redo/undo/binlog |
| D — Java 并发/集合 | D02 × D03 × D12 | ConcurrentHashMap、CAS、synchronized、ABA |
| E — JVM/线程 | D03 × D04 | 线程栈、堆、锁、GC |
| F — 并发/OS | D03 × D10 | 进程 vs 线程、锁、IO |

## 6. 锚点层规则（Phase 2A-2 锚点文件必须遵守）

- 锚点字段：`document` + `section` + `concepts` + `evidence_summary`。
- **禁止绑定 chunk_index**（Phase 2B 会测不同 chunk 参数）。
- 同一问题允许多个 `expected documents/sections`（跨文档 cluster 场景）。
- 锚点文件放 `docs/phase2/anchors/D<NN>-<slug>.md`，每篇一个文件。
- Gold Question 属于 Phase 2A-3，本阶段不生成。

## 7. 已知数据质量风险（锚点时注意）

- 八股速记风格：结论 + 一句话要点，解释深度有限；证据以文档实际内容为准。
- D05×D06、D08×D09 存在真实内容重叠（刻意保留）。
- 部分文档含 `../demos/*.html` 链接与 Windows 路径噪音（D13 无，D06 有 Dockerfile/YAML 代码块）。
- D12 主题不纯（noise/hard），锚点需标注为"跨域混合"。
- JVM(99行)/操作系统(62行) 篇幅偏短，预计每篇仅 1-3 个 chunk（Phase 2B 观察）。
