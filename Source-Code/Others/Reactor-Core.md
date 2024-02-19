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
    extends FluxOperator<I, O> 
    implements Scannable, OptimizableOperator<O, I> 
{ // 继承 ref: sign_c_120
    
    @Nullable
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
            //   调用顺序参考： sign_ord_001
            //   组装的链参考： sign_ch_001
            // publisher  为 FluxRange 实例
            subscriber = Operators.restoreContextOnSubscriberIfPublisherNonInternal(publisher, subscriber);
            publisher.subscribe(subscriber);    // 订阅，ref: sign_m_710
        } ... // catch
    }
```

#### 处理链
- 调用顺序如下(`sign_ord_001`)：
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

- 组装成链如下(`sign_ch_001`)：
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
                s.request(n);
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

#### 请求和消费
- 参考链：`sign_ch_001`

- `reactor.core.publisher.FluxMapFuseable.MapFuseableSubscriber`
```java
        // sign_m_810 拉数据请求
        @Override
        public void request(long n) {
            s.request(n);
        }
```