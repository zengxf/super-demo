## SPI 源码说明
- `java.util.ServiceLoader`
```java
/*** 服务加载器：给定接口，查找实现类。实现可迭代接口 */
public final class ServiceLoader<S> implements Iterable<S> {

    /*** 返回 ServiceLoader 实例 */
    public static <S> ServiceLoader<S> load(Class<S> service, ClassLoader loader) {
        return new ServiceLoader<>(service, loader);
    }

    /*** 构造器 */
    private ServiceLoader(Class<S> svc, ClassLoader cl) {
        // 记录要查找的接口类
        service = Objects.requireNonNull(svc, "Service interface cannot be null");
        // 记录加载器
        loader = (cl == null) ? ClassLoader.getSystemClassLoader() : cl;
        ...
        reload(); // (重新)加载
    }

    /*** 重新加载 */
    public void reload() {
        providers.clear(); // 清空
        lookupIterator = new LazyIterator(service, loader); // 创建懒加载迭代器
    }

    /*** 实现可迭代接口：返回迭代器 */
    @Override
    public Iterator<S> iterator() {
        /*** 一个新的迭代器实现。对懒加载迭代器 lookupIterator 进行封装 */
        return new Iterator<S>() {
            Iterator<Map.Entry<String, S>> knownProviders = providers.entrySet().iterator();
            ...
            public S next() { // 先从已加载的里面选
                if (knownProviders.hasNext())
                    return knownProviders.next().getValue();
                return lookupIterator.next(); // 最后才开始加载
            }
            ...
        };
    }

}
```

- `java.util.ServiceLoader.LazyIterator`
```java
    /*** 懒加载-迭代器。实现迭代器接口 */
    private class LazyIterator implements Iterator<S> {

        /*** 构造器 */
        private LazyIterator(Class<S> service, ClassLoader loader) {
            this.service = service;
            this.loader = loader;
        }

        /*** 获取下一个服务实现对象 */
        public S next() {
            if (acc == null) {
                return nextService(); // 获取下一个服务实现对象
            } 
            ...
        }

        /*** 获取下一个服务实现对象 */
        private S nextService() {
            ...
            String cn = nextName; // 下一个服务实现类的类名。nextName 在 hasNextService() 方法里面设置
            Class<?> c = null;
            try {
                c = Class.forName(cn, false, loader); // 初始化类
            } catch (ClassNotFoundException x) {
                ...
            }
            ...
            try {
                S p = service.cast(c.newInstance()); // 实例化一个对象
                providers.put(cn, p); // 添加到提供者（providers）Map 里，方便上面的判断
                return p;
            }
            ...
        }

        /*** 判断是否有下一个服务 */
        private boolean hasNextService() {
            ...
            if (configs == null) {
                try {
                    // String PREFIX = "META-INF/services/";
                    String fullName = PREFIX + service.getName();
                    ...
                    configs = loader.getResources(fullName); // 加载所有的文件
                } 
                ...
            }
            while ((pending == null) || !pending.hasNext()) {
                if (!configs.hasMoreElements()) {
                    return false;
                }
                pending = parse(service, configs.nextElement()); // 逐个文件加载填充 pending
            }
            nextName = pending.next(); // 设置下一个要加载的类的类名
            return true;
        }
    }
```