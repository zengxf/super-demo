## IDEA 报 GBK 编码错误
- 参考： https://blog.csdn.net/qq_30019911/article/details/107082987
- IDEA 菜单栏找到：help->Edit Custom VM Options，在打开文件中追加：
  - `-Dfile.encoding=UTF-8`
- 然后重启idea，设置才能生效