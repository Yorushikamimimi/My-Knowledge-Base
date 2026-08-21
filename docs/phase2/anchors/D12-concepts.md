# Anchors: D12 — 知识概念.md（noise / hard document）

- document: `Vault/Personal_Archive/10-Knowledge/backend/速查/知识概念.md`
- domain: 混合（高并发 / MySQL / Redis / 其他）— **用户确认作为 noise/hard document**
- 定位：跨域碎片概念速查；Gold 阶段应把本文件视为"容易把人带偏的检索干扰源"，锚点需标注碎片所属子域。
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 性能指标
- concepts: RT, P99, P99.9, 平均值掩盖
- evidence_summary: RT=响应总时间；P99=99% 请求响应上限，大厂排查看 P99/P99.9 不看平均值（被正常请求掩盖）。

## Section: 高并发六大问题
- concepts: 超卖, 热点竞争, DB 瓶颈, 重试风暴, 读写放大, 惊群效应
- evidence_summary: 六大问题定义表：超卖（锁失效多线程读旧库存）、热点竞争（海量线程争同一行锁/Redis 锁）、DB 瓶颈（慢 SQL/缺索引/连接池满）、重试风暴（超时自动重试流量放大）、读写放大（写 10B 重写 16KB 页）、惊群（热点缓存失效/锁释放瞬间唤醒所有等待线程）。与 D09（超卖/重试风暴）、D03（锁竞争）交叉。

## Section: 后端分层架构
- concepts: Controller, Service, Mapper/DAO, Entity, 瘦 Controller
- evidence_summary: 分层职责表：Controller 参数校验/协议转换/响应包装禁止业务逻辑；Service 业务编排/事务控制；Mapper 纯 CRUD；Entity 纯 POJO 无业务逻辑。

## Section: ABA 问题与版本号解决
- concepts: ABA, CAS, version 字段, 乐观锁
- evidence_summary: ABA=CAS 只比较值(1==1)但值经历了 A→B→A；解决：加 version 字段（只增不减）CAS 比较 version 而非业务值；SQL 示例 UPDATE ... SET amount=amount-1, version=version+1 WHERE id=? AND version=?。与 D03 Section 6（CAS ABA）交叉（Cluster D）。

## Section: MySQL 索引相关
- concepts: 回表, 覆盖索引, GIN 倒排索引, JSONB, 全文检索
- evidence_summary: 回表=二级索引只存主键 ID 需回主键索引查完整数据（两次查询）；覆盖索引=查询字段全在索引上无需回表性能提升；GIN 倒排适合 JSONB/数组/全文（值→行 ID）；JSONB 写入预解析读取免解析比 TEXT/JSON 快。与 D07 Section 1（回表/覆盖索引）交叉（Cluster C）。

## Section: MySQL 锁
- concepts: 行锁, 表锁, 死锁, 固定顺序加锁
- evidence_summary: 行锁=WHERE 命中主键/唯一索引只锁一行并发高；表锁=未命中索引锁整表并发降为 0（P0 事故）；死锁=两事务互持对方需要的锁，规避固定顺序加锁（先锁 ID 小）。与 D07 事务/索引交叉（Cluster C）。

## Section: 其他概念
- concepts: Tomcat, Gateway, 防抖 Debounce, Redis SETNX 防重, JSONB
- evidence_summary: Tomcat=Web 服务器/Servlet 容器（Spring Boot 内嵌，1.x 就有）；Gateway=Nginx/Spring Cloud Gateway 流量分发鉴权限流；防抖=停止操作后一段时间才发请求降无效 QPS；Redis SETNX 防重=`SETNX key "processing" EX 10` 必须加过期防死锁；JSONB 比 TEXT/JSON 快。与 D08 分布式锁（SETNX）、D09（防重）交叉。
