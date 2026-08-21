# Anchors: D01 — Java基础 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/Java基础 八股文.md`
- domain: Java
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. == 和 equals()
- concepts: `==`, `equals()`, `hashCode()`, 字符串常量池, 引用比较, 值比较
- evidence_summary: `==` 基本类型比值、引用类型比地址；`equals()` 默认比地址，String 重写后比内容；重写 equals 必须重写 hashCode；String 用 `==` 有时为 true 是常量池原因。

## Section: 2. 重载 vs 重写
- concepts: 重载, 重写, 编译期多态, 运行时多态, private/static 方法
- evidence_summary: 重载=同类同名不同参数（编译期）；重写=子类重实现父类方法（运行时）；private/static 不能重写，static 同名是隐藏。

## Section: 3. String / StringBuilder / StringBuffer
- concepts: String 不可变, StringBuilder 线程不安全, StringBuffer 线程安全, 拼接场景选型
- evidence_summary: String 不可变；StringBuilder 可变线程不安全性能高；StringBuffer 可变线程安全性能低；场景：少量用 String、单线程拼接 StringBuilder、多线程共享 StringBuffer；不可变好处：线程安全/哈希稳定/常量池复用。

## Section: 4. 基本类型 vs 包装类型
- concepts: 基本类型, 包装类型, 拆箱 NPE, Integer 缓存 -128~127
- evidence_summary: 基本类型存值、包装类型是对象；泛型/集合只能用包装类型；包装可表示 null 但拆箱可能 NPE；`Integer.valueOf()` 缓存 -128~127，127==127 true、128==128 false。

## Section: 5. final / finally / finalize
- concepts: final, finally, finalize, System.exit
- evidence_summary: final 修饰变量/方法/类；finally 异常代码块（不保证 100% 执行，如 System.exit）；finalize 是 GC 前回调已废弃；final 引用地址不可变但对象内容可变。

## Section: 6. 接口 vs 抽象类
- concepts: 接口, 抽象类, default/static 方法, 多实现, 单继承
- evidence_summary: 接口偏能力规范(can-do)、抽象类偏公共模板(is-a)；接口多实现、抽象类单继承；抽象类可有成员变量/构造器；接口 Java 8+ 有 default/static。

## Section: 7. 异常体系
- concepts: Throwable, Error, Exception, checked, unchecked, throw, throws
- evidence_summary: Throwable→Error(系统级如 OOM)+Exception(程序级)；checked 编译期强制(IOException)、unchecked 运行期(RuntimeException/NPE)；throw 主动抛、throws 声明；Error 一般不靠业务恢复。

## Section: 8. hashCode() 和 equals()
- concepts: hashCode, equals, 哈希冲突, HashSet 去重, HashMap key
- evidence_summary: equals 相等→hashCode 必须相等；hashCode 相等→equals 不一定相等（冲突）；只重写 equals 不重写 hashCode → HashSet 去重失效、HashMap key 查找异常。

## Section: 9. Java 参数传递
- concepts: 值传递, 引用副本, 对象属性修改
- evidence_summary: Java 只有值传递；传对象传引用副本，能改对象内部属性，但不能让外部引用指向新对象。

## Section: 10. 深拷贝 vs 浅拷贝
- concepts: 浅拷贝, 深拷贝, Object.clone, 序列化
- evidence_summary: 浅拷贝只复制对象本身、内部引用共用；深拷贝内部引用也独立；`Object.clone()` 默认浅拷贝；深拷贝实现：手动复制/拷贝构造器/序列化。

## Section: 11. 泛型
- concepts: 泛型, 类型擦除, 引用类型
- evidence_summary: 泛型把类型参数化，编译期类型检查+减少强转；运行期类型擦除；泛型只接收引用类型（`List<int>` 不行）。

## Section: 12. 反射
- concepts: 反射, 运行时动态, Spring DI/AOP 底层
- evidence_summary: 反射=运行时动态获取类信息并操作；Spring 的 DI、AOP、注解处理底层用反射；优点灵活，缺点性能差、破坏封装。

## Section: NPE（NullPointerException）
- concepts: NPE, 判空, Optional, 实习实例 ECP
- evidence_summary: NPE 是最常见 unchecked 异常，对 null 引用调方法触发；给出 ECP 回单 `task.getId()` 实例与修复（判空 + 日志）；防御姿势：先判空、Optional 包裹、日志记对象名。

## Section: 高频对比速记
- concepts: 全章对比汇总（==/equals、重载/重写、StringBuilder/StringBuffer、final/finally/finalize、接口/抽象类、checked/unchecked、throw/throws、深/浅拷贝）
- evidence_summary: 表格汇总本文件全部核心对比，是"区别型问题"的集中证据区。
