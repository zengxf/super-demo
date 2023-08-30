## 功能点总结
- 根据指定的类检测其注解
- 层次化多个同类型的注解，会合并
- 判断注解类是否存在
- 注解属性可转 Map
- 注解属性强类型校验


## 单元测试
```java
public class MyAnnotationTest {
	@Test
	public void test() {
		AnnotatedElement ae = AppConfig.class;
		System.out.println(ae); // Class 是 AnnotatedElement 的实现类
		System.out.println("--------------------");

		AnnotationMetadata ann = AnnotationMetadata.introspect(AppConfig.class);
		System.out.println(ann.getClass().getName());
		System.out.println(ann);
		System.out.println("is-final: " + ann.isFinal()); // 判断 AppConfig 是不是 final 类
		System.out.println("is-annotated-2222: " + ann.isAnnotated(MyAnn2222.class.getName())); // 判断是不是存在
		System.out.println("--------------------");

		// Map 测试
		// getAnnotationAttributes() 是将所有指定类的注解属性合并到 Map
		{
			Map<String, Object> map = ann.getAnnotationAttributes(MyAnn1111.class.getName());
			System.out.println("MyAnn1111: " + map);
		}
		{
			Map<String, Object> map = ann.getAnnotationAttributes(MyAnn3333.class.getName());
			System.out.println("MyAnn3333: " + map);
		}
		{
			Map<String, Object> map = ann.getAnnotationAttributes(MyScans.class.getName()); // Map 包着的 value 是一个数组
			System.out.println("MyScans: " + map);
		}
		{
			Map<String, Object> map = ann.getAnnotationAttributes(MyScan.class.getName());  // 没有声明，返回 null
			System.out.println("MyScan: " + map);
		}
		System.out.println("--------------------");

		// 类型测试（类型校验严格）
		MergedAnnotations mAnn = ann.getAnnotations();
		System.out.println(mAnn.getClass().getName());
		System.out.println(mAnn);
		System.out.println("--------------------");

		{
			System.out.println("MyAnn1111 --------------");
			MergedAnnotation<?> ma = mAnn.get(MyAnn1111.class);
			System.out.println("ma-present: " + ma.isPresent());
			System.out.println("value: " + ma.getString("value"));
			// System.out.println("v-int: " + ma.getInt("value"));   // 类型不一致，会报错 IllegalArgumentException
			System.out.println("name: " + ma.getString("name"));
			System.out.println("clazz: " + ma.getClass("clazz"));
			// System.out.println("ma-xxx: " + ma.getString("xxx")); // 不存在属性，会报错 NoSuchElementException
		}
		{
			System.out.println("MyAnn3333 --------------");
			MergedAnnotation<?> ma = mAnn.get(MyAnn3333.class);
			System.out.println("ma-present: " + ma.isPresent());
			System.out.println("value: " + ma.getString("value"));
			System.out.println("name: " + ma.getString("name"));
			System.out.println("sign: " + ma.getString("sign"));
		}
		{
			System.out.println("MyScan --------------");
			MergedAnnotation<?> ma = mAnn.get(MyScan.class);
			System.out.println("ma-present: " + ma.isPresent());
			// System.out.println("ma-xxx: " + ma.getString("xxx")); // 注解本身不存在，会报错 NoSuchElementException
		}
	}

	@Test
	public void test2() {
		AnnotatedElement ae = AppConfig.class;
		ae.getDeclaredAnnotations(); // Debug 时，调用此方法后，Class 的 annotationData 才有会
		System.out.println(ae);
	}

	@MyAnnotationRoot
	@MyAnn1111(
			value = "AppConfig-B-8888"    // 会覆盖 @MetaAnnotationRoot 的注解设置
	)
	public static final class AppConfig {
	}


	@Retention(RetentionPolicy.RUNTIME)
	@MyAnn1111(
			value = "MyAnnotationRoot-V-2222",    // 会被外层的覆盖
			name = "MyAnnotationRoot-C-3333", clazz = LocalDate.class
	)
	@MyAnn3333(
			value = "MyAnnotationRoot-V-1111"
			//, sign = "MyAnnotationRoot-S-2222"
			// name = "MyAnnotationRoot-V-1111", // 可以不声明，声明的话，需要值是一样的
			// name = "MyAnnotationRoot-N-2222", // 值不一样会报错 AnnotationConfigurationException
	)
	@MyScans({@MyScan("---1---"), @MyScan("---2---"), @MyScan()})
	public @interface MyAnnotationRoot {
	}

	@Retention(RetentionPolicy.RUNTIME)
	@MyAnn2222
	public @interface MyAnn1111 {
		String value() default "def-D-1111";

		String name() default "def-D-0000";

		Class<?> clazz() default Object.class;
	}

	@Retention(RetentionPolicy.RUNTIME)
	public @interface MyAnn2222 {
	}

	@Retention(RetentionPolicy.RUNTIME)
	public @interface MyAnn3333 {
		@AliasFor("name")
		String value() default "1111";

		@AliasFor("value")              // 须要与 name 值相同，
		String name() default "1111";   // 否则 AnnotationConfigurationException must declare the same default value.

		String sign() default "3333";
	}

	@Retention(RetentionPolicy.RUNTIME)
	public @interface MyScans {
		MyScan[] value(); // 测试数组
	}

	@Retention(RetentionPolicy.RUNTIME)
	public @interface MyScan {
		String value() default "0000";
	}
}
```