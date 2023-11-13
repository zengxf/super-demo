## 测试
- 在 `WebMvcDemoApplication` 类的 `main()` 方法改成如下：
```java
    public static void main(String[] args) {
        System.setProperty("csp.sentinel.dashboard.server", "127.0.0.1:8080");
        System.setProperty("project.name", "My-Test-8866");
        SpringApplication.run(WebMvcDemoApplication.class);
    }
```
- 先启动 `DashboardApplication`
  - 访问 http://localhost:8080/#/dashboard
    - 登录：`sentinel / sentinel`
- 再启动 `WebMvcDemoApplication`
  - 访问 http://localhost:10000/hello
    - dashboard 才会显示


## 原理
- `demo-webmvc` 依赖模块：
  - `sentinel-spring-webmvc-adapter`
    - 用于链路控制适配
  - `sentinel-transport-simple-http` (相同的有 `sentinel-transport-netty-http`)
    - 用于心跳检测

### 链路控制适配
- `com.alibaba.csp.sentinel.adapter.spring.webmvc.SentinelWebInterceptor`
```java
/** 使用 SpringMVC 拦截器进行拦截，在 WebMvcConfigurer 里进行配置 */
public class SentinelWebInterceptor extends AbstractSentinelInterceptor {

    private final SentinelWebMvcConfig config;

    public SentinelWebInterceptor() {
        this(new SentinelWebMvcConfig());
    }

    public SentinelWebInterceptor(SentinelWebMvcConfig config) {
        super(config);
        ... // 省略
    }

}
```

- `com.alibaba.csp.sentinel.adapter.spring.webmvc.AbstractSentinelInterceptor`
```java
/** Sentinel 拦截器 (做控制逻辑) */
public abstract class AbstractSentinelInterceptor implements HandlerInterceptor {

    // 拦截前处理
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
        throws Exception 
    {
        try {
            String resourceName = getResourceName(request);

            ... // resourceName 为空返回 true
            
            if (increaseReferece(request, this.baseWebMvcConfig.getRequestRefName(), 1) != 1) {
                return true;  // 只对首个进行拦截处理
            }
            
            ... // 省略上下文处理
            Entry entry = SphU.entry(resourceName, ResourceTypeConstants.COMMON_WEB, EntryType.IN); // 正式流控
            request.setAttribute(baseWebMvcConfig.getRequestAttributeName(), entry);                // 做记录，方便后面退出处理
            return true;
        } catch (BlockException e) {
            try {
                handleBlockException(request, response, e); // 异常处理 sign_m_010
            } finally {
                ContextUtil.exit();
            }
            return false; // 流控限制
        }
    }
    
    // sign_m_010 异常处理
    protected void handleBlockException(HttpServletRequest request, HttpServletResponse response, BlockException e)
        throws Exception 
    {
        if (baseWebMvcConfig.getBlockExceptionHandler() != null) {
            baseWebMvcConfig.getBlockExceptionHandler().handle(request, response, e);
        } else {
            throw e;
        }
    }

    // 完成后处理
    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) throws Exception 
    {
        if (increaseReferece(request, this.baseWebMvcConfig.getRequestRefName(), -1) != 0) {
            return; // 不在最后一个 (相当于首个) 不处理
        }
        
        Entry entry = getEntryInRequest(request, baseWebMvcConfig.getRequestAttributeName());
        if (entry == null) {
            ... // log warn
            return;
        }
        
        traceExceptionAndExit(entry, ex); // 退出处理
        removeEntryInRequest(request);    // 移除 request 属性
        ContextUtil.exit();
    }

}
```

#### 拦截器添加示例
- `com.alibaba.csp.sentinel.demo.spring.webmvc.config.InterceptorConfig`
```java
// 使用 Spring 配置
@Configuration
public class InterceptorConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        addSpringMvcInterceptor(registry);  
    }

    private void addSpringMvcInterceptor(InterceptorRegistry registry) {
        SentinelWebMvcConfig config = new SentinelWebMvcConfig();
        ... // 省略其他配置
        config.setOriginParser(request -> request.getHeader("S-user"));
        // 添加到拦截器链
        registry.addInterceptor(new SentinelWebInterceptor(config)).addPathPatterns("/**");
    }
}
```