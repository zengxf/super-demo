# Dubbo-集成到-Spring


---
## 启用-Dubbo
- 关键注解：**@EnableDubbo**

- `org.apache.dubbo.config.spring.context.annotation.EnableDubbo`
```java
// sign_c_110  启用 Dubbo 关键注解
@EnableDubboConfig
@DubboComponentScan // 添加扫描包注解，ref: sign_c_210
public @interface EnableDubbo {
}
```


---
## 扫描包
- `org.apache.dubbo.config.spring.context.annotation.DubboComponentScan`
```java
// sign_c_210  扫描包注解
@Import(DubboComponentScanRegistrar.class) // 导入扫描 Bean 注册器，ref: sign_c_220
public @interface DubboComponentScan {
}
```

- `org.apache.dubbo.config.spring.context.annotation.DubboComponentScanRegistrar`
```java
// sign_c_220  扫描 Bean 注册器
public class DubboComponentScanRegistrar implements ImportBeanDefinitionRegistrar {

    // sign_m_220  注册 Bean
    @Override
    public void registerBeanDefinitions(AnnotationMetadata importingClassMetadata, BeanDefinitionRegistry registry) {
        DubboSpringInitializer.initialize(registry); // 初始化 Dubbo Bean, ref: sign_sm_310
        Set<String> packagesToScan = getPackagesToScan(importingClassMetadata);
        registerServiceAnnotationPostProcessor(packagesToScan, registry); // ref: sign_m_221
    }

    // sign_m_221  注册扫描 @DubboService 注解的 Bean
    private void registerServiceAnnotationPostProcessor(Set<String> packagesToScan, BeanDefinitionRegistry registry) {
        BeanDefinitionBuilder builder = BeanDefinitionBuilder.rootBeanDefinition(
            ServiceAnnotationPostProcessor.class        // 创建扫描类 Bean 定义，ref: sign_c_230
        );
        builder.addConstructorArgValue(packagesToScan); // 设置构造参数，ref: sign_cm_230
        builder.setRole(BeanDefinition.ROLE_INFRASTRUCTURE);
        AbstractBeanDefinition beanDefinition = builder.getBeanDefinition();
        BeanDefinitionReaderUtils.registerWithGeneratedName(beanDefinition, registry); // 将 Bean 定义注册进去
    }
}
```

- `org.apache.dubbo.config.spring.beans.factory.annotation.ServiceAnnotationPostProcessor`
```java
// sign_c_230  扫描 @DubboService 注解
public class ServiceAnnotationPostProcessor 
    implements BeanDefinitionRegistryPostProcessor, ..., ApplicationContextAware, ...
{
    private Set<String> resolvedPackagesToScan;
    private BeanDefinitionRegistry registry;

    // sign_cm_230  构造器
    public ServiceAnnotationPostProcessor(Set<String> packagesToScan) {
        this.packagesToScan = packagesToScan;
    }

    // sign_m_230
    @Override
    public void postProcessBeanDefinitionRegistry(BeanDefinitionRegistry registry) throws BeansException {
        this.registry = registry;
        scanServiceBeans(resolvedPackagesToScan, registry);  // sign_m_231
    }

    // sign_m_231
    private void scanServiceBeans(Set<String> packagesToScan, BeanDefinitionRegistry registry) {
        scanned = true;
        ... // 校验 packagesToScan

        DubboClassPathBeanDefinitionScanner scanner = // ref: sign_c_240
                new DubboClassPathBeanDefinitionScanner(registry, environment, resourceLoader);

        BeanNameGenerator beanNameGenerator = resolveBeanNameGenerator(registry);
        scanner.setBeanNameGenerator(beanNameGenerator);
        for (Class<? extends Annotation> annotationType : serviceAnnotationTypes) {
            // 查找带 @DubboService @...dubbo...Service 注解的类
            scanner.addIncludeFilter(new AnnotationTypeFilter(annotationType));
        }
        ...

        for (String packageToScan : packagesToScan) {
            ... // 避免重复扫描判断处理

            scanner.scan(packageToScan); // 扫描包

            // 获取扫描出的 Bean 定义，ref: sign_m_232
            Set<BeanDefinitionHolder> beanDefinitionHolders =
                    findServiceBeanDefinitionHolders(scanner, packageToScan, registry, beanNameGenerator); 

            if (!CollectionUtils.isEmpty(beanDefinitionHolders)) {
                ... // log

                for (BeanDefinitionHolder beanDefinitionHolder : beanDefinitionHolders) {
                    processScannedBeanDefinition(beanDefinitionHolder); // 注册 Bean 处理
                    ... // 记录扫描的类
                }
            } 
            ... // else log
            ... // 记录扫描的包
        }
    }

    // sign_m_232  查找扫描出的 Bean 定义
    private Set<BeanDefinitionHolder> findServiceBeanDefinitionHolders(
        ClassPathBeanDefinitionScanner scanner, String packageToScan,
        BeanDefinitionRegistry registry, BeanNameGenerator beanNameGenerator
    ) {
        Set<BeanDefinition> beanDefinitions = scanner.findCandidateComponents(packageToScan); // 获取扫描出的 Bean 定义，ref: sign_m_240
        Set<BeanDefinitionHolder> beanDefinitionHolders = new LinkedHashSet<>(beanDefinitions.size());

        for (BeanDefinition beanDefinition : beanDefinitions) {
            String beanName = beanNameGenerator.generateBeanName(beanDefinition, registry);
            BeanDefinitionHolder beanDefinitionHolder = new BeanDefinitionHolder(beanDefinition, beanName); // 组装
            beanDefinitionHolders.add(beanDefinitionHolder);
        }

        return beanDefinitionHolders;
    }
}
```

- `org.apache.dubbo.config.spring.context.annotation.DubboClassPathBeanDefinitionScanner`
```java
// sign_c_240  扫描工具类
public class DubboClassPathBeanDefinitionScanner extends ClassPathBeanDefinitionScanner {
    // key 是要扫描的包，value 是扫描出的 Bean 定义
    private final ConcurrentMap<String, Set<BeanDefinition>> beanDefinitionMap = new ConcurrentHashMap<>();

    // sign_m_240  只是做了一层包装，方便查找
    @Override
    public Set<BeanDefinition> findCandidateComponents(String basePackage) {
        Set<BeanDefinition> beanDefinitions = beanDefinitionMap.get(basePackage);
        if (Objects.isNull(beanDefinitions)) {
            beanDefinitions = super.findCandidateComponents(basePackage); // 调用父类进行扫描
            beanDefinitionMap.put(basePackage, beanDefinitions);
        }
        return beanDefinitions;
    }
}
```


---
## 初始化
- `org.apache.dubbo.config.spring.context.DubboSpringInitializer`
```java
// sign_c_310  Spring 初始化入口
public class DubboSpringInitializer {

    // sign_sm_310  初始化
    public static void initialize(BeanDefinitionRegistry registry) {
        // 准备上下文并进行定制
        DubboSpringInitContext context = new DubboSpringInitContext();
        ...

        ConfigurableListableBeanFactory beanFactory = findBeanFactory(registry); // 其实就是转化成 BeanFactory
        initContext(context, registry, beanFactory);    // 初始化 Dubbo 上下文，ref: sign_sm_311
    }
    
    // sign_sm_311  初始化 Dubbo 上下文
    private static void initContext(
        DubboSpringInitContext context, BeanDefinitionRegistry registry, ConfigurableListableBeanFactory beanFactory
    ) {
        context.setRegistry(registry);
        context.setBeanFactory(beanFactory);

        ... // customize context
        ... // init ModuleModel
        ... // set module attributes

        // 将 Dubbo 上下文绑定到 Spring 中
        registerContextBeans(beanFactory, context);
        ...

        // 注册普通 Bean
        DubboBeanUtils.registerCommonBeans(registry);
    }
}
```

- `org.apache.dubbo.config.spring.util.DubboBeanUtils`
```java
// sign_c_320  Dubbo Bean 工具类
public interface DubboBeanUtils {

    // sign_sb_320  注册普通 Bean
    static void registerCommonBeans(BeanDefinitionRegistry registry) {
        registerInfrastructureBean(registry, *.BEAN_NAME, ServicePackagesHolder.class);
        registerInfrastructureBean(registry, *.BEAN_NAME, ReferenceBeanManager.class); // 处理 @DubboReference

        // 处理 @...dubbo...Reference
        registerInfrastructureBean(registry, *.BEAN_NAME, ReferenceAnnotationBeanPostProcessor.class);

        ...
    }
}
```