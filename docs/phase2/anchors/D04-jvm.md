# Anchors: D04 — JVM 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/JVM 八股文.md`
- domain: Java
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. JVM 内存区域
- concepts: 堆, 虚拟机栈, 本地方法栈, 方法区, 程序计数器, Metaspace
- evidence_summary: 五区域：堆（线程共享存对象）、栈（线程私有存局部变量/栈帧）、本地方法栈、方法区（JDK8+ 元空间 Metaspace 用本地内存）、程序计数器。

## Section: 2. 堆 vs 栈
- concepts: 堆, 栈, 线程共享, GC, 局部变量
- evidence_summary: 栈存局部变量和方法调用（线程私有、方法结束自动弹出）；堆存对象实例（线程共享需 GC）；对象在堆、引用变量可能在栈。

## Section: 3. 对象创建过程
- concepts: 类加载检查, 分配内存, 初始化零值, 对象头, 构造方法
- evidence_summary: 对象创建五步：类加载检查→分配内存→初始化零值→设置对象头→执行构造方法。

## Section: 4. 垃圾回收
- concepts: 可达性分析, GC Roots, 标记-清除, 复制, 标记-整理, Minor GC, Full GC, 循环引用
- evidence_summary: GC 主要回收堆，用可达性分析（GC Roots 出发不可达即垃圾），不用引用计数（循环引用失效）；三种算法：标记-清除（碎片）、复制（存活少）、标记-整理（减碎片）；Minor GC 新生代频高成本小、Full GC 涉及老年代暂停长尽量避免。

## Section: 5. 类加载
- concepts: 加载, 验证, 准备, 解析, 初始化, 双亲委派, Bootstrap/Extension/Application
- evidence_summary: 类加载五阶段：加载→验证→准备→解析→初始化；双亲委派：先让父加载器尝试、父加载不了自己再加载；作用避免重复加载+保护核心库；三层 Bootstrap→Extension/Platform→Application；可自定义加载器打破（SPI/热部署）。

## Section: 6. 常见垃圾回收器
- concepts: Serial, CMS, G1, Region
- evidence_summary: Serial 单线程简单；CMS 低停顿但有碎片；G1 按 Region 划分、大堆更均衡更现代。

## Section: 7. OOM vs StackOverflow
- concepts: OOM, StackOverflow, 堆不足, 元空间不足, 无限递归
- evidence_summary: OOM 内存不够（堆/元空间不足，常见对象过多/泄漏/缓存无限增长）；StackOverflow 栈太深（递归无终止/调用链过深）。

## Section: 高频对比速记
- concepts: 对比汇总（堆/栈、Minor/Full GC、CMS/G1、OOM/StackOverflow）
- evidence_summary: 表格汇总本文件核心对比；堆 vs 栈、线程相关与 D03 并发域、D10 操作系统交叉。
