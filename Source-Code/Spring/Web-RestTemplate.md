# Spring-Web-RestTemplate


## 测试
- 参考：
  - [Spring-Cloud-Alibaba-测试-服务发现](../Ali/Spring-Cloud-Alibaba/服务发现与注册.md#测试)

- `com.alibaba.cloud.examples.TestController`
```java
    // http://localhost:18083/echo-rest/test66
    @GetMapping("/echo-rest/{str}")
    public String rest(@PathVariable String str) {
        return urlCleanedRestTemplate.getForObject( // REST 请求，ref: sign_m_100
                SERVICE_PROVIDER_ADDRESS + "/echo/" + str, String.class
        );
    }
```


## 请求链路
- `org.springframework.web.client.RestTemplate`
```java
// 继承： sign_c_120
public class RestTemplate extends InterceptingHttpAccessor implements RestOperations {

    // sign_m_100  REST Get 方式请求
    @Override @Nullable
    public <T> T getForObject(String url, Class<T> responseType, Object... uriVariables) throws RestClientException {
        ...
        return execute(url, HttpMethod.GET, requestCallback, responseExtractor, uriVariables); // ref: sign_m_101
    }

    // sign_m_101  执行请求
    @Override @Nullable
    public <T> T execute(String uriTemplate, HttpMethod method, @Nullable RequestCallback requestCallback,
            @Nullable ResponseExtractor<T> responseExtractor, Object... uriVariables
    ) throws RestClientException {
        URI url = getUriTemplateHandler().expand(uriTemplate, uriVariables);
        return doExecute(url, uriTemplate, method, requestCallback, responseExtractor); // ref: sign_m_102
    }
    
    // sign_m_102  具体执行
    @Nullable
    protected <T> T doExecute(URI url, @Nullable String uriTemplate, @Nullable HttpMethod method, @Nullable RequestCallback requestCallback,
            @Nullable ResponseExtractor<T> responseExtractor
    ) throws RestClientException {
        ...

        ClientHttpRequest request;
        try {
            request = createRequest(url, method); // 创建请求，ref: sign_m_110
        } 
        ... // catch

        ...
        ClientHttpResponse response = null;
        try {
            ...
            response = request.execute(); // 执行请求，ref: sign_m_230
            ...
            return (responseExtractor != null ? responseExtractor.extractData(response) : null); // 提取结果
        }
        ... // catch finally
    }

}
```

- `org.springframework.http.client.support.HttpAccessor`
```java
// sign_c_110
public abstract class HttpAccessor {
    // sign_m_110  创建请求
    protected ClientHttpRequest createRequest(URI url, HttpMethod method) throws IOException {
        ClientHttpRequest request = getRequestFactory() // 返回 InterceptingClientHttpRequestFactory 实例，ref: sign_m_120
            .createRequest(url, method);    // 返回 InterceptingClientHttpRequest 实例，ref: sign_c_210
        initialize(request);
        ...
        return request;
    }
}
```

- `org.springframework.http.client.support.InterceptingHttpAccessor`
```java
// sign_c_120  继承： sign_c_110
public abstract class InterceptingHttpAccessor extends HttpAccessor {
    // sign_m_120  重写了获取请求工厂的方法
    @Override
    public ClientHttpRequestFactory getRequestFactory() {
        List<ClientHttpRequestInterceptor> interceptors = getInterceptors();
        if (!CollectionUtils.isEmpty(interceptors)) { // 有拦截器设置
            ClientHttpRequestFactory factory = this.interceptingRequestFactory;
            if (factory == null) {
                factory = new InterceptingClientHttpRequestFactory(super.getRequestFactory(), interceptors);
                this.interceptingRequestFactory = factory;
            }
            return factory;
        }
        ... // else
    }
}
```

### 请求
- `org.springframework.http.client.InterceptingClientHttpRequest`
```java
// sign_c_210  继承： sign_c_220
class InterceptingClientHttpRequest extends AbstractBufferingClientHttpRequest {

    // sign_m_210
    @Override
    protected final ClientHttpResponse executeInternal(HttpHeaders headers, byte[] bufferedOutput) throws IOException {
        InterceptingRequestExecution requestExecution = new InterceptingRequestExecution(); // ref: sign_c_211 | sign_cm_211
        return requestExecution.execute(this, bufferedOutput); // ref: sign_m_211
    }

    // sign_c_211
    private class InterceptingRequestExecution implements ClientHttpRequestExecution {
        private final Iterator<ClientHttpRequestInterceptor> iterator;

        // sign_cm_211
        public InterceptingRequestExecution() {
            this.iterator = interceptors.iterator();
        }

        // sign_m_211
        @Override
        public ClientHttpResponse execute(HttpRequest request, byte[] body) throws IOException {
            if (this.iterator.hasNext()) { // 存在拦截器
                ClientHttpRequestInterceptor nextInterceptor = this.iterator.next();
                return nextInterceptor.intercept(request, body, this); // 直接用第一个拦截器进行处理
            }
            else { // 没有拦截器
                HttpMethod method = request.getMethod();
                ClientHttpRequest delegate = requestFactory.createRequest(request.getURI(), method);
                ...
                return delegate.execute(); // 则用 SimpleClientHttpRequest 进行请求处理
            }
        }
    }
}
```

- `org.springframework.http.client.AbstractBufferingClientHttpRequest`
```java
// sign_c_220  继承： sign_c_230
abstract class AbstractBufferingClientHttpRequest extends AbstractClientHttpRequest {
    
    // sign_m_220
    @Override
    protected ClientHttpResponse executeInternal(HttpHeaders headers) throws IOException {
        byte[] bytes = this.bufferedOutput.toByteArrayUnsafe();
        ...
        ClientHttpResponse result = executeInternal(headers, bytes); // ref: sign_m_210
        this.bufferedOutput.reset();
        return result;
    }
}
```

- `org.springframework.http.client.AbstractClientHttpRequest`
```java
// sign_c_230
public abstract class AbstractClientHttpRequest implements ClientHttpRequest {

    // sign_m_230  执行请求
    @Override
    public final ClientHttpResponse execute() throws IOException {
        ...
        ClientHttpResponse result = executeInternal(this.headers); // ref: sign_m_220
        this.executed = true;
        return result;
    }
}
```