## 代码参考
- Java 字符串拼接：
  - `string.concat("x").concat("y")`

- Slf4j 格式转化：
  ```java
  FormattingTuple ft = MessageFormatter.arrayFormat("log: {} - {}", paramArr);
  String log = ft.getMessage();
    ```

- Java 异常输出到流：
  ```java
  StringWriter stringWriter = new StringWriter();
  e.printStackTrace(new PrintWriter(stringWriter));
  String log = stringWriter.toString();
  ```

- Spring `SmartInitializingSingleton`：
  - 该接口在 bean 单例对象（非懒加载对象）初始化完成之后调用
  - 包括依赖注入完成，`BeadPostProcess,InitializingBean,initMethod` 等等全部完成后执行
  - 可以理解为 **bean 的收尾操作**
