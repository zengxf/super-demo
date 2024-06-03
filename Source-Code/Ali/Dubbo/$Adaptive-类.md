# Dubbo-$Adaptive-类


---
## 写此篇的原因
- 调试时发现，有一些类的实现是 `*$Adaptive` 后缀，但搜索没有发现具体实现类
- 感觉好奇，写此篇记录下


---
## 单元测试
- `org.apache.dubbo.common.extension.ExtensionLoaderTest`
```java
class ExtensionLoaderTest {

    private <T> ExtensionLoader<T> getExtensionLoader(Class<T> type) {
        return ApplicationModel.defaultModel().getExtensionDirector().getExtensionLoader(type);
    }

    @Test
    void test_AddExtension_Adaptive() {
        ExtensionLoader<AddExt2> loader = getExtensionLoader(AddExt2.class);
        loader.addExtension(null, AddExt2_ManualAdaptive.class);    // 添加适配类

        AddExt2 adaptive = loader.getAdaptiveExtension();           // 获取时直接返回添加的（类的实例）
        assertTrue(adaptive instanceof AddExt2_ManualAdaptive);     // true
    }

    @Test
    void test_replaceExtension_Adaptive() {
        ExtensionLoader<AddExt3> loader = getExtensionLoader(AddExt3.class);
        // 没有添加适配类，则创建类 AddExt3$Adaptive 并返回（其实例）
        AddExt3 adaptive = loader.getAdaptiveExtension();      
        assertFalse(adaptive instanceof AddExt3_ManualAdaptive);    // false
        ...
    }
}
```


---
## 原理
- `org.apache.dubbo.common.extension.ExtensionLoader`
```java
public class ExtensionLoader<T> {

    public T getAdaptiveExtension() {
        Object instance = cachedAdaptiveInstance.get();
        ... // DCL 1

            synchronized (cachedAdaptiveInstance) {
                ... // DCL 2
                    instance = createAdaptiveExtension();
            }

        return (T) instance;
    }

    private T createAdaptiveExtension() {
        try {
            T instance = (T) getAdaptiveExtensionClass()    // 获取适配类
                                .newInstance();             // 创建实例
            ... // 对实例进行钩子处理和初始化
            return instance;
        } 
        ... // catch
    }

    private Class<?> getAdaptiveExtensionClass() {
        ... // 存在则直接返回
        
        return cachedAdaptiveClass = createAdaptiveExtensionClass();
    }

    private Class<?> createAdaptiveExtensionClass() {
        // 使用 SPI 接口类的 ClassLoader
        ClassLoader classLoader = type.getClassLoader();

        ... // Native 处理

        String code = new AdaptiveClassCodeGenerator(type, ...).generate();   // 生成 Java 代码
        org.apache.dubbo.common.compiler.Compiler compiler = extensionDirector
                .getExtensionLoader(org.apache.dubbo.common.compiler.Compiler.class)
                .getAdaptiveExtension();
        return compiler.compile(type, code, classLoader);   // 将 Java 代码编译成 Class 类并加载
    }
}
```


---
## 生成的类参考
### 接口定义
- `org.apache.dubbo.rpc.Protocol`
```java
@SPI(value = "dubbo", scope = ExtensionScope.FRAMEWORK)
public interface Protocol {

    int getDefaultPort();

    @Adaptive
    <T> Exporter<T> export(Invoker<T> invoker) throws RpcException;

    @Adaptive
    <T> Invoker<T> refer(Class<T> type, URL url) throws RpcException;

    void destroy();

    default List<ProtocolServer> getServers() {
        return Collections.emptyList();
    }
}
```

### 生成的类
- `Protocol$Adaptive`
```java
package org.apache.dubbo.rpc;

import org.apache.dubbo.rpc.model.ScopeModel;
import org.apache.dubbo.rpc.model.ScopeModelUtil;

public class Protocol$Adaptive implements org.apache.dubbo.rpc.Protocol {

    // 没有 @Adaptive 注解的方法，直接抛异常
    public void destroy() {
        throw new UnsupportedOperationException(...);
    }

    public int getDefaultPort() {
        throw new UnsupportedOperationException(...);
    }

    // 有  @Adaptive 注解的方法，才进行适配
    public org.apache.dubbo.rpc.Exporter export(org.apache.dubbo.rpc.Invoker arg0) throws org.apache.dubbo.rpc.RpcException {
        ... // check

        org.apache.dubbo.common.URL url = arg0.getUrl();
        String extName = (url.getProtocol() == null ? "dubbo" : url.getProtocol());
        ... // check

        ScopeModel scopeModel = ScopeModelUtil.getOrDefault(url.getScopeModel(), org.apache.dubbo.rpc.Protocol.class);
        org.apache.dubbo.rpc.Protocol extension =
                (org.apache.dubbo.rpc.Protocol) scopeModel.getExtensionLoader(org.apache.dubbo.rpc.Protocol.class)
                .getExtension(extName);
        return extension.export(arg0);
    }

    public org.apache.dubbo.rpc.Invoker refer(
        java.lang.Class arg0, org.apache.dubbo.common.URL arg1
    ) throws org.apache.dubbo.rpc.RpcException {
        ... // check

        ScopeModel scopeModel = ScopeModelUtil.getOrDefault(url.getScopeModel(), org.apache.dubbo.rpc.Protocol.class);
        org.apache.dubbo.rpc.Protocol extension =
                (org.apache.dubbo.rpc.Protocol) scopeModel.getExtensionLoader(org.apache.dubbo.rpc.Protocol.class)
                .getExtension(extName); 
        return extension.refer(arg0, arg1); // 通过 SPI 获取最终的实例，并进行调用
    }

    public java.util.List getServers() {
        throw new UnsupportedOperationException(...);
    }
}
```
