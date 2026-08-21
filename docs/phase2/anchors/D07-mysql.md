# Anchors: D07 — MySQL 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/MySQL 八股文.md`
- domain: MySQL
- 用户确认：接受 MySQL 单篇、不拆分；文档内 cluster 天然存在。
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. 索引
- concepts: B+Tree, 聚簇索引, 非聚簇索引, 回表, 覆盖索引, 最左前缀, 索引失效, 空间换时间
- evidence_summary: 索引=帮助快速查找的数据结构，空间换时间；B+Tree 层数低磁盘 IO 少、叶子有序链接适合范围查询、比二叉树/红黑树层数低；聚簇=索引数据一起（InnoDB 主键，叶子存整行）、非聚簇=叶子存主键需回表；覆盖索引=查询字段都在索引里直接返回；最左前缀=(a,b,c) 从最左列匹配、范围后列利用下降；失效场景：函数/计算/隐式转换、不满足最左前缀、LIKE '%abc'、OR 不当、区分度太低。

## Section: 2. 事务
- concepts: ACID, 原子性, 一致性, 隔离性, 持久性, 隔离级别, 脏读, 不可重复读, 幻读
- evidence_summary: ACID 四特性定义表；隔离级别表（RU 脏读有、RC 不可重复读有、RR MySQL 默认不可重复读无幻读 InnoDB 部分解决、Serializable 全无）；三种读异常定义：脏读=读未提交、不可重复读=同行前后不一致、幻读=范围查询行数变了。

## Section: 3. MVCC
- concepts: MVCC, 一致性快照, undo log, Read View, redo log, binlog, 两阶段提交
- evidence_summary: MVCC 多版本并发控制读写少互阻，普通 SELECT 读一致性快照不阻塞写；依赖 undo log（旧版本）+ Read View（可见性判断）；三种日志：redo=崩溃恢复持久性、undo=回滚+MVCC 多版本、binlog=归档主从复制；附版本链可见性/两阶段提交演示链接。

## Section: 4. InnoDB vs MyISAM
- concepts: InnoDB, MyISAM, 事务, 行锁, 表锁, 外键
- evidence_summary: InnoDB 支持事务/行锁/外键适合高并发 OLTP；MyISAM 无事务/表锁/无外键读多写少已少用。

## Section: 5. 慢查询排查
- concepts: EXPLAIN, type, key, rows, Extra, Using filesort, Using temporary
- evidence_summary: 排查链路：定位 SQL→EXPLAIN→检查索引→看写法数据量；EXPLAIN 重点：type 访问方式、key 实际索引、rows 估算行数、Extra 额外开销（filesort/temporary）。

## Section: 6. 深分页
- concepts: LIMIT 深分页, 游标分页, 先查 ID 再回表
- evidence_summary: LIMIT 100000,10 慢因先扫描丢弃前 10 万行；优化：游标分页（WHERE id>last_id LIMIT 10）、先查 ID 再回表（IN 子查询）。

## Section: 高频对比速记
- concepts: 对比汇总（聚簇/非聚簇、回表/覆盖、redo/undo/binlog、脏读/不可重复读/幻读、InnoDB/MyISAM、行锁/表锁）
- evidence_summary: 表格汇总本文件核心对比；其中事务/MVCC/锁概念与 D12 知识概念（MySQL 索引/锁）构成 Cluster C 证据区。
