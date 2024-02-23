## reactor-core
- GitHub: https://github.com/reactor/reactor-core


## 使用示例
- https://github.com/zengxf/small-frame-demo/blob/master/multi-thread/reactive-test/reactor-demo/src/main/java/cn/zxf/reactor_demo/flux/ComplexTest.java


## 参考
- [JDK-反应流](../JDK/反应流.md#原理)


## 原理
- 跟 JDK 反应流类似

### 初始化流
- `reactor.core.publisher.Flux`
```java
// sign_c_001 流式发布者 (类似 JDK 的 Flow.Publisher 实现)
public abstract class Flux<T> implements CorePublisher<T> {

    // sign_m_001 创建一个指定范围的反应流，入口 ref: sign_demo_001
    public static Flux<Integer> range(int start, int count) {
        ... // 0、1 判断
        return onAssembly(new FluxRange(start, count));    // ref: sign_c_010 | sign_m_010
    }

    // sign_m_010 组装钩子
    protected static <T> Flux<T> onAssembly(Flux<T> source) {
        Function<Publisher, Publisher> hook = Hooks.onEachOperatorHook;
        ... // 组装钩子函数
        return source;
    }
}
```

- `reactor.core.publisher.FluxRange`
```java
// sign_c_010 范围流
final class FluxRange extends Flux<Integer> implements Fuseable, SourceProducer<Integer> {
    final long start;
    final long end;
}
```

### 打印日志
- `reactor.core.publisher.Flux`
```java
    // 使用 ref: sign_demo_101
    public final Flux<T> log(String category) {
        return log(category, Level.INFO);
    }

    public final Flux<T> log(@Nullable String category, Level level, SignalType... options) {
        return log(category, level, false, options);
    }

    public final Flux<T> log(@Nullable String category,
            Level level,
            boolean showOperatorLine,
            SignalType... options
    ) {
        // 用来记录日志的
        SignalLogger<T> log = new SignalLogger<>(this, category, level, showOperatorLine, options);
        if (this instanceof Fuseable) {
            return onAssembly(new FluxLogFuseable<>(this, log)); // 创建新的 Flux, ref: sign_c_101
        }
        ...
    }
```

- `reactor.core.publisher.FluxLogFuseable`
```java
// sign_c_101
final class FluxLogFuseable<T> extends InternalFluxOperator<T, T> implements Fuseable { // 继承 ref: sign_c_110
    final SignalPeek<T> log;

    FluxLogFuseable(Flux<? extends T> source, SignalPeek<T> log) {
        super(source);
        this.log = log;
    }
}
```

- `reactor.core.publisher.InternalFluxOperator`
```java
// sign_c_110
abstract class InternalFluxOperator<I, O> 
    extends FluxOperator<I, O>  // 继承 ref: sign_c_120
    implements Scannable, OptimizableOperator<O, I> 
{
    final OptimizableOperator<?, I> optimizableOperator;    // sign_f_120 用于组装调用链 (相当于上个节点)

    protected InternalFluxOperator(Flux<? extends I> source) {
        super(source);
        if (source instanceof OptimizableOperator) {
            OptimizableOperator<?, I> optimSource = (OptimizableOperator<?, I>) source;
            this.optimizableOperator = optimSource;         // 记录链, ref: sign_f_120
        }
        ...
    }
}
```

- `reactor.core.publisher.FluxOperator`
```java
// sign_c_120
public abstract class FluxOperator<I, O> extends Flux<O> implements Scannable {
    protected final Flux<? extends I> source;

    protected FluxOperator(Flux<? extends I> source) {
        this.source = Objects.requireNonNull(source);
    }
}
```

### 过滤
- `reactor.core.publisher.Flux`
```java
    // 使用 ref: sign_demo_201
    public final Flux<T> filter(Predicate<? super T> p) {
        if (this instanceof Fuseable) {
            return onAssembly(new FluxFilterFuseable<>(this, p));   // 创建新的 Flux, ref: sign_c_201
        }
        ...
    }
```

- `reactor.core.publisher.FluxFilterFuseable`
```java
// sign_c_201
final class FluxFilterFuseable<T> extends InternalFluxOperator<T, T> implements Fuseable { // 继承 ref: sign_c_110
    final Predicate<? super T> predicate;

    FluxFilterFuseable(Flux<? extends T> source, Predicate<? super T> predicate) {
        super(source);
        this.predicate = Objects.requireNonNull(predicate, "predicate");
    }
}
```

### 跳过
- `reactor.core.publisher.Flux`
```java
    // 使用 ref: sign_demo_301
    public final Flux<T> skip(long skipped) {
        ... // skipped 为 0
        else {
            return onAssembly(new FluxSkip<>(this, skipped));    // 创建新的 Flux, ref: sign_c_301
        }
    }
```

- `reactor.core.publisher.FluxSkip`
```java
// sign_c_301
final class FluxSkip<T> extends InternalFluxOperator<T, T> {
    final long n;

    FluxSkip(Flux<? extends T> source, long n) {
        super(source);
        ...
        this.n = n;
    }
}
```

### 排序
- `reactor.core.publisher.Flux`
```java
    // 使用 ref: sign_demo_401
    public final Flux<T> sort() {
        return collectSortedList()  // ref: sign_m_401
            .flatMapIterable(       // 对排完序的 List 进行遍历，ref: sign_m_421
                identityFunction()
            );
    }

    // sign_m_401
    public final Mono<List<T>> collectSortedList() {
        return collectSortedList(null); // ref: sign_m_402
    }

    // sign_m_402
    public final Mono<List<T>> collectSortedList(Comparator<? super T> comparator) {
        // 组装成 List，然后对 List 进行排序
        return collectList()    // ref: sign_m_403
                .doOnNext(      // ref: sign_m_422
                    list -> {
                        list.sort(comparator);
                    }
                );
    }

    // sign_m_403
    public final Mono<List<T>> collectList() {
        ...
        return Mono.onAssembly(new MonoCollectList<>(this));    // ref: sign_c_411
    }
```

- `reactor.core.publisher.MonoCollectList`
```java
// sign_c_411
final class MonoCollectList<T> extends MonoFromFluxOperator<T, List<T>> implements Fuseable {
    MonoCollectList(Flux<? extends T> source) {
        super(source);
    }
}
```

- `reactor.core.publisher.Mono`
```java
// sign_c_421
public abstract class Mono<T> implements CorePublisher<T> {
    // sign_m_421 组装成 Flux
    public final <R> Flux<R> flatMapIterable(Function<? super T, ? extends Iterable<? extends R>> mapper) {
        return Flux.onAssembly(
            // 创建一个迭代器，ref: sign_c_422 | sign_cm_422
            new MonoFlattenIterable<>(this, mapper, Integer.MAX_VALUE, Queues.one())
        );
    }

    // sign_m_422
    public final Mono<T> doOnNext(Consumer<? super T> onNext) {
        Objects.requireNonNull(onNext, "onNext");
        return doOnSignal(this, null, onNext, null, null);  // ref: sign_m_423
    }

    // sign_m_423
    static <T> Mono<T> doOnSignal(
        Mono<T> source,
        @Nullable Consumer<? super Subscription> onSubscribe,
        @Nullable Consumer<? super T> onNext,
        @Nullable LongConsumer onRequest,
        @Nullable Runnable onCancel
    ) {
        if (source instanceof Fuseable) {
            return onAssembly(
                // ref: sign_c_423 | sign_cm_423
                new MonoPeekFuseable<>(source, onSubscribe, onNext, onRequest, onCancel)
            );
        }
        ...
    }
}
```

- `reactor.core.publisher.MonoFlattenIterable`
```java
// sign_c_422 迭代器
final class MonoFlattenIterable<T, R> extends FluxFromMonoOperator<T, R> implements Fuseable {
    ...

    // sign_cm_422
    MonoFlattenIterable(Mono<? extends T> source, ... ) {
        super(source);
        ...
    }
}
```

- `reactor.core.publisher.MonoPeekFuseable`
```java
// sign_c_423
final class MonoPeekFuseable<T> extends InternalMonoOperator<T, T> implements Fuseable, SignalPeek<T> {
    ...

    // sign_cm_423
    MonoPeekFuseable(Mono<? extends T> source, ... ) {
        super(source);
        ...
    }
}
```

### 转换
- `reactor.core.publisher.Flux`
```java
    // 使用 ref: sign_demo_501
    public final <V> Flux<V> map(Function<? super T, ? extends V> mapper) {
        if (this instanceof Fuseable) {
            return onAssembly(new FluxMapFuseable<>(this, mapper)); // 创建新的 Flux, ref: sign_c_501
        }
        ...
    }
```

- `reactor.core.publisher.FluxMapFuseable`
```java
// sign_c_501
final class FluxMapFuseable<T, R> extends InternalFluxOperator<T, R> implements Fuseable {
    final Function<? super T, ? extends R> mapper;

    FluxMapFuseable(Flux<? extends T> source, Function<? super T, ? extends R> mapper) {
        super(source);
        this.mapper = Objects.requireNonNull(mapper, "mapper");
    }
}
```

### 订阅并消费
- `reactor.core.publisher.Flux`
```java
    // 使用 ref: sign_demo_601
    public final Disposable subscribe(Consumer<? super T> consumer) {
        ...
        return subscribe(consumer, null, null);
    }

    public final Disposable subscribe(
            @Nullable Consumer<? super T> consumer,
            @Nullable Consumer<? super Throwable> errorConsumer,
            @Nullable Runnable completeConsumer
    ) {
        return subscribe(consumer, errorConsumer, completeConsumer, (Context) null);
    }

    public final Disposable subscribe(
            @Nullable Consumer<? super T> consumer,
            @Nullable Consumer<? super Throwable> errorConsumer,
            @Nullable Runnable completeConsumer,
            @Nullable Context initialContext
    ) {
        return subscribeWith(
            // 包装成 Lambda 订阅者，用于订阅
            new LambdaSubscriber<>(consumer, errorConsumer, completeConsumer, null, initialContext)
        );
    }

    public final <E extends Subscriber<? super T>> E subscribeWith(E subscriber) {
        subscribe(subscriber);
        return subscriber;
    }

    @Override
    public final void subscribe(Subscriber<? super T> actual) {
        CorePublisher publisher = Operators.onLastAssembly(this);       // 组装发布源
        CoreSubscriber subscriber = Operators.toCoreSubscriber(actual); // 组装订阅者

        ...

        try {
            if (publisher instanceof OptimizableOperator) {
                OptimizableOperator operator = (OptimizableOperator) publisher;
                while (true) {
                    subscriber = operator.subscribeOrReturn(subscriber);
                    if (subscriber == null) {
                        return;
                    }
                    OptimizableOperator newSource = operator.nextOptimizableSource();
                    if (newSource == null) {
                        // 最后一步会进入此，读取到 FluxRange 实例，此实例组装参考： sign_m_001
                        publisher = operator.source();
                        break;
                    }
                    operator = newSource;
                }
            }

            // subscriber 为 PeekFuseableConditionalSubscriber 实例。
            //   调用顺序参考： sign_inv_001
            //   组装的链参考： sign_ch_001
            // publisher  为 FluxRange 实例
            subscriber = Operators.restoreContextOnSubscriberIfPublisherNonInternal(publisher, subscriber);
            publisher.subscribe(subscriber);    // 订阅，ref: sign_m_710
        } ... // catch
    }
```

#### 处理链
- 调用顺序(`sign_inv_001`)：
```java
1. reactor.core.publisher.FluxMapFuseable #subscribeOrReturn        // 转换
    -> MapFuseableSubscriber
2. reactor.core.publisher.MonoFlattenIterable #subscribeOrReturn    // 排序
    -> FlattenIterableSubscriber
3. reactor.core.publisher.MonoPeekFuseable #subscribeOrReturn       // 排序
    -> PeekFuseableSubscriber
4. reactor.core.publisher.MonoCollectList #subscribeOrReturn        // 排序
    -> MonoCollectListSubscriber
5. reactor.core.publisher.FluxSkip #subscribeOrReturn               // 跳过
    -> SkipSubscriber
6. reactor.core.publisher.FluxFilterFuseable #subscribeOrReturn     // 过滤
    -> FilterFuseableSubscriber
7. reactor.core.publisher.FluxLogFuseable #subscribeOrReturn        // 日志
    -> PeekFuseableConditionalSubscriber
```

- 组装成链(`sign_ch_001`)：
```java
subscriber =>
  -> PeekFuseableConditionalSubscriber(actual) 
  -> FilterFuseableSubscriber(actual) 
  -> SkipSubscriber(actual) 
  -> MonoCollectListSubscriber(actual) 
  -> PeekFuseableSubscriber(actual) 
  -> FlattenIterableSubscriber(actual) 
  -> MapFuseableSubscriber(actual) 
  -> LambdaSubscriber(consumer)     // 自己的业务逻辑

// 生成数据之后调用下游的 onNext(t) 进行传递
```

#### 订阅
- 参考链：`sign_ch_001`

- `reactor.core.publisher.FluxRange`
```java
    // sign_m_710 订阅
    @Override
    public void subscribe(CoreSubscriber<? super Integer> actual) {
        long st = start;
        long en = end;

        ...
        
        if (actual instanceof ConditionalSubscriber) {
            // actual 为 PeekFuseableConditionalSubscriber 实例，会进入此逻辑块
            // 订阅传递，ref: sign_m_720
            actual.onSubscribe(new RangeSubscriptionConditional((ConditionalSubscriber<? super Integer>) actual, st, en));
            return;
        }
        ...
    }
```

- `reactor.core.publisher.FluxPeekFuseable.PeekFuseableConditionalSubscriber`
```java
        // sign_m_720
        @Override
        public void onSubscribe(Subscription s) {
            // s:       RangeSubscriptionConditional 实例
            // actual:  FilterFuseableSubscriber 实例
            if(Operators.validate(this.s, s)) {
                // parent:  SignalLogger 实例
                final Consumer<? super Subscription> subscribeHook = parent.onSubscribeCall();
                if (subscribeHook != null) {
                    try {
                        subscribeHook.accept(s); // 打印 log
                    } ... // catch 
                }
                this.s = (QueueSubscription<T>) s;
                actual.onSubscribe(this);   // ref: sign_m_730
            }
        }
```

- `reactor.core.publisher.FluxFilterFuseable.FilterFuseableSubscriber`
```java
        // sign_m_730
        @Override
        public void onSubscribe(Subscription s) {
            // s:       PeekFuseableConditionalSubscriber 实例
            // actual:  SkipSubscriber 实例
            if (Operators.validate(this.s, s)) {
                this.s = (QueueSubscription<T>) s;
                actual.onSubscribe(this);   // ref: sign_m_740
            }
        }
```

- `reactor.core.publisher.FluxSkip.SkipSubscriber`
```java
        // sign_m_740
        @Override
        public void onSubscribe(Subscription s) {
            // s:       FilterFuseableSubscriber 实例
            // actual:  MonoCollectListSubscriber 实例
            if (Operators.validate(this.s, s)) {
                this.s = s;
                long n = remaining;         // demo: remaining = 1
                actual.onSubscribe(this);   // ref: sign_m_750
                s.request(n);   // 后续已无实际操作
            }
        }
```

- `reactor.core.publisher.MonoCollectList.MonoCollectListSubscriber`
```java
    static final class MonoCollectListSubscriber<T> extends Operators.BaseFluxToMonoOperator<T, List<T>> {
    }

    static abstract class BaseFluxToMonoOperator<I, O> implements InnerOperator<I, O>, Fuseable, QueueSubscription<I> {
        // sign_m_750
        @Override
        public void onSubscribe(Subscription s) {
            // s:       SkipSubscriber 实例
            // actual:  PeekFuseableSubscriber 实例
            if (Operators.validate(this.s, s)) {
                this.s = s;
                actual.onSubscribe(this);   // ref: sign_m_760
            }
        }
    }
```

- `reactor.core.publisher.FluxPeekFuseable.PeekFuseableSubscriber`
```java
        // sign_m_760
        @Override
        public void onSubscribe(Subscription s) {
            // s:       MonoCollectListSubscriber 实例
            // actual:  FlattenIterableSubscriber 实例
            if(Operators.validate(this.s, s)) {
                final Consumer<? super Subscription> subscribeHook = parent.onSubscribeCall();
                if (subscribeHook != null) {
                    ... // subscribeHook 为 null，不进入此逻辑块
                }
                this.s = (QueueSubscription<T>) s;
                actual.onSubscribe(this);   // ref: sign_m_770
            }
        }
```

- `reactor.core.publisher.FluxFlattenIterable.FlattenIterableSubscriber`
```java
        // sign_m_770
        @Override
        public void onSubscribe(Subscription s) {
            // s:       PeekFuseableSubscriber 实例
            // actual:  MapFuseableSubscriber 实例
            if (Operators.validate(this.s, s)) {
                this.s = s;

                if (s instanceof QueueSubscription) {
                    QueueSubscription<T> qs = (QueueSubscription<T>) s;
                    int m = qs.requestFusion(Fuseable.ANY); // m 为 0

                    if (m == Fuseable.SYNC) {       // SYNC = 1
                    else if (m == Fuseable.ASYNC)   // ASYNC = 2
                        ... // 不进入此逻辑块
                        return;
                    }
                }

                queue = queueSupplier.get();    // 返回 OneQueue
                actual.onSubscribe(this);       // ref: sign_m_780
                /**
                 * prefetch 为 Integer.MAX_VALUE
                 * unboundedOrPrefetch(i) 返回 Long.MAX_VALUE
                 * 请求，参考： sign_m_830
                 */
                s.request(Operators.unboundedOrPrefetch(prefetch));
            }
        }
```

- `reactor.core.publisher.FluxMapFuseable.MapFuseableSubscriber`
```java
        // sign_m_780
        @Override
        public void onSubscribe(Subscription s) {
            // s:       FlattenIterableSubscriber 实例
            // actual:  LambdaSubscriber 实例
            if (Operators.validate(this.s, s)) {
                this.s = (QueueSubscription<T>) s;
                actual.onSubscribe(this);   // sign_m_790
            }
        }
```

- `reactor.core.publisher.LambdaSubscriber`
```java
    // sign_m_790
    @Override
    public final void onSubscribe(Subscription s) {
        // s:       MapFuseableSubscriber 实例
        if (Operators.validate(subscription, s)) {
            this.subscription = s;
            if (subscriptionConsumer != null) {
                ... // subscriptionConsumer 为 null，不进入此逻辑块
            }
            else {
                // 进入此逻辑块
                s.request(Long.MAX_VALUE);  // 拉数据请求，ref: sign_m_810
            }
        }
    }
```

#### 请求
- 参考链：`sign_ch_001`

- `reactor.core.publisher.FluxMapFuseable.MapFuseableSubscriber`
```java
        // sign_m_810 拉数据请求
        @Override
        public void request(long n) {
            // s:  FlattenIterableSubscriber
            s.request(n);   // ref: sign_m_820
        }
```

- `reactor.core.publisher.FluxFlattenIterable.FlattenIterableSubscriber`
  - **链中断**
```java
        // sign_m_820
        @Override
        public void request(long n) {
            if (Operators.validate(n)) {
                ... // 没有实质性的处理 (可以理解为链中断，后续由上游发起调用)
                drain(null);
            }
        }
```

- `reactor.core.publisher.FluxPeekFuseable.PeekFuseableSubscriber`
```java
        // sign_m_830
        @Override
        public void request(long n) {
            // s:  MonoCollectListSubscriber
            final LongConsumer requestHook = parent.onRequestCall();
            if (requestHook != null) {
                ... // requestHook 为 null，不进入此逻辑
            }
            s.request(n);   // ref: sign_m_840
        }
```

- `reactor.core.publisher.MonoCollectList.MonoCollectListSubscriber`
```java
        // sign_m_840
        // 父类方法 reactor.core.publisher.Operators.BaseFluxToMonoOperator #request
        @Override
        public void request(long n) {
            // s:  SkipSubscriber
            if (!hasRequest) {
                hasRequest = true;

                final int state = this.state;
                ...

                if (STATE.compareAndSet(this, state, state | 1)) {
                    if (state == 0) {
                        // 进入此逻辑
                        s.request(Long.MAX_VALUE);  // ref: sign_m_850
                    }
                    else { ... }
                }
            }
        }
```

- `reactor.core.publisher.FluxSkip.SkipSubscriber`
```java
        // sign_m_850
        @Override
        public void request(long n) {
            // s:  FilterFuseableSubscriber
            s.request(n);   // ref: sign_m_860
        }
```

- `reactor.core.publisher.FluxFilterFuseable.FilterFuseableSubscriber`
```java
        // sign_m_860
        @Override
        public void request(long n) {
            // s:  PeekFuseableConditionalSubscriber
            s.request(n);   // ref: sign_m_870
        }
```

- `reactor.core.publisher.FluxPeekFuseable.PeekFuseableConditionalSubscriber`
```java
        // sign_m_870
        @Override
        public void request(long n) {
            // s:  RangeSubscriptionConditional

            final LongConsumer requestHook = parent.onRequestCall();
            ... // parent 是 SignalLogger 实例，进行日志打印

            s.request(n);   // ref: sign_m_880
        }
```

- `reactor.core.publisher.FluxRange.RangeSubscriptionConditional`
```java
        // sign_m_880
        @Override
        public void request(long n) {
            if (Operators.validate(n)) {
                if (Operators.addCap(REQUESTED, this, n) == 0) {
                    if (n == Long.MAX_VALUE) {
                        // 进入此逻辑
                        fastPath(); // 生成"序列"数据给下游消费，ref: sign_m_881
                    } ... // else
                }
            }
        }

        // sign_m_881 生成"序列"数据给下游消费
        void fastPath() {
            // actual:  PeekFuseableConditionalSubscriber
            final long e = end;                 // end 为 11
            final ConditionalSubscriber<? super Integer> a = actual;

            for (long i = index; i != e; i++) { // index 为 1
                ... // 取消判断处理
                a.tryOnNext((int) i);   // 给下游消费，ref: sign_m_910 
            }

            ... // 取消判断处理
            // sign_cb_880
            a.onComplete(); // ref: sign_m_950
        }
```

#### 消费
- `reactor.core.publisher.FluxPeekFuseable.PeekFuseableConditionalSubscriber`
```java
        // sign_m_910 消费
        @Override
        public boolean tryOnNext(T t) {
            // actual:  FilterFuseableSubscriber

            ... // done 判断并返回

            final Consumer<? super T> nextHook = parent.onNextCall();
            ... // parent 是 SignalLogger 实例，进行日志打印

            return actual.tryOnNext(t); // ref: sign_m_920
        }
```

- `reactor.core.publisher.FluxFilterFuseable.FilterFuseableSubscriber`
```java
        // sign_m_920
        @Override
        public boolean tryOnNext(T t) {
            // actual:  SkipSubscriber

            ... // done 判断并返回

            boolean b;
            try {
                b = predicate.test(t);
            } ... // catch
            if (b) {
                actual.onNext(t);   // 判断通过，传给下游消费，ref: sign_m_930
                return true;
            }
            
            ... // 判断不通过，丢弃处理
        }
```

- `reactor.core.publisher.FluxSkip.SkipSubscriber`
```java
        // sign_m_930
        @Override
        public void onNext(T t) {
            // actual:  SkipSubscriber
            long r = remaining;     // demo 设置 remaining 为 1
            if (r == 0L) {
                actual.onNext(t);   // 跳过 n 个之后，传给下游消费，ref: sign_m_940
            }
            else {
                Operators.onDiscard(t, ctx);    // 丢弃处理
                remaining = r - 1;  // 对跳过数进行计数处理
            }
        }
```

- `reactor.core.publisher.MonoCollectList.MonoCollectListSubscriber`
  - **链中断**
```java
        // sign_m_940
        @Override
        public void onNext(T t) {
            // actual:  SkipSubscriber

            ... // done 判断并返回

            final List<T> l;
            synchronized (this) {
                l = list;
                if (l != null) {
                    /**
                     * list 不为空，进入此逻辑，缓存元素 (链中断，后续由上游传递)。
                     * 集合排序会在上游 onComplete() 时处理，ref: sign_cb_880
                     *     并将元素传递给下游，ref: sign_m_950
                     */
                    l.add(t);
                    return;
                }
            }

            Operators.onDiscard(t, actual.currentContext());
        }
```

- `reactor.core.publisher.FluxPeekFuseable.PeekFuseableConditionalSubscriber#onComplete`
```java
        // sign_m_950
        @Override
        public void onComplete() {
            // actual:  FilterFuseableSubscriber
            if (done) { return; }

            if (sourceMode == ASYNC) { ... }
            else { // 进入此逻辑
                final Runnable completeHook = parent.onCompleteCall();
                ... // parent 是 SignalLogger 实例，进行日志打印

                done = true;
                actual.onComplete();    // ref: sign_m_960

                ... // 完成后的钩子处理
            }
        }
```

- `reactor.core.publisher.FluxFilterFuseable.FilterFuseableSubscriber`
```java
        // sign_m_960
        @Override
        public void onComplete() {
            // actual:  SkipSubscriber
            if (done) { return; }

            done = true;
            actual.onComplete();    // ref: sign_m_970
        }
```

- `reactor.core.publisher.FluxSkip.SkipSubscriber`
```java
        // sign_m_970
        @Override
        public void onComplete() {
            // actual:  MonoCollectListSubscriber
            actual.onComplete();    // ref: sign_m_980
        }
```

- `reactor.core.publisher.MonoCollectList.MonoCollectListSubscriber`
```java
        // sign_m_980
        @Override
        public void onComplete() {
            // actual:  PeekFuseableSubscriber
            if (done) { return; }

            done = true;
            completePossiblyEmpty();    // ref: sign_m_981
        }

        // sign_m_981
        final void completePossiblyEmpty() {
            if (hasRequest) { // 进入此逻辑
                final O value = accumulatedValue(); // 获取上面组装的 List
                if (value == null) { return; }

                this.actual.onNext(value);  // 传给下游消费，ref: sign_m_990
                this.actual.onComplete();   // 后续已无实际操作
                return;
            }
            ...
        }
```

- `reactor.core.publisher.FluxPeekFuseable.PeekFuseableSubscriber`
```java
        // sign_m_990 消费
        @Override
        public void onNext(T t) {
            // actual:  FlattenIterableSubscriber
            if (sourceMode == ASYNC) { ... }
            else { // 进入此逻辑
                if (done) { ... return; }

                final Consumer<? super T> nextHook = parent.onNextCall();
                ... // 处理排序 *.Flux #collectSortedList(Comparator<T>)

                actual.onNext(t);   // ref: sign_m_9A0
            }
        }
```

- `reactor.core.publisher.FluxFlattenIterable.FlattenIterableSubscriber`
```java
        // sign_m_9A0
        @Override
        public void onNext(T t) {
            if (fusionMode != Fuseable.ASYNC) {
                if (!queue.offer(t)) {
                    ... // queue 能添加 t (即上面的 List)，不进入此逻辑
                    return;
                }
            }
            drain(t);   // ref: sign_m_9A1
        }

        // sign_m_9A1
        void drain(@Nullable T dataSignal) {
            ...
            if (fusionMode == SYNC) { drainSync(); }
            else { // 进入此逻辑
                drainAsync();   // ref: sign_m_9A2
            }
        }

        // sign_m_9A2
        void drainAsync() {
            // actual:  MapFuseableSubscriber
            final Subscriber<? super R> a = actual;
            final Queue<T> q = queue;
            Spliterator<? extends R> sp = current;

            for (; ; ) {
                if (sp == null) {   // 进入此逻辑
                    ...

                    T t = q.poll();   // 获取上面添加的 list
                    ...

                    Iterable<? extends R> iterable = mapper.apply(t); // 获取迭代器
                    sp = iterable.spliterator();
                    ...
                }

                if (sp != null) {   // 上面填充 sp 之后，进入此逻辑
                    ...
                    while (e != r) {    // e != r 为 true
                        ...
                        R   v = Objects.requireNonNull(
                                    next(sp),   // 获取元素
                                    "iterator returned null"
                                );
                        ...

                        a.onNext(v);    // 给下游消费，ref: sign_m_9B0
                        ...

                        boolean b = hasNext(sp);    // 判断是否还有元素
                        ... // 没有元素时中断 while 循环
                    }
                    ...
                }
                ... // 遍历完后，退出 for 循环
            }
        }
```

- `reactor.core.publisher.FluxMapFuseable.MapFuseableSubscriber`
```java
        // sign_m_9B0
        @Override
        public void onNext(T t) {
            if (sourceMode == ASYNC) { actual.onNext(null); }
            else { // 进入此逻辑
                if (done) { ... return; }
                
                R v;
                try {
                    v = mapper.apply(t);    // map 转换，ref: sign_demo_501
                    ... // v 不能为 null 校验
                } ... // catch 

                actual.onNext(v);   // ref: sign_m_9C0
            }
        }
```

- `reactor.core.publisher.LambdaSubscriber`
```java
    // sign_m_9C0
    @Override
    public final void onNext(T x) {
        try {
            if (consumer != null) {
                consumer.accept(x);         // 消费，ref: sign_demo_601
            }
        } ... // catch 
    }
```

### 总结
- **处理链关键点**
  - 在 `sign_m_881` 生成"序列"数据给下游消费
  - 在 `sign_m_940` 收集元素到 List
  - 在 `sign_cb_880` 调用 onComplete() 将 List 传给下游
  - 在 `sign_m_990` 进入 List 排序
  - 排序完后，在 `sign_m_9A2` 遍历元素，并传给下游