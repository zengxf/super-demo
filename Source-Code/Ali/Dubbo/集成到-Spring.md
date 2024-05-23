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
        registerInfrastructureBean(registry, ServicePackagesHolder.BEAN_NAME, ServicePackagesHolder.class);
        registerInfrastructureBean(registry, ReferenceBeanManager.BEAN_NAME, ReferenceBeanManager.class); // 注入 @DubboReference

        // Since 2.5.7 Register @Reference Annotation Bean Processor as an infrastructure Bean
        registerInfrastructureBean(
                registry, ReferenceAnnotationBeanPostProcessor.BEAN_NAME, ReferenceAnnotationBeanPostProcessor.class);


        // register ApplicationListeners
        registerInfrastructureBean(
                registry, DubboDeployApplicationListener.class.getName(), DubboDeployApplicationListener.class);
        registerInfrastructureBean(
                registry, DubboConfigApplicationListener.class.getName(), DubboConfigApplicationListener.class);

        // Since 2.7.6 Register DubboConfigDefaultPropertyValueBeanPostProcessor as an infrastructure Bean
        registerInfrastructureBean(
                registry,
                DubboConfigDefaultPropertyValueBeanPostProcessor.BEAN_NAME,
                DubboConfigDefaultPropertyValueBeanPostProcessor.class);

        // Dubbo config initializer
        registerInfrastructureBean(registry, DubboConfigBeanInitializer.BEAN_NAME, DubboConfigBeanInitializer.class);

        // register infra bean if not exists later
        registerInfrastructureBean(
                registry, DubboInfraBeanRegisterPostProcessor.BEAN_NAME, DubboInfraBeanRegisterPostProcessor.class);
    }
}
```