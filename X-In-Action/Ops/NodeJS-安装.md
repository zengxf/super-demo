# NodeJS 安装


## 下载
- https://nodejs.org/en/download
- 解压并加入 `$Path`


## 设置镜像
```sh
# 永久修改配置
npm config set registry https://registry.npmmirror.com

# 验证是否配置成功
npm config get registry

# 查看详细配置列表
npm config list
```