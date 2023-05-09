# Arhtas 实战
## ref
- **快速入门** https://arthas.aliyun.com/doc/quick-start.html
- **arthas-idea-plugin** https://www.yuque.com/arthas-idea-plugin
- **Spring-Web 试验项目** https://github.com/zengxf/spring-demo/tree/master/web/mock-data-web


---
## 启动
- **运行 jar**：`java -Dfile.encoding=UTF-8 -jar arthas-boot.jar`
  - 设置 `UTF-8` 防止乱码
```js
C:\Users\656553> cd /d D:\Install\Java\Ali\arthas-3.6.8
// 启动：直接运行 jar: java -jar arthas-boot.jar
D:\Install\Java\Ali\arthas-3.6.8> java -Dfile.encoding=UTF-8 -jar arthas-boot.jar
[INFO] JAVA_HOME: C:\Install\Java\JDK\openjdk-17-35
[INFO] arthas-boot version: 3.6.8
[INFO] Process 20648 already using port 3658
[INFO] Process 20648 already using port 8563
[INFO] Found existing java process, please choose one and input the serial number of the process, eg : 1. Then hit ENTER.
* [1]: 20648 test.MainApplication
  [2]: 12304
  [3]: 12432 org.gradle.launcher.daemon.bootstrap.GradleDaemon
// 选择 1
1
[INFO] arthas home: D:\Install\Java\Ali\arthas-3.6.8
[INFO] The target process already listen port 3658, skip attach.
// 开启连接端口，可 Web 查看：http://127.0.0.1:3658
[INFO] arthas-client connect 127.0.0.1 3658
  ,---.  ,------. ,--------.,--.  ,--.  ,---.   ,---.
 /  O  \ |  .--. ''--.  .--'|  '--'  | /  O  \ '   .-'
|  .-.  ||  '--'.'   |  |   |  .--.  ||  .-.  |`.  `-.
|  | |  ||  |\  \    |  |   |  |  |  ||  | |  |.-'    |
`--' `--'`--' '--'   `--'   `--'  `--'`--' `--'`-----'

wiki       https://arthas.aliyun.com/doc
tutorials  https://arthas.aliyun.com/doc/arthas-tutorials.html
version    3.6.8
main_class
pid        20648
time       2023-05-08 14:33:00

[arthas@20648]$
```

- **Web 控制台**：http://127.0.0.1:3658


---
## 使用
### IDEA 安装 `arthas-idea` 插件
- **方便复制相关命令**
![x](https://s1.ax1x.com/2023/05/08/p9whcRO.png)
```js
// 复制的命令如下：
watch test.biz.BizService getUsers '{params,returnObj,throwExp}'  -n 5  -x 3 
```


---
## 命令
### dashboard
- https://arthas.aliyun.com/doc/dashboard.html
- **查看系统的实时数据面板**，按 `ctrl + c` 退出
- cmd `dashboard`
- 插件 `Other` 里面
- ~~此命令 `dashboard l:3000 n:3`~~ 并不退出

### getstatic
- https://arthas.aliyun.com/doc/getstatic.html
- **查看类的静态属性**
- cmd `getstatic test.user.LoginController USERNAME -x 3`
- 插件 `Simple Get Static Field`
![x](https://s1.ax1x.com/2023/05/08/p9wI5w9.png)
```js
[arthas@6972]$ getstatic test.user.LoginController USERNAME -x 3
field: USERNAME
@String[zxf]
Affect(row-cnt:1) cost in 12 ms.

// 相当于如下 ognl 命令
[arthas@6972]$ ognl -x 3 '@test.user.LoginController@USERNAME'
@String[zxf]
[arthas@6972]$
```

### heapdump
- https://arthas.aliyun.com/doc/heapdump.html
- **dump 堆到文件**
- cmd `heapdump /tmp/dump.hprof`
- 插件 `Other` 里面
- **`arthas-output` 在目标应用的当前目录下**
```js
// 生成文件在 arthas-output 目录，
// 可以通过浏览器下载： http://127.0.0.1:3658/arthas-output/
[arthas@6972]$ heapdump arthas-output/dump.hprof
Dumping heap to arthas-output/dump.hprof ...
Heap dump file created

// 只 dump live 对象到指定文件
[arthas@6972]$ heapdump --live D:/Data/test/dump.hprof
Dumping heap to D:/Data/test/dump.hprof ...
Heap dump file created

// dump 到临时文件
[arthas@6972]$ heapdump
Dumping heap to C:\Users\656553\AppData\Local\Temp\heapdump2023-05-08-15-2013284160575598095523.hprof ...
Heap dump file created
[arthas@6972]$
```

### jvm
- https://arthas.aliyun.com/doc/jvm.html
- **查看当前 JVM 信息**
- **要查看`死锁的线程数`及线程其他相关统计和 JVM 参数时有用**

### logger
- https://arthas.aliyun.com/doc/logger.html
- **查看 logger 信息，更新 logger level**
- ***测试失败***

### mbean
- https://arthas.aliyun.com/doc/mbean.html
- **查看 Mbean 信息**
- ***很少使用***

### memory
- https://arthas.aliyun.com/doc/memory.html
- **查看 JVM 内存信息**
```js
[arthas@24132]$ memory
Memory                                             used             total            max              usage
heap                                               50M              108M             4032M            1.25%
g1_eden_space                                      22M              52M              -1               42.31%
g1_old_gen                                         26M              54M              4032M            0.66%
g1_survivor_space                                  2M               2M               -1               100.00%
nonheap                                            65M              68M              -1               95.15%
codeheap_'non-nmethods'                            1M               2M               5M               24.15%
metaspace                                          45M              46M              -1               98.97%
codeheap_'profiled_nmethods'                       9M               10M              117M             8.19%
compressed_class_space                             5M               5M               1024M            0.56%
codeheap_'non-profiled_nmethods'                   2M               3M               117M             2.30%
mapped                                             0K               0K               -                0.00%
direct                                             4M               4M               -                100.00%
mapped - 'non-volatile memory'                     0K               0K               -                0.00%
```

### ognl
- https://arthas.aliyun.com/doc/ognl.html
- **执行 ognl 表达式**
- ognl: `@test.utils.UserUtils@getUsers(0, " ")`
![x](https://s1.ax1x.com/2023/05/08/p9wje78.png)
- cmd `ognl -x 3 '@test.utils.UserUtils@getUsers(1, "xx-")'`
![x](https://s1.ax1x.com/2023/05/08/p9wjvgs.png)
```js
// 调用静态函数
[arthas@23600]$ ognl '@java.lang.System@out.println("hello")'
null

// 调用静态函数（有返回结果的）
[arthas@23600]$ ognl '@test.utils.UserUtils@getUsers(2, "test-6688-")'
@ArrayList[
    @UserDto[UserDto(id=test-6688-1, name=test-1, age=33, remark=null, status=null)],
    @UserDto[UserDto(id=test-6688-2, name=test-2, age=34, remark=null, status=null)],
]

// 调用静态函数（抛错的）
[arthas@23600]$ ognl '@test.utils.UserUtils@getUsers(-1, "test-6688-")'
Failed to execute ognl, exception message: ognl.MethodFailedException: Method "getUsers" failed for object class test.utils.UserUtils [java.lang.RuntimeException: 参数错误！size = -1], please check $HOME/logs/arthas/arthas.log for more details.

// 调用静态函数（格式化输出）
[arthas@23600]$ ognl -x 3 '@test.utils.UserUtils@getUsers(1, "x-68-")'
@ArrayList[
    @UserDto[
        id=@String[x-68-1],
        name=@String[test-1],
        age=@Integer[33],
        remark=null,
        status=null,
    ],
]
[arthas@23600]$
```

### ...
### retransform
- https://arthas.aliyun.com/doc/retransform.html
- **加载外部的.class文件，retransform jvm 已加载的类**
- **消除 retransform 的影响**
  - 删除这个类对应的 retransform entry
  - 重新触发 retransform
```js
// 将 ms 由原来的 5 改成 10
private int sleep5Ms() throws InterruptedException {
    int ms = 10;
    Thread.sleep(ms);
    return ms;
}

// 执行 TestBizService 单元测试，IDEA 才会重新编译
// 访问 http://localhost:9066/api/biz/sleepMs?ms=20
09:50:14.084 [http-nio-9066-exec-3] INFO  test.biz.BizService - use ms: [48], ms2: [5] 
// 输出没变

// 重新加载类
[arthas@18512]$ retransform  build/classes/java/main/test/biz/BizService.class
retransform success, size: 1, classes:
test.biz.BizService
[arthas@18512]$

// 访问 http://localhost:9066/api/biz/sleepMs?ms=20
09:53:39.697 [http-nio-9066-exec-5] INFO  test.biz.BizService - use ms: [43], ms2: [10] 
// 输出已改变


// 查看 retransform entry
[arthas@18512]$ retransform -l
Id              ClassName       TransformCount  LoaderHash      LoaderClassName
1               test.biz.BizSer 1               null            null
                vice
2               test.biz.BizSer 2               null            null
                vice
// 删除指定 retransform entry
[arthas@18512]$ retransform -d 1
// 删除所有 retransform entry
[arthas@18512]$ retransform --deleteAll
// 显式触发 retransform（不触发一次不会还原）
[arthas@18512]$ retransform --classPattern test.biz.BizService
retransform success, size: 1, classes:
test.biz.BizService
[arthas@18512]$

// 访问 http://localhost:9066/api/biz/sleepMs?ms=20
10:01:06.780 [http-nio-9066-exec-8] INFO  test.biz.BizService - use ms: [32], ms2: [5] 
// 输出已还原
```

### ...
### monitor
- https://arthas.aliyun.com/doc/monitor.html
- **监控方法执行**
- 监控方法的成功数、失败数、用时
- 插件 `Monitor`
```js
[arthas@23600]$ monitor test.biz.BizService getUsers  -n 10  --cycle 10
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 2) cost in 26 ms, listenerId: 2
 timestamp         class                      method                      total    success  fail     avg-rt(  fail-ra
                                                                                                     ms)      te
----------------------------------------------------------------------------------------------------------------------
 2023-05-08 17:13  test.biz.BizService        getUsers                    9        5        4        0.17     44.44%
 :02

 timestamp         class                      method                      total    success  fail     avg-rt(  fail-ra
                                                                                                     ms)      te
----------------------------------------------------------------------------------------------------------------------
 2023-05-08 17:13  test.biz.BizService        getUsers                    7        7        0        0.07     0.00%
 :09

[arthas@23600]$
```

### stack
- https://arthas.aliyun.com/doc/stack.html
- **输出当前方法被调用的调用路径**
- 插件 `Stack`
```js
// 只监控 5 次
[arthas@21452]$ stack test.biz.BizService sleepMs  -n 5
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 1) cost in 23 ms, listenerId: 2
ts=2023-05-08 17:30:01;thread_name=http-nio-9066-exec-4;id=1e;is_daemon=true;priority=5;TCCL=org.springframework.boot.web.embedded.tomcat.TomcatEmbeddedWebappClassLoader@e9dc4d0
    @test.biz.BizService.sleepMs()
        at test.biz.BizController.sleepMs(BizController.java:58)
        at jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(NativeMethodAccessorImpl.java:-2)

// 根据执行时间来过滤
// 小于 20 ms，不打印 http://localhost:9066/api/biz/sleepMs?ms=1
// 大于 20 ms，打印   http://localhost:9066/api/biz/sleepMs?ms=30
[arthas@21452]$ stack test.biz.BizService sleepMs  -n 5 '#cost > 20'
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 1) cost in 23 ms, listenerId: 4
ts=2023-05-08 17:30:56;thread_name=http-nio-9066-exec-5;id=1f;is_daemon=true;priority=5;TCCL=org.springframework.boot.web.embedded.tomcat.TomcatEmbeddedWebappClassLoader@e9dc4d0
    @test.biz.BizService.sleepMs()
        at test.biz.BizController.sleepMs(BizController.java:58)
```

### trace
- https://arthas.aliyun.com/doc/trace.html
- **查看方法内部调用路径，并输出方法路径上的每个节点上耗时**
  - 被调用的方法的内部不监控
- 插件 `Trace`
```js
[arthas@22044]$ trace test.biz.BizService sleepMs  -n 5 --skipJDKMethod false
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 1) cost in 79 ms, listenerId: 1
`---ts=2023-05-08 17:40:56;thread_name=http-nio-9066-exec-3;id=1d;is_daemon=true;priority=5;TCCL=org.springframework.boot.web.embedded.tomcat.TomcatEmbeddedWebappClassLoader@41522537
    `---[45.1117ms] test.biz.BizService:sleepMs()
        +---[0.39% 0.178ms ] org.slf4j.Logger:info() #39
        +---[81.22% 36.639ms ] java.lang.Thread:sleep() #40
        +---[17.32% 7.8123ms ] test.biz.BizService:sleep5Ms() #41
        `---[0.42% 0.1905ms ] org.slf4j.Logger:info() #42

`---ts=2023-05-08 17:40:59;thread_name=http-nio-9066-exec-2;id=1c;is_daemon=true;priority=5;TCCL=org.springframework.boot.web.embedded.tomcat.TomcatEmbeddedWebappClassLoader@41522537
    `---[59.1906ms] test.biz.BizService:sleepMs()
        +---[0.17% 0.1006ms ] org.slf4j.Logger:info() #39
        +---[89.37% 52.9015ms ] java.lang.Thread:sleep() #40
        +---[9.99% 5.9125ms ] test.biz.BizService:sleep5Ms() #41
        `---[0.34% 0.1989ms ] org.slf4j.Logger:info() #42
```

### tt
- https://arthas.aliyun.com/doc/tt.html
  - 参考`条件表达式、解决方法重载、解决指定参数`，可指定对应的方法
- **方法执行的时空隧道**
  - 记录方法每次调用的入参和返回信息
  - **可重新发起调用**
- tt 是 TimeTunnel 的首字母
- 插件 `TimeTunnel Tt`
```js
// 正常访问 http://localhost:9066/api/biz/getUsers2?size=1
// 错误访问 http://localhost:9066/api/biz/getUsers2?size=-1
[arthas@22044]$ tt -t test.biz.BizService getUsers -n 5
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 2) cost in 31 ms, listenerId: 5
 INDEX       TIMESTAMP                    COST(ms)      IS-RET      IS-EXP      OBJECT                CLASS                                      METHOD
---------------------------------------------------------------------------------------------------------------------------------------------------------
 1008        2023-05-08 17:56:21          0.2564        false       true        0x13a7fdc3            BizService                                 getUsers
 1009        2023-05-08 17:56:23          0.1228        true        false       0x13a7fdc3            BizService                                 getUsers
 1010        2023-05-08 17:56:32          0.7039        true        false       0x13a7fdc3            BizService                                 getUsers
 1011        2023-05-08 17:56:36          0.0712        true        false       0x13a7fdc3            BizService                                 getUsers

/**
 * 检索调用记录 
 */
// 查看所有
[arthas@22044]$ tt -l
 INDEX       TIMESTAMP                    COST(ms)      IS-RET      IS-EXP      OBJECT                CLASS                                      METHOD
---------------------------------------------------------------------------------------------------------------------------------------------------------
 1000        2023-05-08 17:44:56          1.4117        true        false       0x13a7fdc3            BizService                                 getUsers
 1001        2023-05-08 17:45:08          0.0751        true        false       0x13a7fdc3            BizService                                 getUsers
 1002        2023-05-08 17:45:08          0.6442        true        false       0x13a7fdc3            BizService                                 getUsers
 1003        2023-05-08 17:45:18          0.0804        true        false       0x13a7fdc3            BizService                                 getUsers
Affect(row-cnt:12) cost in 1 ms.

// 查看指定方法的记录
[arthas@22044]$ tt -s 'method.name=="getUsers"'
 INDEX       TIMESTAMP                    COST(ms)      IS-RET      IS-EXP      OBJECT                CLASS                                      METHOD
---------------------------------------------------------------------------------------------------------------------------------------------------------
 1000        2023-05-08 17:44:56          1.4117        true        false       0x13a7fdc3            BizService                                 getUsers
 1001        2023-05-08 17:45:08          0.0751        true        false       0x13a7fdc3            BizService                                 getUsers
 1002        2023-05-08 17:45:08          0.6442        true        false       0x13a7fdc3            BizService                                 getUsers

// 查看指定的记录
[arthas@22044]$ tt -i 1000
 RE-INDEX       1000
 GMT-REPLAY     2023-05-08 17:58:52
 OBJECT         0x13a7fdc3
 CLASS          test.biz.BizService
 METHOD         getUsers
 PARAMETERS[0]  @Integer[1]
 PARAMETERS[1]  @String[id-]
 IS-RETURN      true
 IS-EXCEPTION   false
 COST(ms)       0.1371
 RETURN-OBJ     @ArrayList[
                    @UserDto[UserDto(id=id-1, name=test-1, age=33, remark=ts-17:58:52.582469, status=null)],
                ]
Time fragment[1000] successfully replayed 1 times.

// 查看指定报错的记录（异常栈记录的不是很好）
[arthas@22044]$ tt -i 1012
 INDEX            1012
 GMT-CREATE       2023-05-08 18:02:24
 COST(ms)         0.2651
 OBJECT           0x13a7fdc3
 CLASS            test.biz.BizService
 METHOD           getUsers
 IS-RETURN        false
 IS-EXCEPTION     true
 PARAMETERS[0]    @Integer[-1]
 PARAMETERS[1]    @String[id-]
                                                                                       ke0(Native Method)
                                                                     dAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
                                                             egatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)

                                                              ort.InvocableHandlerMethod.doInvoke(InvocableHandlerMethod.java:207)
                                                      hod.support.InvocableHandlerMethod.invokeForRequest(InvocableHandlerMethod.java:152)

// 重做一次调用。
// 使用 -p 参数。通过 --replay-times 指定 调用次数，通过 --replay-interval 指定多次调用间隔(单位 ms, 默认 1000ms)
[arthas@22044]$ tt -i 1012 -p
 RE-INDEX         1012
 GMT-REPLAY       2023-05-08 18:08:17
 OBJECT           0x13a7fdc3
 CLASS            test.biz.BizService
 METHOD           getUsers
 PARAMETERS[0]    @Integer[-1]
 PARAMETERS[1]    @String[id-]
 IS-RETURN        false
 IS-EXCEPTION     true


                                                                                       ke0(Native Method)
                                                                     dAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
                                                             egatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
Time fragment[1012] successfully replayed 1 times.

[arthas@22044]$
```

### watch
- https://arthas.aliyun.com/doc/watch.html
- **观测函数执行数据**
  - 观察范围为：入参、返回值、异常
- 插件 `Watch`
- 参数 `-x` 表示遍历深度，可以调整来打印具体的参数和结果内容，默认值是 1
```js
// 正常请求：http://localhost:9066/api/biz/getUsers2?size=1
[arthas@22044]$ watch test.biz.BizService getUsers '{params,returnObj,throwExp}'  -n 5  -x 3
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 2) cost in 28 ms, listenerId: 7
method=test.biz.BizService.getUsers location=AtExit
ts=2023-05-08 18:57:48; [cost=0.093ms] result=@ArrayList[
    @Object[][
        @Integer[1],
        @String[id-],
    ],
    @ArrayList[
        @UserDto[
            id=@String[id-1],
            name=@String[test-1],
            age=@Integer[33],
            remark=@String[ts-18:57:48.093312400],
            status=null,
        ],
    ],
    null,
]

// 错误请求：http://localhost:9066/api/biz/getUsers2?size=-1
[arthas@22044]$ watch test.biz.BizService getUsers '{params,returnObj,throwExp}'  -n 5  -x 3
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 2) cost in 23 ms, listenerId: 8
method=test.biz.BizService.getUsers location=AtExceptionExit
ts=2023-05-08 18:58:32; [cost=0.4093ms] result=@ArrayList[
    @Object[][
        @Integer[-1],
        @String[id-],
    ],
    null,
    java.lang.RuntimeException: 参数错误！size = -1
        at test.biz.BizService.getUsers(BizService.java:31)
        at test.biz.BizController.getUsers2(BizController.java:49)
        at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        ...

// 按照耗时进行过滤
// 进入   http://localhost:9066/api/biz/sleepMs?ms=50
// 进入   http://localhost:9066/api/biz/sleepMs?ms=20
// 不进入 http://localhost:9066/api/biz/sleepMs?ms=1
[arthas@22044]$ watch test.biz.BizService sleepMs '{params,returnObj,throwExp}'  -n 5  -x 3 '#cost > 20'
Press Q or Ctrl+C to abort.
Affect(class count: 1 , method count: 1) cost in 25 ms, listenerId: 9
method=test.biz.BizService.sleepMs location=AtExit
ts=2023-05-08 19:05:49; [cost=71.264501ms] result=@ArrayList[
    @Object[][
        @Integer[50],
    ],
    null,
    null,
]
method=test.biz.BizService.sleepMs location=AtExit
ts=2023-05-08 19:05:59; [cost=30.2032ms] result=@ArrayList[
    @Object[][
        @Integer[10],
    ],
    null,
    null,
]
```

### profiler
- https://arthas.aliyun.com/doc/profiler.html
- **生成火焰图**
- 插件 `Async Profiler`
- ***只支持 Linux 环境***
```js
[arthas@22044]$ profiler start --event cpu --interval 10000000
AsyncProfiler error: Current OS do not support AsyncProfiler, Only support Linux/Mac.
[arthas@22044]$ 
```