## 总说明
- 源码仓库： https://github.com/dromara/hutool
- 克隆：`git clone https://github.com/dromara/hutool.git`
- 切分支（tag）：`git checkout 5.8.17`
- JDK: **要 JDK-1.8**，JDK-17 会报错


---
## 借鉴点或亮点
### AOP 亮点
- 支持 JDK、CGLib、SPRING-CGLib

### BloomFilter 实现
- 将多个 Hash 过滤器（函数）组合起来使用

### BOM 亮点
- 支持按需引入依赖
- https://hutool.cn/docs/#/bom/概述

### Cache 借鉴点
- 入口：`cn.hutool.cache.CacheTest #fifoCacheTest`
- 参考：`cn.hutool.cache.impl.StampedCache #put || #get`
  - **使用乐观锁 `StampedLock` 解决读多写少的场景**，非常适合缓存使用
  - 使用**惰性删除**清空过期缓存

### Captcha 亮点
- 支持 GIF 验证码

### Core
#### lang 亮点
- **表格格式输出**，使用：`cn.hutool.core.lang.ConsoleTable`
  - 参考：`cn.hutool.Hutool #printAllUtils`
- **雪花算法**，使用：`cn.hutool.core.lang.generator.SnowflakeGenerator`
  - 支持序号随机，防止低频时，ID 始终为偶数
    - 参考：`cn.hutool.core.lang.Snowflake #randomSequenceLimit`
  - 系统时钟优化`System.currentTimeMillis()`高并发性能问题
    - 参考：`cn.hutool.core.date.SystemClock`

#### 集合亮点
- List 分割：`cn.hutool.core.collection.ListUtil #partition`

#### io 亮点
- `cn.hutool.core.io.FastByteBuffer` 使用 2 维数组，避免多次复制

#### thread 亮点
- 高并发测试工具类 `cn.hutool.core.thread.ConcurrencyTester`
  - 使用`CountDownLatch`让所有线程在同一时刻才执行，但测 CPU 型任务没意义
  - 参考：`cn.hutool.core.thread.SyncFinisher #start`

#### util 亮点
- 坐标系转换工具类 `cn.hutool.core.util.CoordinateUtil`
- 脱敏工具类 `cn.hutool.core.util.DesensitizedUtil`
- 身份证工具类 `cn.hutool.core.util.IdcardUtil`

### Setting 亮点
- 支持 setting、yaml、properties **文件读取与对象转换**

### cron 亮点
- 支持获取要执行的时间点，使用 `cn.hutool.cron.pattern.CronPatternUtil #matchedDates`

### dfa 亮点
- 支持**敏感词过滤**，能防止特殊字符插中间干扰
  - 如：`我有一颗$大土^豆`，敏感字：`大土豆`，过滤后为：`我有一颗$****`


---
## ServiceLoaderUtil-原理
### 简介
- 主要是通过 Java SPI 去获取服务提供者
  - 所以后面**主要是介绍 Java SPI 原理**

### 测试
- 在 `cn.hutool.aop.proxy.ProxyFactory` 加个 `main` 方法
```java
    /*** 获取实现类 */
    public static ProxyFactory create() {
        return ServiceLoaderUtil.loadFirstAvailable(ProxyFactory.class);
    }

    // 测试
    public static void main(String[] args) {
        ProxyFactory factory = create();
        System.out.println(factory);
    }
```

### 源码说明
- `cn.hutool.core.util.ServiceLoaderUtil`
```java
    /*** 加载第一个可用服务 */
    public static <T> T loadFirstAvailable(Class<T> clazz) {
        final Iterator<T> iterator = load(clazz).iterator(); // 获取 ServiceLoader 的迭代器
        while (iterator.hasNext()) {
            try {
                return iterator.next(); // 出错时忽略，继续查找下一个
            } catch (ServiceConfigurationError ignore) {
                // ignore
            }
        }
        return null;
    }

    /*** 加载服务 */
    public static <T> ServiceLoader<T> load(Class<T> clazz) {
        return load(clazz, null);
    }

    /*** 加载服务 */
    public static <T> ServiceLoader<T> load(Class<T> clazz, ClassLoader loader) {
        // 使用 Java SPI。
        return ServiceLoader.load(clazz, ObjectUtil.defaultIfNull(loader, ClassLoaderUtil::getClassLoader));
    }
```

- Java SPI 参考：[JDK-SPI](../JDK/SPI.md)


#### SPI 文件示例
- `hutool-aop/src/main/resources/ META-INF/services/ cn.hutool.aop.proxy.ProxyFactory`
```js
// 文件名（即接口类的全名）：cn.hutool.aop.proxy.ProxyFactory
cn.hutool.aop.proxy.CglibProxyFactory
cn.hutool.aop.proxy.SpringCglibProxyFactory
cn.hutool.aop.proxy.JdkProxyFactory
```