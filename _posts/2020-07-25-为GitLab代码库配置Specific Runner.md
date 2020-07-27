---
title: 为 GitLab 代码库配置 Specific Runner
layout: info
commentable: true
Edit: 2020-07-25
mathjax: true
mermaid: true
tags: GitLab
categories: GitLab
description: 在 GitLab 的 CI/CD 流程。
---

### 配置 Specific Runner

在 GitLab 的 CI/CD 流程中具体执行任务的节点叫做 [runner](https://docs.gitlab.com/runner/)。GitLab 中有两种类型的 runner：

- **Shared Runners** 由 GitLab 管理员配置的公有 runner。多个项目公用。作为开发人员无需配置，可以直接使用。
- **Specific Runners** 开发人员为每个代码库单独配置的专属 runner。只能执行所属代码库的任务。需要开发人员手动搭建。

由于我厂的 GitLab 并没有配置任何 Shared Runner。所以只能选择在自己的台式机上手动搭建。

### 下载 runner 可执行文件

根据你的环境下载 [x86](https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-windows-386.exe) 或者 [amd64](https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-windows-amd64.exe) 版本。

创建 `D:\GitLab-Runner` 目录，将刚刚下载好的文件复制到该目录并重命名为 `gitlab-runner.exe`。

### 获取配置信息

进入代码库主页，依次点击 `Settings` => `CI / CD` => `Runners settings`。

![1595562311495](/assets/images/2020/07/1595562311495.png)

这里展开的信息中有两个字段需要我们记下来。分别是一个 URL 和一个 Token。

![1595562367478](/assets/images/2020/07/1595562367478.png)

### 注册 runner

进入 `D:\GitLab-Runner` 目录执行命令：

```yml
./gitlab-runner.exe register
```

执行完后会进入一个交互式的配置流程，你需要回答以下问题：

- `Please enter the gitlab-ci coordinator URL`：填入上一步获取的 URL
- `Please enter the gitlab-ci token for this runner`：填入上一步获取的 Token
- `Please enter the gitlab-ci description for this runner`：给你的 runner 起一个名字
- `Please enter the gitlab-ci tags for this runner (comma separated)`：GitLab 允许我们给 runner 设置标签，设置好后该 runner 只会执行拥有相同标签的任务。由于我们的 runner 只为我们自己的代码库服务，所以此处不做过多配置。留空即可。
- `Whether to lock Runner to current project`：该 runner 是否应该锁定在当前项目上。由于我们是自己用，选 `true` 即可。
- `Please enter the executor: ssh, docker+machine, docker-ssh+machine, kubernetes, docker, parallels, virtualbox, docker-ssh, shell: docker`：选择任务执行环境，我们选择最简单的 `shell`。

### 验证服务已启动

进入代码库主页，依次点击 `Settings` => `CI / CD` => `Runners settings`。

![1595562200358](/assets/images/2020/07/1595562200358.png)


