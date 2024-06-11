# Dubbo-$Adaptive-类


---
## 此篇说明
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

        AddExt2 adaptive = loader.getAdaptiveExtension();           // 获取时直接返回添加的（类的实例），ref: sign_m_110
        assertTrue(adaptive instanceof AddExt2_ManualAdaptive);     // true
    }

    @Test
    void test_replaceExtension_Adaptive() {
        ExtensionLoader<AddExt3> loader = getExtensionLoader(AddExt3.class);
        // 没有添加适配类，则创建类 AddExt3$Adaptive 并返回（其实例），ref: sign_m_110
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
// sign_c_110
public class ExtensionLoader<T> {

    // sign_m_110  获取适配实例
    public T getAdaptiveExtension() {
        Object instance = cachedAdaptiveInstance.get();
        ... // DCL 1

            synchronized (cachedAdaptiveInstance) {
                ... // DCL 2
                    instance = createAdaptiveExtension();   // 创建适配实例，ref: sign_m_111
            }

        return (T) instance;
    }

    // sign_m_111  创建适配实例
    private T createAdaptiveExtension() {
        try {
            T instance = (T) getAdaptiveExtensionClass()    // 获取适配类，ref: sign_m_112
                                .newInstance();             // 创建实例
            ... // 对实例进行钩子处理和初始化
            return instance;
        } 
        ... // catch
    }

    // sign_m_112  获取适配类
    private Class<?> getAdaptiveExtensionClass() {
        ... // 存在则直接返回
        
        return cachedAdaptiveClass = createAdaptiveExtensionClass();    // 创建适配类，ref: sign_m_113
    }

    // sign_m_113  创建适配类
    private Class<?> createAdaptiveExtensionClass() {
        // 使用 SPI 接口类的 ClassLoader
        ClassLoader classLoader = type.getClassLoader();

        ... // Native 处理

        String code = new AdaptiveClassCodeGenerator(type, ...)
                            .generate();   // 生成 Java 代码，生成的代码参考： sign_c_250
        org.apache.dubbo.common.compiler.Compiler compiler = extensionDirector
                .getExtensionLoader(org.apache.dubbo.common.compiler.Compiler.class)
                .getAdaptiveExtension();
        return compiler.compile(type, code, classLoader);   // 将 Java 代码编译成 Class 类并加载
    }
}
```


---
## 生成的类参考
### 接口定义示例
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

// sign_c_250  生成的适配类（参考）
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

        ScopeModel scopeModel = ScopeModelUtil.getOrDefault(url.getScopeModel(), Protocol.class);   // ref: sign_m_410
        org.apache.dubbo.rpc.Protocol extension =
                (org.apache.dubbo.rpc.Protocol) scopeModel.getExtensionLoader(org.apache.dubbo.rpc.Protocol.class)
                .getExtension(extName);
        return extension.export(arg0);
    }

    // sign_m_250
    public org.apache.dubbo.rpc.Invoker refer(
        java.lang.Class arg0, org.apache.dubbo.common.URL arg1
    ) throws org.apache.dubbo.rpc.RpcException {
        ... // check

        ScopeModel scopeModel = ScopeModelUtil.getOrDefault(url.getScopeModel(), Protocol.class);   // ref: sign_m_410
        org.apache.dubbo.rpc.Protocol extension =
                (org.apache.dubbo.rpc.Protocol) scopeModel.getExtensionLoader(org.apache.dubbo.rpc.Protocol.class)
                .getExtension(extName); 
        return extension.refer(arg0, arg1); // 通过分层 SPI 获取最终的实例，并进行调用
    }

    public java.util.List getServers() {
        throw new UnsupportedOperationException(...);
    }
}
```

### 其他生成的类参考
- `ProxyFactory$Adaptive`
```java
package org.apache.dubbo.rpc;

import org.apache.dubbo.rpc.model.ScopeModel;
import org.apache.dubbo.rpc.model.ScopeModelUtil;
import org.apache.dubbo.rpc.*;   // 为省代码

// sign_c_260
public class ProxyFactory$Adaptive implements ProxyFactory {
    
    // sign_m_260
    public java.lang.Object getProxy(
        Invoker invoker, boolean generic
    ) throws RpcException {
        ... // check

        org.apache.dubbo.common.URL url = invoker.getUrl();
        String extName = url.getParameter("proxy", "javassist");
        ... // check

        ScopeModel scopeModel = ScopeModelUtil.getOrDefault(url.getScopeModel(), ProxyFactory.class);   // ref: sign_m_410
        ProxyFactory extension = scopeModel.getExtensionLoader(ProxyFactory.class)  // 返回 ExtensionLoader
                .getExtension(extName);
        return extension.getProxy(invoker, generic);
    }

    ... // 其他适配的方法省略
}
```

- `Transporter$Adaptive`
```java
package org.apache.dubbo.remoting;

import org.apache.dubbo.rpc.model.ScopeModel;
import org.apache.dubbo.rpc.model.ScopeModelUtil;
import org.apache.dubbo.remoting.*;

public class Transporter$Adaptive implements Transporter {

    public org.apache.dubbo.remoting.Client connect(URL arg0, ChannelHandler arg1) throws RemotingException {
        URL url = arg0;
        String extName = url.getParameter("client", url.getParameter("transporter", "netty"));
        ScopeModel scopeModel = ScopeModelUtil.getOrDefault(url.getScopeModel(), Transporter.class);    // ref: sign_m_410
        Transporter extension =
                (Transporter) scopeModel.getExtensionLoader(Transporter.class)
                .getExtension(extName);
        return extension.connect(arg0, arg1);
    }

    public RemotingServer bind(URL arg0, ChannelHandler arg1) throws RemotingException {
        URL url = arg0;
        String extName = url.getParameter("server", url.getParameter("transporter", "netty"));
        ScopeModel scopeModel = ScopeModelUtil.getOrDefault(url.getScopeModel(), Transporter.class);    // ref: sign_m_410
        Transporter extension =
                (Transporter) scopeModel.getExtensionLoader(Transporter.class)
                .getExtension(extName);
        return extension.bind(arg0, arg1);
    }
}
```

### 总结
- 有 `@Adaptive` 注解的方法，才进行适配
  - 内部只是利用分层 SPI 获取目标对象，并进行最终调用


---
## SPI 调用
- `org.apache.dubbo.rpc.model.ScopeModelUtil`
```java
// sign_c_410
public class ScopeModelUtil {

    // sign_m_410
    public static <T> ScopeModel getOrDefault(ScopeModel scopeModel, Class<T> type) {
        // 一般将 URL.getScopeModel() 作参数传过来，其值为 ModuleModel 实例
        if (scopeModel != null) {
            return scopeModel;
        }
        return getDefaultScopeModel(type);  // ref: sign_m_411
    }

    // sign_m_411
    private static <T> ScopeModel getDefaultScopeModel(Class<T> type) {
        SPI spi = type.getAnnotation(SPI.class);
        ... // check

        switch (spi.scope()) {
            case FRAMEWORK:
                return FrameworkModel.defaultModel();   // ref: sign_m_420
            case APPLICATION:
                return ApplicationModel.defaultModel(); // ref: sign_m_430
            case MODULE:
                return ApplicationModel.defaultModel().getDefaultModule();  // ref: sign_m_430 | sign_m_431
            default:
                throw new IllegalStateException(...);
        }
    }
}
```

- `org.apache.dubbo.rpc.model.FrameworkModel`
```java
// sign_c_420
public class FrameworkModel extends ScopeModel {

    // sign_m_420
    public static FrameworkModel defaultModel() {
        FrameworkModel instance = defaultInstance;

        ... // DCL
                defaultInstance = new FrameworkModel();
                instance = defaultInstance;
        ...

        return instance;
    }

    // sign_m_421
    public ApplicationModel defaultApplication() {
        ApplicationModel appModel = this.defaultAppModel;
        ... // DCL
                    this.defaultAppModel = newApplication();    // ref: sign_m_422
                    appModel = this.defaultAppModel;
        ...
        return appModel;
    }

    // sign_m_422
    public ApplicationModel newApplication() {
        synchronized (instLock) {
            return new ApplicationModel(this);  // 将自己作为 ApplicationModel 的父级
        }
    }
}
```

- `org.apache.dubbo.rpc.model.ApplicationModel`
```java
// sign_c_430
public class ApplicationModel extends ScopeModel {

    // sign_m_430
    public static ApplicationModel defaultModel() {
        return FrameworkModel.defaultModel().defaultApplication();  // ref: sign_m_421
    }

    // sign_m_431
    public ModuleModel getDefaultModule() {
        ... // DCL
                    defaultModule = this.newModule();   // ref: sign_m_432
        ...

        return defaultModule;
    }

    // sign_m_432
    public ModuleModel newModule() {
        synchronized (instLock) {
            return new ModuleModel(this);
        }
    }
}
```

### SPI 分层
```js
// 分层链类似 Java 的类加载器
ModuleModel(.parent) -> ApplicationModel(.parent) -> FrameworkModel(.parent) -> null

// 获取扩展加载器 (ExtensionLoader) #getExtensionLoader(type)
// 先调用自身，再按照上面的链结构调用父类
```