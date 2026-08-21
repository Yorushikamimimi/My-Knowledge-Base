# Anchors: D06 — 全流程后端微服务资料.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/速查/全流程后端微服务资料.md`
- domain: Spring（1-7 节）/ 微服务（8-12 节）
- 用户确认：接受混合文档纳入；锚点按节标注域归属；与 D05 构成 Cluster A。
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. Servlet to Spring MVC
- concepts: Front Controller, DispatcherServlet, @RestController, Tomcat, Web 层职责
- evidence_summary: DispatcherServlet 统一处理 HTTP 请求，Controller 只写业务逻辑；原生 Servlet 需自处理协议细节；Web 层职责参数校验/协议转换/响应包装，禁止写业务逻辑；易错点：Service 层不要引入 HttpServletRequest。

## Section: 2. IoC & DI
- concepts: IoC, DI, 构造器注入, @RequiredArgsConstructor, 字段注入禁止, 循环依赖
- evidence_summary: 对象由框架创建管理，构造器注入依赖；推荐 @RequiredArgsConstructor；禁止字段注入（无法单测）；循环依赖导致启动失败（Spring Boot 2.6+ 默认禁止）。与 D05 Section 2 交叉。

## Section: 3. AOP
- concepts: AOP, JDK 动态代理, CGLIB, @Aspect, @Around, @Transactional, @Cacheable, @Async, AOP 失效
- evidence_summary: 通过动态代理插入横切逻辑；核心注解 @Aspect/@Around/@Before/@After；典型应用 @Transactional/@Cacheable/@Async；失效场景：同类内部调用 this 非代理对象；易错点：同 class 内调 @Transactional/@Async 代理失效。与 D05 Section 3/9 交叉（Cluster A）。

## Section: 4. ThreadLocal
- concepts: ThreadLocal, SecurityContextHolder, 参数透传, remove, 线程池复用串号
- evidence_summary: 线程独享变量避免参数透传；典型应用 Spring Security SecurityContextHolder 存用户上下文；必须请求结束 remove()，否则线程池复用数据泄露；面试答法：Tomcat 线程池复用不清理会串号。与 D03 Section 11 交叉。

## Section: 5. 声明式事务 @Transactional
- concepts: @Transactional, rollbackFor, RuntimeException/checked, try-catch 陷阱, setRollbackOnly, ThreadLocal 绑定 Connection, AOP 失效
- evidence_summary: 通过 AOP 代理捕获异常自动回滚；推荐 rollbackFor=Exception.class；默认只回滚 RuntimeException/Error；try-catch 吞异常不回滚，需 throw RuntimeException 或 setRollbackOnly()；底层依赖 ThreadLocal 绑定同一 Connection；同类内部调用无效。与 D05 Section 9 高度重叠（Cluster A 核心）。

## Section: 6. 消息队列 MQ
- concepts: MQ, 异步解耦, 削峰填谷, 幂等, 手动 ACK, 死信队列 DLQ, At-least-once
- evidence_summary: MQ 异步解耦 fire-and-forget 削峰填谷；场景发邮件/PDF/延迟任务；组件 Producer/Consumer/Queue；幂等 At-least-once 需防重（唯一索引/Redis Token）；手动 ACK 业务成功后再确认；DLQ 处理永远失败消息；代价是最终一致性。

## Section: 7. Redis缓存
- concepts: Cache Aside, 缓存击穿, 缓存穿透, 缓存雪崩, TTL 随机抖动, Spring Cache, @Cacheable, @CacheEvict
- evidence_summary: Cache Aside 读先查缓存未命中查 DB 写回；三大问题表（击穿=热点 Key 过期并发打穿→分布式锁；穿透=恶意不存在 Key→布隆/空值短 TTL；雪崩=大量 Key 同时过期→TTL 随机抖动）；更新策略先更新 DB 再删缓存；实际用 Spring Cache(@Cacheable/@CacheEvict)。与 D08/D09 Redis 域交叉（Cluster B 弱关联）。

## Section: 8. 服务发现与RPC
- concepts: Nacos, Eureka, Feign, 注册中心, 心跳, 熔断器, Fallback, 超时配置
- evidence_summary: 服务启动向注册中心注册 IP 端口心跳保活；@FeignClient 声明式远程调用（负载均衡/序列化）；必须配置 connectTimeout/readTimeout；熔断器连续失败 N 次熔断执行 Fallback；面试答法：Nacos 解决"你在哪"、Feign 解决"怎么调"、熔断防雪崩。

## Section: 9. API Gateway
- concepts: Gateway, 统一鉴权, 动态路由, 限流, Netty, Reactive, 非阻塞, 禁止 Blocking I/O
- evidence_summary: 网关统一入口承担鉴权/路由/限流；前端只访问一个域名、网关路由内网服务；核心功能统一鉴权(JWT)/动态路由(/order/**→order-service)/限流；底层 Netty+Reactive 非阻塞 NIO Event Loop；禁止在 Gateway Filter 用同步 JDBC/Thread.sleep；含 yaml 配置示例。

## Section: 10. 分布式事务
- concepts: Seata AT, @GlobalTransactional, TC, Undo Log, 强一致性, MQ 最终一致性, 全局锁
- evidence_summary: 跨库一致性：强一致 Seata（@GlobalTransactional + TC 协调 + Undo Log 补偿，代价全局锁性能差）、最终一致 MQ（本地事务后发消息、消费失败重试/补偿，时间换空间）；面试答法：核心资金用 Seata、高并发用 MQ。

## Section: 11. Docker容器化
- concepts: Docker, 镜像分层, Volume 挂载, docker-compose, K8s
- evidence_summary: 镜像打包应用+依赖+环境；分层=基础镜像+依赖+业务代码；Volume 挂载持久化（MySQL 数据目录必须挂）；docker-compose 编排多服务；K8s 自动扩缩容自愈；易错：容器不挂 Volume 删了就丢数据；含 Dockerfile 示例。

## Section: 12. CI/CD
- concepts: CI/CD, GitHub Actions, 蓝绿发布, 灰度发布, 自动化测试, Repository Secrets
- evidence_summary: 代码提交后自动测试打包部署；GitHub Actions 流程示例（checkout→setup-java→mvn package→ssh deploy）；蓝绿发布=Blue 老+Green 新、测试通过切流量秒级回滚；灰度=逐步放量；必须有自动化测试；禁止硬编码密码用 Secrets。

## Section: 架构全景图
- concepts: 全景架构, 单一职责, 面向接口, 异步解耦, 防御性编程, 基础设施即代码
- evidence_summary: 全景图：用户→Gateway→服务(注册中心/Feign)→Redis+MySQL+MQ→Docker+CI/CD；核心哲学五条（单一职责/面向接口/异步解耦/防御性编程熔断降级限流/基础设施即代码）。
