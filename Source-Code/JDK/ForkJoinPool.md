# JDK-ForkJoinPool


---
## JDK 版本
```js
openjdk version "17.0.12" 2024-07-16
OpenJDK Runtime Environment Temurin-17.0.12+7 (build 17.0.12+7)
OpenJDK 64-Bit Server VM Temurin-17.0.12+7 (build 17.0.12+7, mixed mode, sharing)
```


---
## 测试
```java
@Slf4j
public class MixTest {

    @Test
    public void testFJ() throws Exception {
        ForkJoinPool forkJoinPool = new ForkJoinPool();     // 初始化池，ref: sign_c_110 | sign_cm_210
        CountTask task = new CountTask(1, 10);              // 初始化自定义任务，ref: sign_demo_c_110
        // System.out.println(task.compute());              // 也可直接用默认的 fj 线程池执行
        Future<Integer> result = forkJoinPool.submit(task); // 提交任务，ref: sign_m_310
        System.out.println("结果：" + result.get());
    }

    // sign_demo_c_110  自定义任务
    public static class CountTask extends RecursiveTask<Integer> {  // 继承可递归任务，ref: sign_c_450
        private static final int THRESHOLD = 2;     // 阈值
        private final int start;
        private final int end;

        // sign_demo_cm_110
        public CountTask(int start, int end) {
            this.start = start;
            this.end = end;
        }

        // sign_demo_m_110  计算任务结果
        @Override
        public Integer compute() {
            int sum = 0;

            try {
                Thread.sleep(200L);
                System.out.printf("cur-thread: [%s].%n", Thread.currentThread().getName());
            } catch (InterruptedException e) { }

            // 如果任务足够小就计算任务
            boolean canCompute = (end - start) <= THRESHOLD;
            if (canCompute) {
                for (int i = start; i <= end; i++) {
                    sum += i;
                }
            } else {
                // 如果任务大于阈值，就分裂成两个子任务计算
                int middle = (start + end) / 2;
                CountTask leftTask = new CountTask(start, middle);
                CountTask rightTask = new CountTask(middle + 1, end);

                // 执行子任务
                leftTask.fork();    // ref: sign_m_422
                rightTask.fork();

                // 等待子任务执行完，并得到其结果
                int leftResult = leftTask.join();
                int rightResult = rightTask.join();

                // 合并子任务结果
                sum = leftResult + rightResult;
            }
            return sum;
        }
    }
}
```


---
## 原理
### 类结构
- `java.util.concurrent.ForkJoinPool`
```java
// sign_c_110  FJ 线程池
public class ForkJoinPool extends AbstractExecutorService {
    WorkQueue[] queues;                  // main registry
    final ForkJoinWorkerThreadFactory factory;
    final UncaughtExceptionHandler ueh;  // per-worker UEH
    final String workerNamePrefix;       // 创建工作线程的名称前缀
}
```

- `java.util.concurrent.ForkJoinPool.WorkQueue`
```java
    // sign_c_120  任务队列
    static final class WorkQueue {
        ForkJoinTask<?>[] array;            // 排队的任务；大小为 2 的幂
        final ForkJoinWorkerThread owner;   // 归属线程或共享时为 null
    }
```

- `java.util.concurrent.ForkJoinWorkerThread`
```java
// sign_c_110  FJ 工作线程
public class ForkJoinWorkerThread extends Thread {
    final ForkJoinPool pool;                // 此线程所在的池
    final ForkJoinPool.WorkQueue workQueue; // 工作窃取机制
}
```

### 初始化
- `java.util.concurrent.ForkJoinPool`
```java
// sign_c_210
public class ForkJoinPool extends AbstractExecutorService {
    
    // sign_cm_210  构造器
    public ForkJoinPool() {
        this(
            Math.min(MAX_CAP, Runtime.getRuntime().availableProcessors()),  // cpus: 20
            defaultForkJoinWorkerThreadFactory,         // 默认线程工厂，实例类 ref: sign_c_220
            null, false,
            0, MAX_CAP, // 0x7fff ==> 32767
            1, null, 
            DEFAULT_KEEPALIVE, TimeUnit.MILLISECONDS    // def: 60s
        );
    }

    // sign_cm_211  构造器
    public ForkJoinPool(
        int parallelism, ForkJoinWorkerThreadFactory factory, UncaughtExceptionHandler handler,
        ..., long keepAliveTime, TimeUnit unit
    ) {
        ...
        int p = parallelism;    // = cpus = 20
        this.factory = factory;
        this.ueh = handler;
        this.keepAlive = Math.max(unit.toMillis(keepAliveTime), TIMEOUT_SLOP);  // = 60s
        int size = 1 << (33 - Integer.numberOfLeadingZeros(p - 1));             // = 64
        ...

        this.registrationLock = new ReentrantLock();
        this.queues = new WorkQueue[size];
        String pid = Integer.toString(getAndAddPoolIds(1) + 1);                 // = 1
        this.workerNamePrefix = "ForkJoinPool-" + pid + "-worker-";
    }


    static {
        ...

        defaultForkJoinWorkerThreadFactory = new DefaultForkJoinWorkerThreadFactory();  // ref: sign_c_220
        ...

        ForkJoinPool tmp = ... new ForkJoinPool((byte) 0);
        common = tmp;   // 通用共公池
    }
}
```

- `java.util.concurrent.ForkJoinPool.DefaultForkJoinWorkerThreadFactory`
```java
    // sign_c_220  默认线程工厂
    static final class DefaultForkJoinWorkerThreadFactory implements ForkJoinWorkerThreadFactory {

        // sign_m_220  创建一个新线程
        public final ForkJoinWorkerThread newThread(ForkJoinPool pool) {
            return ... new ForkJoinWorkerThread(null, pool, true, false);   // ref: sign_cm_230
        }
    }
```

- `java.util.concurrent.ForkJoinWorkerThread`
```java
// sign_c_230
public class ForkJoinWorkerThread extends Thread {

    // sign_cm_230  构造器
    ForkJoinWorkerThread(
        ThreadGroup group, ForkJoinPool pool,
        boolean useSystemClassLoader, boolean isInnocuous
    ) {
        super(group, null, pool.nextWorkerThreadName(), 0L);
        UncaughtExceptionHandler handler = (this.pool = pool).ueh;      // 记录 pool 和 UEH
        this.workQueue = new ForkJoinPool.WorkQueue(this, isInnocuous); // 创建自己的任务队列
        super.setDaemon(true);  // 默认为守护线程
        if (handler != null)
            super.setUncaughtExceptionHandler(handler);
        if (useSystemClassLoader)
            super.setContextClassLoader(ClassLoader.getSystemClassLoader());
    }
}
```


### 启动线程
- `java.util.concurrent.ForkJoinPool`
```java
// sign_c_310
public class ForkJoinPool extends AbstractExecutorService {

    // sign_m_310  提交任务
    public <T> ForkJoinTask<T> submit(ForkJoinTask<T> task) {
        return externalSubmit(task);    // ref: sign_m_311
    }

    // sign_m_311
    private <T> ForkJoinTask<T> externalSubmit(ForkJoinTask<T> task) {
        Thread t; ForkJoinWorkerThread wt; WorkQueue q;
        ... // 校验参数

        if (((t = Thread.currentThread()) instanceof ForkJoinWorkerThread) &&   // 第一次进来，不是 FJ 线程
            (q = (wt = (ForkJoinWorkerThread)t).workQueue) != null &&           //            且队列为空
            wt.pool == this)
            q.push(task, this);
        else    // 走此逻辑
            externalPush(task); // ref: sign_m_312
        return task;
    }

    // sign_m_312
    final void externalPush(ForkJoinTask<?> task) {
        WorkQueue q;
        if ((q = submissionQueue()) == null)        // 查找或创建 WorkQueue
            throw ...;                  // shutdown or disabled
        else if (q.lockedPush(task))    // 添加到队列
            signalWork();               // 添加成功，则创建或唤醒线程，ref: sign_m_313
    }

    // sign_m_313  创建或唤醒线程
    final void signalWork() {
        for (long c = ctl; c < 0L;) {
            int sp, i; WorkQueue[] qs; WorkQueue v;
            if ((sp = (int)c & ~UNSIGNALLED) == 0) {    // no idle workers
                ...
                    createWorker();                     // 创建线程，ref: sign_m_313
                    break;
            }
            ... // 其他状态校验

            else {
                ...
                Thread vt = v.owner;
                ...
                    LockSupport.unpark(vt);             // 唤醒线程
                    break;
            }
        }
    }

    // sign_m_313  创建线程
    private boolean createWorker() {
        ForkJoinWorkerThreadFactory fac = factory;
        ForkJoinWorkerThread wt = null;
        try {
            if (fac != null
                && (wt = fac.newThread(this)) != null   // 创建 FJ 线程，ref: sign_m_220
            ) {
                wt.start();     // 启动线程
                return true;
            }
        }
        ... // catch
        return false;
    }

}
```

### 执行
- `java.util.concurrent.ForkJoinWorkerThread`
```java
// sign_c_410
public class ForkJoinWorkerThread extends Thread {

    // sign_m_410  任务运行体
    public void run() {
        ForkJoinPool p = pool;
        ForkJoinPool.WorkQueue w = workQueue;
        if (p != null && w != null) {   // 初始化失败时跳过
            try {
                p.registerWorker(w);
                onStart();              // (空实现，子类可覆盖)
                p.runWorker(w);         // (这是关键) 执行任务，ref: sign_m_420
            } 
            ... // catch ... finally 
        }
    }
}
```

- `java.util.concurrent.ForkJoinPool`
```java
// sign_c_420
public class ForkJoinPool extends AbstractExecutorService {

    // sign_m_420  顶层循环运行
    final void runWorker(WorkQueue w) {
        if (mode >= 0 && w != null) {           // skip on failed init
            w.config |= SRC;                    // mark as valid source
            int r = w.stackPred, src = 0;       // use seed from registerWorker
            do {
                r ^= r << 13; r ^= r >>> 17; r ^= r << 5;   // xorshift
            } while ((src = scan(w, src, r)) >= 0 ||        // 扫描并支行任务，ref: sign_m_421
                     (src = awaitWork(w)) == 0);
        }
    }

    // sign_m_421  扫描队列任务
    private int scan(WorkQueue w, int prevSrc, int r) {
        WorkQueue[] qs = queues;
        for (int step = (r >>> 16) | 1, i = n; i > 0; --i, r += step) {
            int j, cap, b; WorkQueue q; ForkJoinTask<?>[] a;
            if ((q = qs[j = r & (n - 1)]) != null && 
                (a = q.array) != null && (cap = a.length) > 0) {
                ...

                ForkJoinTask<?> t = WorkQueue.getSlot(a, k);
                ...
                else if (t != null && WorkQueue.casSlotToNull(a, k, t)) {
                    ...
                    w.topLevelExec(t, q);   // 顶层执行，ref: sign_m_430
                    return src;
                }
                ...
            }
        }
        ...
    }

    // sign_m_422  提交子任务
    public final ForkJoinTask<V> fork() {
        Thread t; ForkJoinWorkerThread w;
        if ((t = Thread.currentThread()) instanceof ForkJoinWorkerThread)
            (w = (ForkJoinWorkerThread)t).workQueue.push(this, w.pool);     // 添加到当前 FJ 线程队列里
        else
            ForkJoinPool.common.externalPush(this); // 用公共的 FJ 线程池追加任务
        return this;
    }
}
```

- `java.util.concurrent.ForkJoinPool.WorkQueue`
```java
    // sign_c_430
    static final class WorkQueue {

        // sign_m_430  顶层执行
        final void topLevelExec(ForkJoinTask<?> task, WorkQueue q) {
            int cfg = config, nstolen = 1;
            while (task != null) {
                task.doExec();  // 任务执行，ref: sign_m_440
                if ((task = nextLocalTask(cfg)) == null &&      // 先获取本地任务进行执行
                    q != null && (task = q.tryPoll()) != null)  // 再进行工作窃取处理：窃取 q 队列里的任务
                    ++nstolen;
            }
            nsteals += nstolen; // 对窃取数进行累加记录
            ...
        }
    }
```

- `java.util.concurrent.ForkJoinTask`
```java
// sign_c_440  FJ 任务
public abstract class ForkJoinTask<V> implements Future<V>, Serializable {

    volatile int status;

    // sign_m_440  执行任务
    final int doExec() {
        int s; boolean completed;
        if ((s = status) >= 0) {
            try {
                completed = exec(); // 执行，调用子类的实现，ref: sign_m_450
            } 
            ... // catch
            ... // 正常完成处理
        }
        return s;
    }
}
```

- `java.util.concurrent.RecursiveTask`
```java
// sign_c_450  可递归的带返回结果的任务
public abstract class RecursiveTask<V> extends ForkJoinTask<V> {

    // sign_m_450  执行任务
    protected final boolean exec() {
        result = compute();         // 计算，调用子类的实现，ref: sign_demo_m_110
        return true;
    }
}
```