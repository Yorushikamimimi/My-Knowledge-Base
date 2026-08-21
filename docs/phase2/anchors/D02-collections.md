# Anchors: D02 — 集合 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/集合 八股文.md`
- domain: Java
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. List / Set / Map
- concepts: List, Set, Map, ArrayList, LinkedList, HashSet, TreeMap, Collection 体系
- evidence_summary: List 有序可重复、Set 无重复、Map 键值对；Map 与 Collection 是两套体系。

## Section: 2. ArrayList vs LinkedList
- concepts: 动态数组, 双向链表, 随机访问 O(1), 扩容 1.5 倍
- evidence_summary: ArrayList 动态数组随机访问 O(1)、中间插入需移动；LinkedList 双向链表增删方便、查询 O(n)；ArrayList 扩容 1.5 倍（新建数组+拷贝）；多数场景优先 ArrayList。

## Section: 3. HashMap
- concepts: 数组+链表+红黑树, put 流程, 1.7 头插 vs 1.8 尾插, 树化条件, 负载因子, 线程不安全
- evidence_summary: 底层数组+链表+红黑树；put=算 hash→找桶→空放/非空比较→覆盖或挂链/树→超负载扩容；1.7 头插、1.8 尾插+红黑树；树化需链表≥8 且容量≥64，容量<64 优先扩容；无同步控制并发不安全。

## Section: 4. ConcurrentHashMap
- concepts: ConcurrentHashMap, CAS+synchronized, 1.7 Segment, 1.8 细粒度锁, synchronizedMap 对比
- evidence_summary: CHM 是线程安全 HashMap；1.7 Segment 分段锁、1.8 CAS+synchronized 数组+链表+红黑树；锁粒度比 Hashtable/synchronizedMap 细，并发性能更好。

## Section: 5. HashSet
- concepts: HashSet, 底层 HashMap, equals/hashCode 去重
- evidence_summary: HashSet 底层基于 HashMap，元素存 key、value 固定占位对象；自定义对象去重失败→没正确重写 equals/hashCode。

## Section: 6. fail-fast
- concepts: fail-fast, ConcurrentModificationException, modCount, Iterator.remove
- evidence_summary: 遍历时检测结构被修改→抛 CME，通过 modCount 检测；安全删除用 Iterator.remove()，不要在 for-each 里 list.remove()。

## Section: 7. 其他集合
- concepts: CopyOnWriteArrayList, LinkedHashMap LRU, TreeMap 红黑树
- evidence_summary: COW 写时复制读不加锁适合读多写少；LinkedHashMap 保持插入/访问顺序可做 LRU；TreeMap 红黑树按 key 排序。

## Section: 8. 选型速查
- concepts: 选型表（HashMap/CHM/LinkedHashMap/TreeMap/ArrayList/COW/HashSet）
- evidence_summary: 按需求选型：普通 KV=HashMap、并发 KV=CHM、顺序=LinkedHashMap、排序=TreeMap、列表=ArrayList、并发读多写少=COW、去重=HashSet。

## Section: 高频对比速记
- concepts: 对比汇总（ArrayList/LinkedList、HashMap/CHM、HashMap/LinkedHashMap/TreeMap、synchronizedMap/CHM、1.7/1.8）
- evidence_summary: 表格汇总本文件核心对比，是"区别型问题"集中证据区；其中 HashMap vs CHM、synchronizedMap vs CHM 与 D03 并发域重叠。
