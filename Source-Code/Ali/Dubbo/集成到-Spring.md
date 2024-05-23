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
        DubboSpringInitializer.initialize(registry); // 初始化 Dubbo Bean
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

- `org.apache.dubbo.config.spring.context.DubboSpringInitializer`
```java
public class DubboSpringInitializer {
    public static void initialize(BeanDefinitionRegistry registry) {

        // prepare context and do customize
        DubboSpringInitContext context = new DubboSpringInitContext();

        // Spring ApplicationContext may not ready at this moment (e.g. load from xml), so use registry as key
        if (contextMap.putIfAbsent(registry, context) != null) {
            return;
        }

        // find beanFactory
        ConfigurableListableBeanFactory beanFactory = findBeanFactory(registry);

        // init dubbo context
        initContext(context, registry, beanFactory);
    }
    
    private static void initContext(
        DubboSpringInitContext context, BeanDefinitionRegistry registry, ConfigurableListableBeanFactory beanFactory
    ) {
        context.setRegistry(registry);
        context.setBeanFactory(beanFactory);

        // customize context, you can change the bind module model via DubboSpringInitCustomizer SPI
        customize(context);

        // init ModuleModel
        ModuleModel moduleModel = context.getModuleModel();
        if (moduleModel == null) {
            ApplicationModel applicationModel;
            if (findContextForApplication(ApplicationModel.defaultModel()) == null) {
                // first spring context use default application instance
                applicationModel = ApplicationModel.defaultModel();
                logger.info("Use default application: " + applicationModel.getDesc());
            } else {
                // create a new application instance for later spring context
                applicationModel = FrameworkModel.defaultModel().newApplication();
                logger.info("Create new application: " + applicationModel.getDesc());
            }

            // init ModuleModel
            moduleModel = applicationModel.getDefaultModule();
            context.setModuleModel(moduleModel);
            logger.info("Use default module model of target application: " + moduleModel.getDesc());
        } else {
            logger.info("Use module model from customizer: " + moduleModel.getDesc());
        }
        logger.info(
                "Bind " + moduleModel.getDesc() + " to spring container: " + ObjectUtils.identityToString(registry));

        // set module attributes
        Map<String, Object> moduleAttributes = context.getModuleAttributes();
        if (moduleAttributes.size() > 0) {
            moduleModel.getAttributes().putAll(moduleAttributes);
        }

        // bind dubbo initialization context to spring context
        registerContextBeans(beanFactory, context);

        // mark context as bound
        context.markAsBound();
        moduleModel.setLifeCycleManagedExternally(true);

        // register common beans
        DubboBeanUtils.registerCommonBeans(registry);
    }
}
```

- `org.apache.dubbo.config.spring.util.DubboBeanUtils`
```java
public interface DubboBeanUtils {

    static void registerCommonBeans(BeanDefinitionRegistry registry) {

        registerInfrastructureBean(registry, ServicePackagesHolder.BEAN_NAME, ServicePackagesHolder.class);

        registerInfrastructureBean(registry, ReferenceBeanManager.BEAN_NAME, ReferenceBeanManager.class); // 注入 @DubboReference

        // Since 2.5.7 Register @Reference Annotation Bean Processor as an infrastructure Bean
        registerInfrastructureBean(
                registry, ReferenceAnnotationBeanPostProcessor.BEAN_NAME, ReferenceAnnotationBeanPostProcessor.class);

        // TODO Whether DubboConfigAliasPostProcessor can be removed ?
        // Since 2.7.4 [Feature] https://github.com/apache/dubbo/issues/5093
        registerInfrastructureBean(
                registry, DubboConfigAliasPostProcessor.BEAN_NAME, DubboConfigAliasPostProcessor.class);

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