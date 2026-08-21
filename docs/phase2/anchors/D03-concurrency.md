# Anchors: D03 — 并发 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/并发 八股文.md`
- domain: Java
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. 进程 vs 线程
- concepts: 进程, 线程, 资源分配单位, CPU 调度单位, 共享资源
- evidence_summary: 进程是资源分配单位（独立内存）、线程是 CPU 调度单位（共享进程资源）；线程轻量但共享资源易并发问题。与 D10 操作系统同概念交叉。

## Section: 2. 创建线程方式
- concepts: Thread, Runnable, Callable+Future, 线程池
- evidence_summary: 四种方式：继承 Thread、实现 Runnable（无返回值不能抛受检）、Callable+Future（有返回值）、实际开发交给线程池。

## Section: 3. sleep() vs wait()
- concepts: sleep, wait, 释放锁, notify, 同步块
- evidence_summary: sleep 属 Thread 不释放锁任意位置；wait 属 Object 释放锁必须在同步块内、notify/notifyAll 唤醒。

## Section: 4. synchronized
- concepts: synchronized, 对象锁, 原子性, 可见性, 锁 this/Class/对象, 锁升级
- evidence_summary: synchronized 是最基础同步手段，对象锁保证原子性+可见性；实例方法锁 this、静态方法锁 Class、代码块锁指定对象；附锁升级演示链接（无锁→偏向→轻量→重量）。

## Section: 5. volatile
- concepts: volatile, 可见性, 禁止重排序, 不保证原子性, 双重检查单例
- evidence_summary: volatile 保证可见性+禁止部分重排序，不保证原子性；适合状态标记/开关/双重检查单例；不适合 i++ 读-改-写。

## Section: 6. CAS
- concepts: CAS, Compare And Swap, AtomicInteger, ABA 问题, 自旋
- evidence_summary: CAS 比较当前值与预期值相同则更新否则失败重试，无锁并发思想，AtomicInteger 依赖它；问题：ABA、自旋开销、只能单变量原子性。与 D12 知识概念 ABA 交叉。

## Section: 7. 乐观锁 vs 悲观锁
- concepts: 乐观锁, 悲观锁, CAS/版本号, synchronized/Lock
- evidence_summary: 悲观锁先加锁再操作（synchronized/Lock）；乐观锁先操作再校验（CAS/版本号）；冲突频繁用悲观、冲突不高用乐观。

## Section: 8. synchronized vs Lock
- concepts: ReentrantLock, 可中断, tryLock, 手动 unlock, AQS
- evidence_summary: synchronized 关键字语法级自动释放；Lock(ReentrantLock) API 手动 unlock、可中断/超时/尝试；简单同步用 synchronized、强控制用 Lock；附 AQS CLH 演示链接。

## Section: 9. 线程池
- concepts: ThreadPoolExecutor, corePoolSize, maximumPoolSize, keepAliveTime, workQueue, 拒绝策略, Executors 陷阱, execute vs submit
- evidence_summary: 线程池复用线程+控并发；核心参数 core/max/keepAlive/队列/handler；执行流程"先核心→再队列→再非核心→最后拒绝"；四种拒绝策略（Abort/CallerRuns/Discard/DiscardOldest）；不用 Executors（Fixed 无界队列 OOM、Cached 线程失控）；execute 无返回值、submit 返回 Future。

## Section: 10. 死锁
- concepts: 死锁, 互斥, 请求并持有, 不可剥夺, 循环等待, jstack
- evidence_summary: 死锁四必要条件（互斥/请求并持有/不可剥夺/循环等待）；避免：固定加锁顺序/减少嵌套/tryLock+超时；排查：jstack 看阻塞与锁等待。

## Section: 11. ThreadLocal
- concepts: ThreadLocal, ThreadLocalMap, 内存泄漏, remove, 线程池复用
- evidence_summary: ThreadLocal 每线程独立副本，用空间换线程隔离（非加锁）；场景：用户上下文/TraceId/DB 连接；风险：线程池不及时 remove→内存泄漏+数据污染；附 ThreadLocalMap GC key 演示链接。与 D06 Section 4 ThreadLocal 交叉。

## Section: 12. AtomicInteger
- concepts: AtomicInteger, CAS 原子类, volatile 对比
- evidence_summary: AtomicInteger 基于 CAS 原子自增/自减/更新，比加锁轻量；volatile 只保证可见性，AtomicInteger 保证原子更新。

## Section: 高频对比速记
- concepts: 对比汇总（进程/线程、sleep/wait、Runnable/Callable、synchronized/Lock、synchronized/volatile、乐观/悲观、volatile/AtomicInteger、execute/submit）
- evidence_summary: 表格汇总本文件核心对比；与 D02 集合（CHM/synchronizedMap）、D10 操作系统（进程线程/IO）构成跨文档 cluster 证据区。
