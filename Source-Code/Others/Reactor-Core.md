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

	// 创建一个指定范围的反应流，入口 ref: sign_demo_001
	public static Flux<Integer> range(int start, int count) {
		... // 0、1 判断
		return onAssembly(new FluxRange(start, count));	// ref: sign_c_010 | sign_m_010
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
			return onAssembly(new FluxLogFuseable<>(this, log));
		}
		return onAssembly(new FluxLog<>(this, log));	// 创建新的 Flux, ref: sign_c_101
	}
```

- `reactor.core.publisher.FluxLog`
```java
// sign_c_101
final class FluxLog<T> extends InternalFluxOperator<T, T> { // 继承 ref: sign_c_110

	final SignalPeek<T> log;

	FluxLog(Flux<? extends T> source, SignalPeek<T> log) {
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
	final OptimizableOperator<?, I> optimizableOperator;

	protected InternalFluxOperator(Flux<? extends I> source) {
		super(source);
		if (source instanceof OptimizableOperator) {
			OptimizableOperator<?, I> optimSource = (OptimizableOperator<?, I>) source;
			this.optimizableOperator = optimSource;
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
		...
		return onAssembly(new FluxFilter<>(this, p));	// 创建新的 Flux, ref: sign_c_201
	}
```

- `reactor.core.publisher.FluxFilter`
```java
// sign_c_201
final class FluxFilter<T> extends InternalFluxOperator<T, T> { // 继承 ref: sign_c_110

	final Predicate<? super T> predicate;

	FluxFilter(Flux<? extends T> source, Predicate<? super T> predicate) {
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
		...
		else {
			return onAssembly(new FluxSkip<>(this, skipped));	// 创建新的 Flux, ref: sign_c_301
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
		return collectSortedList() // ref: sign_m_401
			.flatMapIterable(identityFunction());	// 对排完序的 List 进行遍历，ref: sign_m_421
	}

	// sign_m_401
	public final Mono<List<T>> collectSortedList() {
		return collectSortedList(null); // ref: sign_m_402
	}

	// sign_m_402
	public final Mono<List<T>> collectSortedList(Comparator<? super T> comparator) {
		// 组装成 List，然后对 List 进行排序
		return collectList()	// ref: sign_m_403
				.doOnNext(list -> {
					list.sort(comparator);
				});
	}

	// sign_m_403
	public final Mono<List<T>> collectList() {
		...
		return Mono.onAssembly(new MonoCollectList<>(this));	// ref: sign_c_411
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
		return Flux.onAssembly(new MonoFlattenIterable<>(this, mapper, Integer.MAX_VALUE, Queues.one()));
	}

}
```

### 转换
- `reactor.core.publisher.Flux`
```java
	// 使用 ref: sign_demo_501
	public final <V> Flux<V> map(Function<? super T, ? extends V> mapper) {
		...
		return onAssembly(new FluxMap<>(this, mapper));	// 创建新的 Flux, ref: sign_c_501
	}
```

- `reactor.core.publisher.FluxMap`
```java
// sign_c_501
final class FluxMap<T, R> extends InternalFluxOperator<T, R> {

	final Function<? super T, ? extends R> mapper;

	FluxMap(Flux<? extends T> source, Function<? super T, ? extends R> mapper) {
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
			new LambdaSubscriber<>(consumer, errorConsumer, completeConsumer, null, initialContext)
		);
	}

	public final <E extends Subscriber<? super T>> E subscribeWith(E subscriber) {
		subscribe(subscriber);
		return subscriber;
	}
```