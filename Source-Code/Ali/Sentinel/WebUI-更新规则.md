## 说明
- 更新规则分为两步：
  - 控制台修改并通知给应用端
  - 应用端监听并修改到内存


## 参考
1. [WebMVC-控制-交互服务启动 sign_m_210](WebMVC-控制.md#交互服务启动)
2. [入口控制-设置规则 sign_demo_020](入口控制.md#设置规则)


## 原理
### 控制台
- 模块：`sentinel-dashboard`

- **不启动权限**设置
  - 改 `application.properties`
    - 添加一行 `auth.enabled=false`
  - 然后再启动 `DashboardApplication`，就不用经常登录了

- Web 请求：
  ```js
  // 新增
  POST /v1/flow/rule
  
  {
    "grade": 1,
    "strategy": 0,
    "controlBehavior": 0,
    "app": "My-Test-8866",
    "ip": "10.32.51.130",
    "port": "8720",
    "limitApp": "default",
    "clusterMode": false,
    "clusterConfig": {
      "thresholdType": 0
    },
    "resource": "GET:/hello", // 资源名
    "count": 2
  }
  
  // 修改 (集群模式改不了)
  PUT /v1/flow/save.json
  ?controlBehavior=0&count=33&grade=1&id=27&limitApp=default&maxQueueingTimeMs=500&resource=test11&strategy=0&warmUpPeriodSec=10
  
  // Param:
  controlBehavior=0
  count=33
  grade=1
  id=27
  limitApp=default
  maxQueueingTimeMs=500
  resource=test11
  strategy=0
  warmUpPeriodSec=10
  ```

- `com.alibaba.csp.sentinel.dashboard.controller.FlowControllerV1`
```java
/*** 规则的 Web 交互控制器 */
@RestController
@RequestMapping(value = "/v1/flow")
public class FlowControllerV1 {

    // 映射的全路径为: /v1/flow/rule
    @PostMapping("/rule")
    @AuthAction(PrivilegeType.WRITE_RULE)
    public Result<FlowRuleEntity> apiAddFlowRule(@RequestBody FlowRuleEntity entity) {
        ... // 省略校验 entity

        entity.setId(null); // repository.save() 会设置 id

        ... // 省略设置 entity 的创建和修改时间
        ... // 省略去除 entity 的 LimitApp 和 Resource 空格
        try {
            entity = repository.save(entity);   // 保存到内存
            publishRules(entity.getApp(), entity.getIp(), entity.getPort()) // 重新发布一次所有规则  sign_m_110
                .get(5000, TimeUnit.MILLISECONDS);
            return Result.ofSuccess(entity);
        } ... // catch
    }

    // sign_m_110 发布所有规则
    private CompletableFuture<Void> publishRules(String app, String ip, Integer port) {
        List<FlowRuleEntity> rules = repository.findAllByMachine(MachineInfo.of(app, ip, port));
        return sentinelApiClient.setFlowRuleOfMachineAsync(app, ip, port, rules);   // 发布所有规则  sign_m_120
    }

}
```

- `com.alibaba.csp.sentinel.dashboard.client.SentinelApiClient`
```java
    // sign_m_120 发布所有规则
    public CompletableFuture<Void> setFlowRuleOfMachineAsync(String app, String ip, int port, List<FlowRuleEntity> rules) {
        return setRulesAsync(app, ip, port, FLOW_RULE_TYPE, rules); // sign_m_121
    }

    // sign_m_121
    private CompletableFuture<Void> setRulesAsync(
        String app, String ip, int port, String type, List<? extends RuleEntity> entities
    ) {
        try {
            ... // 省略校验参数
            String data = JSON.toJSONString(
                entities.stream().map(r -> r.toRule()).collect(Collectors.toList()) // FlowRuleEntity -> FlowRule
            );
            Map<String, String> params = new HashMap<>(2);  // sign_param_110 参数规则
            params.put("type", type);
            params.put("data", data);
            // SET_RULES_PATH = "setRules"; 
            // 相当于命令为 setRules，命令处理者为 ModifyRulesCommandHandler, ref: sign_c_200
            return executeCommand(app, ip, port, SET_RULES_PATH, params, true)  // sign_m_122
                .thenCompose(r -> {
                    if ("success".equalsIgnoreCase(r.trim())) {
                        return CompletableFuture.completedFuture(null);
                    }
                    return AsyncUtils.newFailedFuture(new CommandFailedException(r));
                });
        } ... // catch
    }

    // sign_m_122
    private CompletableFuture<String> executeCommand(
        String app, String ip, int port, String api, Map<String, String> params, boolean useHttpPost
    ) {
        CompletableFuture<String> future = new CompletableFuture<>();
        
        ... // 省略参数校验

        StringBuilder urlBuilder = new StringBuilder();
        urlBuilder.append("http://");
        urlBuilder.append(ip).append(':').append(port).append('/').append(api);
        
        ... // 省略 params 为空处理

        if (!useHttpPost || !isSupportPost(app, ip, port)) {
            // 旧版本使用 GET，在 URL 后面追加参数
            if (!params.isEmpty()) {
                ... // 省略拼接参数到 URL (如：? &)
            }
            return executeCommand(new HttpGet(urlBuilder.toString()));  // sign_m_123
        } else {
            // 使用 POST
            return executeCommand(                                      // sign_m_123
                    // 构建 http-client 请求
                    postRequest(urlBuilder.toString(), params, isSupportEnhancedContentType(app, ip, port))
                );
        }
    }

    // sign_m_123
    private CompletableFuture<String> executeCommand(HttpUriRequest request) {
        CompletableFuture<String> future = new CompletableFuture<>();
        httpClient.execute(request, new FutureCallback<HttpResponse>() {
            @Override
            public void completed(final HttpResponse response) {
                int statusCode = response.getStatusLine().getStatusCode();
                try {
                    String value = getBody(response);
                    if (isSuccess(statusCode)) {
                        future.complete(value);
                    } else {
                        ... // 省略异常处理
                    }
                } ... // catch
            }
            ... // 省略 failed、cancelled 处理
        });
        return future;
    }
```

### 应用端
- 参考：
  - [WebMVC-控制-交互服务启动 sign_m_210](WebMVC-控制.md#交互服务启动)
  - [入口控制-设置规则 sign_demo_020](入口控制.md#设置规则)

- `com.alibaba.csp.sentinel.command.handler.ModifyRulesCommandHandler`
```java
@CommandMapping(
    name = "setRules",  // 相当于命令名
    desc = "modify the rules, accept param: type={ruleType}&data={ruleJson}"
)
// sign_c_200 更改规则 (setRules) 命令处理者
public class ModifyRulesCommandHandler implements CommandHandler<String> {

    @Override
    public CommandResponse<String> handle(CommandRequest request) {
        ... // 省略校验 fastjson 版本

        String type = request.getParam("type");
        String data = request.getParam("data");     // 规则数据

        ... // 省略对 data 进行 URL 解码

        String result = "success";

        if (FLOW_RULE_TYPE.equalsIgnoreCase(type)) {
            List<FlowRule> flowRules = JSONArray.parseArray(data, FlowRule.class);
            FlowRuleManager.loadRules(flowRules);   // 更新规则到内存  ref: sign_demo_020
            /**
             * 写入数据源 (可参考 FileWritableDataSource，自己实现)，
             * 官方只实现从其他数据源 (Redis, Nacos 等) 的读，没有实现写，
             * 因此需要自己实现写。
             */
            if (!writeToDataSource(getFlowDataSource(), flowRules)) {
                result = WRITE_DS_FAILURE_MSG;
            }
            return CommandResponse.ofSuccess(result);
        }
        ... // 省略其他类型处理

        return CommandResponse.ofFailure(new IllegalArgumentException("invalid type"));
    }

}
```

### 总结
- 官方只实现从其他数据源 (Redis, Nacos 等) 的读，没有实现写，因此需要自己实现写。