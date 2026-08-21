# Anchors: D05 — Spring ， Spring Boot 八股文.md

- document: `Vault/Personal_Archive/10-Knowledge/backend/八股/Spring ， Spring Boot 八股文.md`
- domain: Spring
- 锚点层规则：document + section + concepts + evidence_summary；不绑定 chunk_index；跨文档问题允许多个 expected sections。

## Section: 1. Spring 是什么
- concepts: 轻量级框架, IoC, AOP, 事务, MVC, 解耦
- evidence_summary: Spring 是轻量级 Java 框架，核心价值管理对象/依赖/降低耦合，提供 IoC、AOP、事务、MVC 能力。

## Section: 2. IoC / DI
- concepts: IoC, DI, 容器, 控制反转, 依赖注入
- evidence_summary: IoC=对象创建管理权交给 Spring 容器；DI 是 IoC 具体实现，容器自动注入依赖；"IoC 是思想，DI 是实现"。与 D06 Section 2 交叉。

## Section: 3. AOP
- concepts: AOP, 横切逻辑, JDK 动态代理, CGLIB, final 类
- evidence_summary: AOP 把日志/事务/权限横切逻辑抽离；底层动态代理：有接口 JDK 代理、无接口 CGLIB（生成子类）；final 类不能被 CGLIB 代理。与 D06 Section 3 交叉。

## Section: 4. Bean 生命周期
- concepts: Bean 生命周期, 实例化, 依赖注入, @PostConstruct, @PreDestroy
- evidence_summary: Bean 生命周期：实例化→依赖注入→初始化(@PostConstruct)→使用→销毁(@PreDestroy)；附交互演示链接。

## Section: 5. 常用注解
- concepts: @Component, @Service, @Repository, @RestController, @Autowired, 构造器注入
- evidence_summary: @Component 通用组件；@Service/@Repository 语义分层；@RestController=@Controller+@ResponseBody；@Autowired 注入（推荐构造器注入）。

## Section: 6. Spring MVC 执行流程
- concepts: DispatcherServlet, HandlerMapping, HandlerAdapter, 前端控制器
- evidence_summary: MVC 流程：请求→DispatcherServlet（前端控制器）→HandlerMapping 找 Controller→HandlerAdapter 执行→返回响应；核心是 DispatcherServlet 统一接收分发返回。

## Section: 7. @SpringBootApplication
- concepts: @SpringBootApplication, @SpringBootConfiguration, @EnableAutoConfiguration, @ComponentScan
- evidence_summary: 组合注解 = @SpringBootConfiguration + @EnableAutoConfiguration + @ComponentScan（配置类+自动配置+组件扫描）。

## Section: 8. Spring Boot 自动配置
- concepts: 自动配置, @Conditional, 约定大于配置, @EnableAutoConfiguration
- evidence_summary: 根据依赖和环境按 @Conditional 条件自动装配 Bean，约定大于配置；入口 @EnableAutoConfiguration；不是无脑全配而是按条件装配。

## Section: 9. @Transactional
- concepts: @Transactional, AOP 代理, 默认回滚规则, RuntimeException, checked, rollbackFor, 事务失效场景, 传播行为 REQUIRED/REQUIRES_NEW
- evidence_summary: 声明式事务本质 AOP 代理；默认：RuntimeException/Error 回滚、checked 不回滚需显式 rollbackFor；五大失效场景：同类内部调用（this 绕过代理）、catch 吞异常、非 public、抛受检异常、非 Spring Bean；传播：REQUIRED（默认，有则加入无则新建）、REQUIRES_NEW（强制新开）。与 D06 Section 5 高度重叠，Cluster A 核心。

## Section: 10. JDK 动态代理 vs CGLIB
- concepts: JDK 动态代理, CGLIB, 接口, 继承, final 限制
- evidence_summary: JDK 代理基于接口、目标类须实现接口；CGLIB 基于继承生成子类、无需接口；final 类/方法不能 CGLIB 代理。

## Section: 11. BeanFactory vs ApplicationContext
- concepts: BeanFactory, ApplicationContext, 国际化, 事件, 资源加载
- evidence_summary: BeanFactory 最基础容器；ApplicationContext 增强版支持国际化/事件/资源加载；实际开发用 ApplicationContext。

## Section: 12. Spring vs Spring Boot
- concepts: Spring, Spring Boot, 自动配置, Starter, 内嵌服务器
- evidence_summary: Spring 提供核心能力（IoC/AOP/事务/MVC）；Spring Boot 通过自动配置+Starter+内嵌服务器简化配置快速开发；Starter=场景化依赖套餐。

## Section: 高频对比速记
- concepts: 对比汇总（IoC/DI、JDK/CGLIB、BeanFactory/ApplicationContext、Spring/Boot、REQUIRED/REQUIRES_NEW）
- evidence_summary: 表格汇总本文件核心对比；REQUIRED vs REQUIRES_NEW、代理失效与 D06 构成 Cluster A 证据区。
