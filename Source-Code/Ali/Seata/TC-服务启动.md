# Seata-TC-服务启动


---
## 应用启动
- 模块为: `server [seata-server]`
- 启动类: `io.seata.server.ServerApplication`

### 初始-TC-监听端口
- 一般为 Web 端口加 `1000`

- `io.seata.server.spring.listener.ServerApplicationListener`
```java
public class ServerApplicationListener implements GenericApplicationListener {

    @Override
    public void onApplicationEvent(ApplicationEvent event) {
        ...

        ConfigurableEnvironment environment = environmentPreparedEvent.getEnvironment();
        ObjectHolder.INSTANCE.setObject(OBJECT_KEY_SPRING_CONFIGURABLE_ENVIRONMENT, environment);
        ...

        // 获取端口顺序为：-p > -D > env > yml > default
        ... // -p 8091
        ... // -Dserver.servicePort=8091
        ... // docker -e SEATA_PORT=8091
        ... // yml properties server.service-port=8091
        
        // server.port=7091
        String serverPort = environment.getProperty("server.port", String.class);
        ...

        // 端口最终为 7091 + 1000 = 8091
        String servicePort = String.valueOf(Integer.parseInt(serverPort) + SERVICE_OFFSET_SPRING_BOOT);
        setTargetPort(environment, servicePort, true); // 设置到配置中
    }
}
```