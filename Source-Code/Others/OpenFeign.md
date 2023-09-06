## 重试机制代码参考
- 调用：
```java
while (true) {
  try {
    xxx; // 业务代码
  } catch (RetryableException e) {
    retryer.continueOrPropagate(e); // 异常时重试，并将异常传过去
  }
}
```

- 重试：
```java
public void continueOrPropagate(RetryableException e) {
  if (attempt++ >= maxAttempts)
    throw e; // 超过重试次数则抛出原来的异常

  long interval = nextMaxInterval();
  try {
    Thread.sleep(interval); // 睡眠一段时间
  } catch (InterruptedException ignored) {
    Thread.currentThread().interrupt();
  }
}
```

- 附：
  - OpenFeign 原理：使用 Java 动态代理，生成调用对象