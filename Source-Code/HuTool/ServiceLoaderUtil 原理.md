## 简介
- 主要是通过 Java SPI 去获取服务提供者
  - 所以后面**主要是介绍 Java SPI 原理**

## 测试
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

## 源码说明
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


### SPI 文件示例
- `hutool-aop/src/main/resources/ META-INF/services/ cn.hutool.aop.proxy.ProxyFactory`
```js
// 文件名（即接口类的全名）：cn.hutool.aop.proxy.ProxyFactory
cn.hutool.aop.proxy.CglibProxyFactory
cn.hutool.aop.proxy.SpringCglibProxyFactory
cn.hutool.aop.proxy.JdkProxyFactory
```