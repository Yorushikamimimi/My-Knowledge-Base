# Gold V1.1

```text
Status: FROZEN
Parent: Gold V1
Change reason: q-001 source omission discovered during production-faithful benchmark audit
Semantic changes: 1
```

## 变更内容

Gold V1.1 相比 V1 仅有一个 semantic change：

**q-001** `expected_sources` 增加两个已经审计确认可以独立回答该问题的 section（均来自 D06 全流程后端微服务资料）：

```text
Vault/Personal_Archive/10-Knowledge/backend/速查/全流程后端微服务资料.md
  - section: "3. AOP"                    （AOP 失效场景：同类内部方法调用时 this 非代理对象）
  - section: "5. 声明式事务 @Transactional"（易错点：同类内部调用无效 / AOP 失效）

同时保留原 D05 §9 "9. @Transactional"。
```

最终 q-001 为 **三个合法 evidence source**，`source_match` 继续为 `any`。

## 为什么不是 compound question

D06 §3 与 §5 均具有**独立 evidence**：

- D06 §3 AOP：原文「AOP失效场景：同类内部方法调用时，this非代理对象，AOP不生效」「不要在同一个类里调用本类的@Transactional或@Async方法，代理会失效」——单独足以回答"同类内部调用事务为什么不生效"。
- D06 §5 声明式事务：原文「易错点 2：同类内部调用无效（AOP失效）」——单独足以回答。

因此任一 source 单独命中即 Retrieval Hit，不要求联合多文档，`source_match=any` 语义保持，非 compound。

## 不变项

- q-002 ~ q-030：case 数据与 Gold V1 完全一致（canonical comparison 验证，其余 29 个 case 逐字节相同）。
- Gold V1（`gold-v1.json`）保持完全不可变，作为历史版本保留。
- 版本约定不变：未来任何影响评测语义的修改必须 version bump。

## 验证

```text
semantic diffs: 1（仅 q-001 expected_sources）
q-001 sources: 1 → 3
其余 29 cases: 逐 case canonical 相同
```

## 文件

- 正式数据：`docs/phase2/gold-v1.1.json`
- 元数据：本文件
- 父版本：`docs/phase2/gold-v1.json` / `docs/phase2/gold-v1.md`
