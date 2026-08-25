"""生成面试题。

根据检测出的语言与框架，从知识库中选取相关面试题；此外总会附带一组
与仓库本身相关的“项目题”，帮助候选人理解真实代码。
"""

from __future__ import annotations

from .github import RepoData
from .techstack import TechStack

# 通用项目题模板（结合仓库信息渲染）
_PROJECT_QUESTIONS = [
    "请描述这个仓库的整体架构，以及各模块之间的依赖关系。",
    "如果要给这个项目新增一个功能，你会从哪些文件开始改动？为什么？",
    "如何在本机运行、构建和测试这个项目？",
    "这个项目中有哪些设计模式或架构思想值得借鉴？",
    "你觉得这个项目在哪些地方可能存在性能瓶颈或安全隐患？",
    "如果让你重构这个项目，你会优先改进哪些地方？",
]

# 按语言/技术组织的面试题知识库
LANGUAGE_QUESTIONS = {
    "Python": [
        "解释 Python 中列表和元组的区别，分别在什么场景使用？",
        "什么是 GIL？它对多线程编程有什么影响？",
        "装饰器是什么？举例说明它的应用场景。",
        "生成器与迭代器的区别是什么？什么时候用生成器更合适？",
        "Python 中 `is` 和 `==` 有什么区别？",
        "如何理解可变对象与不可变对象？默认参数有哪些坑？",
    ],
    "JavaScript": [
        "解释 JavaScript 中的闭包，并举例说明其用途。",
        "`var`、`let`、`const` 的区别是什么？",
        "什么是事件循环（Event Loop）？宏任务与微任务如何调度？",
        "原型链是什么？`prototype` 和 `__proto__` 有何区别？",
        "如何理解 `this` 的绑定规则？箭头函数中的 `this` 有什么特点？",
        "解释浅拷贝与深拷贝的区别，并说明实现方式。",
    ],
    "TypeScript": [
        "TypeScript 中 `interface` 和 `type` 的区别是什么？",
        "什么是泛型？它解决了什么问题？",
        "`any`、`unknown`、`never` 之间有什么区别？",
        "如何理解 TypeScript 的类型收窄（Type Narrowing）？",
    ],
    "Go": [
        "Go 中 goroutine 与线程的区别是什么？",
        "channel 是如何实现 goroutine 之间通信的？有缓冲和无缓冲有何区别？",
        "Go 的接口是如何设计的？如何理解“隐式实现”？",
        "`defer` 的执行顺序是怎样的？常见使用场景有哪些？",
        "Go 的内存模型与垃圾回收有什么特点？",
    ],
    "Rust": [
        "什么是所有权（Ownership）？它与借用、生命周期是什么关系？",
        "Rust 中 `String` 和 `&str` 有什么区别？",
        "什么是 trait？它和接口有什么区别？",
        "如何理解 Rust 的智能指针（如 `Box`、`Rc`、`Arc`）？",
        "Rust 如何在没有垃圾回收的情况下保证内存安全？",
    ],
    "Java": [
        "Java 中 `==` 和 `equals()` 的区别是什么？",
        "HashMap 的底层实现原理是什么？JDK 8 做了哪些优化？",
        "什么是 JVM？它的内存区域是如何划分的？",
        "谈谈你对 Java 并发编程中 `synchronized` 和 `ReentrantLock` 的理解。",
        "接口与抽象类的区别是什么？",
    ],
    "C++": [
        "指针和引用的区别是什么？",
        "什么是 RAII？它如何帮助管理资源？",
        "移动语义（move semantics）解决了什么问题？",
        "虚函数与纯虚函数的区别？多态是如何实现的？",
        "谈谈 `std::shared_ptr` 与 `std::unique_ptr` 的区别。",
    ],
    "C#": [
        "值类型和引用类型的区别是什么？",
        "什么是委托（delegate）和事件（event）？",
        "`async` / `await` 的工作原理是什么？",
        "LINQ 是什么？它有哪些常用操作？",
    ],
    "Ruby": [
        "Ruby 中符号（Symbol）和字符串（String）的区别是什么？",
        "什么是模块（Module）？它和类（Class）有什么区别？",
        "Ruby 中的块（block）、Proc 和 lambda 有何区别？",
    ],
    "PHP": [
        "PHP 中 `==` 和 `===` 的区别是什么？",
        "解释 PHP 的自动加载机制（autoload）。",
        "PHP 的数组底层是如何实现的？",
    ],
    "Kotlin": [
        "Kotlin 中 `val` 和 `var` 的区别是什么？",
        "什么是扩展函数？它如何实现？",
        "协程（Coroutine）与线程有什么区别？",
    ],
    "Swift": [
        "Swift 中值类型和引用类型的区别是什么？",
        "什么是可选类型（Optional）？如何安全解包？",
        "解释 ARC（自动引用计数）的工作原理。",
    ],
    "Scala": [
        "Scala 中 `val`、`var`、`def` 的区别是什么？",
        "什么是 case class？它与普通类的区别？",
        "谈谈 Scala 中隐式转换（implicit）的作用。",
    ],
}

FRAMEWORK_QUESTIONS = {
    "Django": [
        "Django 的 MTV 架构是什么？各层职责是什么？",
        "Django 的 ORM 是如何工作的？如何优化查询？",
        "什么是中间件（Middleware）？举一个应用场景。",
        "Django 如何处理请求-响应生命周期？",
    ],
    "Flask": [
        "Flask 的应用上下文和请求上下文分别是什么？",
        "Flask 如何实现路由？蓝本（Blueprint）有什么作用？",
        "Flask 的请求钩子（before_request、after_request）如何使用？",
    ],
    "FastAPI": [
        "FastAPI 相比 Flask/Django 有哪些优势？",
        "FastAPI 如何利用 Pydantic 做请求校验？",
        "FastAPI 的依赖注入（Depends）是如何工作的？",
    ],
    "React": [
        "React 中函数组件和类组件有什么区别？",
        "什么是虚拟 DOM？它如何提升性能？",
        "React 的 Hooks 有哪些？`useEffect` 的依赖数组如何工作？",
        "受控组件和非受控组件的区别是什么？",
        "React 中状态提升（lifting state up）是什么意思？",
    ],
    "Vue.js": [
        "Vue 的响应式原理是什么？（Vue 2 与 Vue 3 有何区别）",
        "`computed` 和 `watch` 的区别是什么？",
        "Vue 组件之间如何通信？",
        "什么是 Vue 的插槽（slot）？",
    ],
    "Angular": [
        "Angular 的依赖注入是如何工作的？",
        "什么是 Angular 模块（NgModule）？",
        "Angular 中组件生命周期钩子有哪些？",
    ],
    "Next.js": [
        "Next.js 的 SSR、SSG、ISR 分别是什么？",
        "Next.js 中 `getServerSideProps` 和 `getStaticProps` 的区别？",
        "什么是 App Router？它和 Pages Router 有何不同？",
    ],
    "Express": [
        "Express 中间件的执行顺序是怎样的？",
        "如何设计 Express 应用的错误处理？",
        "Express 中 `app.use` 和 `app.get` 有什么区别？",
    ],
    "NestJS": [
        "NestJS 的模块、控制器、服务分别是什么？",
        "NestJS 的依赖注入是如何实现的？",
        "什么是装饰器？NestJS 如何使用装饰器？",
    ],
    "Spring": [
        "什么是 IoC 和 AOP？它们在 Spring 中如何体现？",
        "Spring Bean 的生命周期是怎样的？",
        "`@Autowired`、`@Resource`、`@Inject` 有什么区别？",
    ],
    "Spring Boot": [
        "Spring Boot 的自动配置原理是什么？",
        "`@SpringBootApplication` 注解包含哪些内容？",
        "如何理解 Spring Boot 的 starter 机制？",
    ],
    "Ruby on Rails": [
        "Rails 的 MVC 架构是什么？",
        "Rails 的 ActiveRecord 如何做数据库迁移？",
        "什么是 Rails 的约定优于配置（Convention over Configuration）？",
    ],
    "Laravel": [
        "Laravel 的服务容器和依赖注入是如何工作的？",
        "什么是 Eloquent ORM？它有哪些优势？",
        "Laravel 的中间件如何使用？",
    ],
    "pandas": [
        "如何用 pandas 进行数据清洗？常用方法有哪些？",
        "`apply`、`map`、`applymap` 有什么区别？",
        "如何合并 DataFrame？`merge` 和 `concat` 有何不同？",
    ],
    "NumPy": [
        "NumPy 数组和 Python 列表有什么区别？",
        "什么是广播（Broadcasting）？举例说明。",
        "NumPy 的向量化运算为什么比循环快？",
    ],
    "PyTorch": [
        "PyTorch 的动态计算图和静态计算图有什么区别？",
        "什么是张量（Tensor）？它和 NumPy 数组有何关系？",
        "如何理解 PyTorch 的自动求导（autograd）机制？",
    ],
    "TensorFlow": [
        "TensorFlow 2.x 相比 1.x 有哪些改进？",
        "什么是张量（Tensor）和图（Graph）？",
        "TensorFlow 的 eager execution 是什么？",
    ],
    "scikit-learn": [
        "如何用 scikit-learn 做模型训练和评估？",
        "什么是交叉验证（Cross Validation）？",
        "谈谈你对过拟合和欠拟合的理解，以及应对方法。",
    ],
    "Redis": [
        "Redis 有哪些数据类型？各自适用场景是什么？",
        "Redis 的持久化机制（RDB、AOF）有什么区别？",
        "缓存穿透、缓存击穿、缓存雪崩分别指什么？如何解决？",
    ],
    "MongoDB": [
        "MongoDB 和关系型数据库的区别是什么？",
        "什么是 MongoDB 的分片（Sharding）和副本集？",
        "MongoDB 的索引是如何工作的？",
    ],
    "PostgreSQL": [
        "PostgreSQL 的 MVCC 是如何实现的？",
        "什么是索引？B-Tree 和 GIN 索引有什么区别？",
        "如何优化一条慢查询？谈谈你的思路。",
    ],
    "Docker": [
        "镜像和容器的区别是什么？",
        "Dockerfile 中 `CMD` 和 `ENTRYPOINT` 有什么区别？",
        "什么是 Docker 的多阶段构建（multi-stage build）？",
    ],
    "Kubernetes": [
        "Pod、Service、Deployment 分别是什么？",
        "Kubernetes 如何做服务发现和负载均衡？",
        "什么是 ConfigMap 和 Secret？它们的区别？",
    ],
}

# 数据存储相关的通用题
DATABASE_QUESTIONS = {
    "SQLite": [
        "SQLite 和常见客户端-服务器数据库（如 PostgreSQL）的区别是什么？",
        "SQLite 适合哪些场景？有哪些局限？",
    ],
    "MySQL": [
        "MySQL 的 InnoDB 和 MyISAM 存储引擎有什么区别？",
        "MySQL 的事务隔离级别有哪些？",
    ],
}


def generate_questions(data: RepoData, stack: TechStack) -> list[tuple[str, str]]:
    """返回面试题列表，每项为 (分类, 题目)。"""
    questions: list[tuple[str, str]] = []

    # 1. 项目题（必出，结合仓库名）
    for q in _PROJECT_QUESTIONS:
        questions.append(("项目理解", q))

    # 2. 语言题
    for lang, _ in stack.languages[:3]:
        if lang in LANGUAGE_QUESTIONS:
            for q in LANGUAGE_QUESTIONS[lang]:
                questions.append((lang, q))

    # 3. 框架题
    for fw in stack.frameworks:
        if fw in FRAMEWORK_QUESTIONS:
            for q in FRAMEWORK_QUESTIONS[fw]:
                questions.append((fw, q))

    # 4. 数据库题
    for db in stack.databases:
        if db in DATABASE_QUESTIONS:
            for q in DATABASE_QUESTIONS[db]:
                questions.append((db, q))

    # 去重（保留顺序）
    seen: set[str] = set()
    result: list[tuple[str, str]] = []
    for category, question in questions:
        if question not in seen:
            seen.add(question)
            result.append((category, question))

    return result
