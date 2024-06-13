# Git-命令


---
## 查看远程仓库地址
```shell
git remote -v
```


---
## 删除分支
- ref: https://www.freecodecamp.org/chinese/news/git-delete-branch-how-to-remove-a-local-or-remote-branch/
- 删除本地分支 `git branch -d xxxname`
- 强制删除本地分支 `git branch -D xxxname`
- 删除远程分支 `git push origin -d xxxname`


---
## 从 Tag 创建分支
- ref: https://blog.csdn.net/lhcxwjh/article/details/51083249
- 命令格式: `git branch <new-branch-name> <tag-name>`
- 创建分支: `git branch my-2.2.3 2.2.3`
- 切换分支: `git checkout my-2.2.3`


---
## 设置提交用户
```js
git config user.name ZXF
git config user.email zxf@sina.cn
// 查看
git config user.name
git config user.email
```


---
## 取消合并
- ref: https://www.freecodecamp.org/chinese/news/git-undo-merge-how-to-revert-the-last-merge-commit-in-git/
- `git reflog` 更具可读性
```js
PS D:\Work\Code\java-project> git reflog
bec2563a1 (HEAD -> develop) HEAD@{0}: merge fix-by-zxf-0404: Merge made by the 'ort' strategy.  // 这个是合并的记录
8e56854fd (origin/develop) HEAD@{1}: checkout: moving from fix-by-zxf-0404 to develop           // 回滚到这
c00330270 (origin/fix-by-zxf-0404, fix-by-zxf-0404) HEAD@{2}: checkout: moving from uat_new to fix-by-zxf-0404
4fe8a847f (origin/uat_new, uat_new) HEAD@{3}: commit: task#725839
32e650fc1 HEAD@{4}: commit (merge): task#725839

PS D:\Work\Code\java-project> git reset --hard 8e56854fd                                        // 与上对应
HEAD is now at 8e56854fd Merge branch 'xxx' into 'develop'

PS D:\Work\Code\java-project> git status
On branch develop
Your branch is up to date with 'origin/develop'.

nothing to commit, working tree clean
```


---
## 覆盖远程分支
```js
// locdev 本地分支
// remdev 远程分支

git push origin locdev:remdev -f    // 这个才有用

git push origin remdev --force      // 这个命令没用，只是推，不会覆盖
```


---
## 恢复某个文件到上一个提交版本
- ref: https://blog.csdn.net/I_recluse/article/details/88105385
- 但需要重新提交一次


---
## 恢复删除的文件
- ref: https://www.cnblogs.com/yangshifu/p/9680993.html
```js
git reset HEAD file-or-folder
git checkout file-or-folder
```


---
## GitHub: Clone succeeded, but checkout failed
- **文件名太长**
- ref: https://stackoverflow.com/questions/22041752/github-clone-succeeded-but-checkout-failed
```js
git config --system core.longpaths true
```