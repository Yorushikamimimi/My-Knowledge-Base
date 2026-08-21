# Anchors: D10 — 操作系统 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/操作系统 八股文.md`
- domain: 后端基础（操作系统）
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. 用户态 vs 内核态
- concepts: 用户态, 内核态, 系统调用, 安全性
- evidence_summary: 用户态权限低跑应用、内核态权限高管硬件；IO 操作需系统调用从用户态切内核态；区分原因：安全稳定防应用直接操作硬件。

## Section: 2. 阻塞 IO vs 非阻塞 IO
- concepts: 阻塞 IO, 非阻塞 IO, 线程膨胀, 上下文切换
- evidence_summary: 阻塞 IO 数据没准备好一直等；非阻塞立即返回之后再检查；阻塞问题：线程大量等待、高并发线程膨胀、上下文切换开销大。

## Section: 3. IO 多路复用
- concepts: IO 多路复用, 单线程监听多连接, 就绪处理
- evidence_summary: 一个线程同时监听多个连接谁就绪处理谁，提升高并发线程利用率。

## Section: 4. select / poll / epoll
- concepts: select, poll, epoll, fd 上限, 全量遍历, 就绪通知, Nginx/Netty
- evidence_summary: select fd 有限制每次全量遍历；poll 无固定上限仍全量遍历；epoll 就绪通知不全量扫描内核管理数据；select/poll 像轮询、epoll 像就绪通知；适用高并发（Nginx/Netty）。与 D03 线程池（高并发线程利用）弱交叉。

## Section: 5. 零拷贝
- concepts: 零拷贝, 用户态/内核态, CPU 开销, Kafka, Netty
- evidence_summary: 减少用户态/内核态重复拷贝降低 CPU 开销提升传输；不是完全不拷贝而是尽量少拷贝；应用 Kafka/Netty。

## Section: 6. 进程 vs 线程（OS 视角）
- concepts: 进程, 线程, 资源分配, 调度, 共享内存
- evidence_summary: 进程是资源分配基本单位、线程是调度执行基本单位；同进程线程共享内存更轻量但有并发安全问题。与 D03 Section 1 同概念（Java 视角 vs OS 视角，Cluster F）。

## Section: 高频对比速记
- concepts: 对比汇总（用户态/内核态、阻塞/非阻塞、select/poll/epoll、进程/线程）
- evidence_summary: 表格汇总本文件核心对比；进程 vs 线程与 D03、IO 多路复用与后端高并发构成跨文档证据区。
