# 死代码仓库盘点报告（/home/geeker/architecture/home/geeker/code_repo）

> 扫描时间：2026-10-11　判定窗口：近一年 = **2025-10-11 ~ 2026-10-11**　
> 扫描范围：当前目录及全部子目录，共 **3,572,231 个文件 / 330.2 GB**（已排除 `.git`、`node_modules`、`target`、`.venv`、`__pycache__`、`.m2`、`.gradle` 等目录本身的体积）

## 一、结论速览

| 分级 | 数量 | 体积 | 占总量 | 含义 |
|---|---:|---:|---:|---|
| **C 死代码** | 290 | **60.4 GB** | 18.3% | 近一年没有任何文件被打开看过，也没有任何文件被改动 |
| B 冷藏只读 | 370 | 56.4 GB | 17.1% | 近一年看过（读过文件）但没改过，属于资料/参考 |
| A 活跃 | 508 | 213.3 GB | 64.6% | 近一年有文件被写过（含近一年 clone/更新的写入）或有本地 git 操作 |

- **可直接归档/删除的死代码约 60.4 GB**，其中非 git 的大件（Qt 安装包、MySQL/HBuilderX 二进制、cuda 包、驱动参考包等）占大头。
- 其中真正的 **git 仓库** 死代码 1.8 GB / 42 个。
- ⚠️ 死代码清单中有 **15 个仓库** 存在未推送提交 / 未提交改动 / stash，删除前需先确认（见第四节）。

## 二、判定口径与方法

| 维度 | 取值来源 | 说明 |
|---|---|---|
| 是否被“查看” | 文件 `atime`（最后访问时间） | 文件系统挂载带 `relatime`，读取文件即更新；只要近一年内打开/读取过任意文件即视为“看过” |
| 是否被“改动” | 文件 `mtime`（最后修改时间） | 近一年内有任意文件被写入即视为改动 |
| 本地 git 活跃度 | `.git/logs/HEAD` reflog 时间戳 | clone / fetch / pull / checkout / commit 都会记录，代表**本地**操作时间 |
| 上游活跃度 | `git log -1` 的 HEAD 提交时间 | 这些多为 clone 的开源仓库，HEAD 时间是**上游作者**的提交时间，不能代表本地是否动过，故仅作参考 |

**分级规则**

```
C  死代码   = 近一年 0 个文件被读过 + 0 个文件被改过
B  冷藏只读 = 近一年有文件被读过，但 0 个文件被改过，且无本地 git 操作
A  活跃     = 近一年有文件被改过，或有本地 git 操作（含近一年 clone/更新）
```

补充说明：git 仓库被 clone 时文件 `mtime/atime` 就是 clone 时刻，因此另做了“clone 后是否真的打开过”的交叉校验（`max(atime)` 是否晚于 reflog 中的 clone 时间）——结果见 4.4。

> 局限说明：① `atime` 是“读过”的下界——用 `cat/编辑器/编译` 打开才会更新，被 IDE 索引、grep 搜索也会更新；② 扫描期间目录被并发改动过（`theory_base_hardware_chips` 下若干仓库在扫描过程中被移除），清单以扫描时刻快照为准；③ 体积为文件表观大小之和，不含 `.git` 目录与依赖缓存目录。

## 三、全库概览（顶层目录）

| 顶层目录 | 文件数 | 体积 | 最后查看 | 最后修改 | 近一年被读 | 近一年被改 |
|---|---:|---:|---|---|---:|---:|
| `infrastructure_system_softwares` | 1,572,765 | 119.18 GB | 2026-10-11 | 2026-10-11 | 1,007,687 | 739,206 |
| `algo_engine_bigdata` | 496,926 | 101.36 GB | 2026-10-10 | 2026-10-09 | 425,733 | 331,683 |
| `platforms_scene` | 893,177 | 56.53 GB | 2026-10-11 | 2026-10-08 | 397,004 | 218,027 |
| `best_practice_perf` | 241,536 | 28.32 GB | 2026-10-11 | 2026-10-11 | 188,387 | 187,192 |
| `industry_secne` | 134,333 | 17.53 GB | 2026-10-10 | 2026-09-01 | 4,106 | 875 |
| `middle_wares_interfaces_connectors` | 129,939 | 3.61 GB | 2026-10-11 | 2026-08-24 | 67,409 | 6,606 |
| `theory_base_hardware_chips` | 86,394 | 2.71 GB | 2026-10-11 | 2026-10-10 | 86,203 | 27,945 |
| `softwares_repo` | 17,158 | 963.3 MB | 2026-10-10 | 2025-11-18 | 7,016 | 4,127 |
| `resumes` | 2 | 2.2 MB | 2026-09-25 | 2026-09-25 | 2 | 2 |
| **合计** | **3,572,231** | **330.2 GB** | | | | |

## 四、死代码清单

### 4.1 C 级：完全死代码 —— 非 git 目录（多为大件二进制/安装包）

| 体积 | 文件数 | 路径 | 最后查看 | 最后修改 |
|---:|---:|---|---|---|
| 23.40 GB | 442 | `infrastructure_system_softwares/kernel_dev/driver_dev/driver_ref` | 2025-01-13 | 2025-01-13 |
| 3.85 GB | 2 | `algo_engine_bigdata/ai/cuda_gpu_dev` | 2025-03-19 | 2025-03-19 |
| 3.82 GB | 57,467 | `platforms_scene/qt_dev/Qt_devtools/6.9.1` | 2025-08-19 | 2025-08-19 |
| 3.33 GB | 4,798 | `platforms_scene/multi_media_dev/text_process/auto_dev` | 2025-08-30 | 2025-08-30 |
| 3.23 GB | 61,839 | `platforms_scene/multi_media_dev/text_process/office_suites_dev` | 2025-08-19 | 2025-08-19 |
| 2.64 GB | 5,380 | `platforms_scene/multi_media_dev/voice_dev/build` | 2025-08-26 | 2025-08-26 |
| 2.41 GB | 3 | `industry_secne/ebussiness_dev` | 2025-09-15 | 2025-09-15 |
| 2.20 GB | 38,829 | `platforms_scene/qt_dev/Qt_devtools/Tools` | 2025-08-19 | 2025-08-19 |
| 1.95 GB | 951 | `platforms_scene/multi_media_dev/voice_dev/cef_binary_6533_linux_x86_64` | 2025-08-27 | 2024-08-16 |
| 1.32 GB | 33,205 | `industry_secne/ebussiness_dev/hbuilderX/HBuilderX_Alpha` | 2025-09-08 | 2025-07-31 |
| 1.32 GB | 33,208 | `industry_secne/ebussiness_dev/hbuilderX/HBuilderX` | 2025-09-09 | 2025-08-21 |
| 1.05 GB | 48,227 | `algo_engine_bigdata/database_system/mysql/mysql-9.1.0` | 2025-01-16 | 2024-09-24 |
| 910.0 MB | 11,289 | `platforms_scene/multi_media_dev/video_dev/app` | 2025-08-27 | 2025-08-27 |
| 818.1 MB | 3 | `algo_engine_bigdata/database_system/mysql/backup` | 2025-02-07 | 2025-02-07 |
| 733.9 MB | 6,506 | `algo_engine_bigdata/database_system/mysql/mysql-5.5.58-linux-glibc2.12-x86_64` | 2025-01-16 | 2017-09-14 |
| 661.6 MB | 2 | `infrastructure_system_softwares/language_dev/java/work_flow_activiti` | 2025-01-13 | 2025-01-13 |
| 589.5 MB | 4 | `platforms_scene/multi_media_dev/voice_dev` | 2025-08-27 | 2025-08-27 |
| 588.6 MB | 11,018 | `platforms_scene/oa_dev/image_anotation/.vir_env` | 2025-07-18 | 2025-07-18 |
| 371.2 MB | 6,356 | `infrastructure_system_softwares/language_dev/lisp_fortran/portacle_lin` | 2025-08-25 | 2025-08-25 |
| 363.7 MB | 3 | `best_practice_perf/profile_performance_analyse` | 2025-02-26 | 2025-02-26 |
| 298.9 MB | 8,292 | `platforms_scene/qt_dev/Qt_devtools/Docs` | 2025-08-19 | 2025-05-29 |
| 246.9 MB | 6 | `platforms_scene/multi_media_dev/video_dev` | 2025-08-27 | 2025-08-27 |
| 220.9 MB | 22 | `platforms_scene/social_chat_im_oa_dev/mattermost-desktop-5.11.2-linux-x64` | 2025-06-18 | 2025-03-12 |
| 185.2 MB | 274 | `algo_engine_bigdata/database_system/mysql/log_parser` | 2025-02-13 | 2024-06-06 |
| 182.0 MB | 1 | `algo_engine_bigdata/ai/virtual_varta` | 2025-06-28 | 2025-06-28 |
| 179.7 MB | 2 | `platforms_scene/multi_media_dev/text_process/marktext_dev` | 2025-06-16 | 2025-06-16 |
| 160.3 MB | 2 | `platforms_scene/multi_media_dev/img_dev` | 2025-08-20 | 2025-08-20 |
| 158.7 MB | 6,673 | `best_practice_perf/bugs_killer/clamav-1.4.2/.cargo` | 2025-02-20 | 2025-01-20 |
| 115.3 MB | 5 | `best_practice_perf/bugs_killer` | 2025-03-18 | 2025-03-18 |
| 112.9 MB | 6,905 | `platforms_scene/qt_dev/Qt_devtools/Examples` | 2025-05-30 | 2025-05-29 |
| … | | 其余 218 项见 CSV | | |

### 4.2 C 级：完全死代码 —— git 仓库

| 体积 | 文件数 | 仓库路径 | 最后查看 | 最后修改 | 最后本地git操作 | HEAD提交 | 远程 |
|---:|---:|---|---|---|---|---|
| 703.8 MB | 100,791 | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/visualvm/visualvm/visualvm/build/nb/netbeans` | 2025-07-05 | 2025-07-05 | 2025-07-05 | 2024-05-16 | GH:apache/netbeans |
| 494.3 MB | 2,317 | `platforms_scene/multi_media_dev/text_process/office_suites_dev/paperless_dev/paperless-ngx` | 2025-08-18 | 2025-08-18 | 2025-08-18 | 2025-08-17 | GH:paperless-ngx/paperless-ngx.git |
| 250.3 MB | 690 | `infrastructure_system_softwares/language_dev/java/se_app/core_tech_app/java-almanac` | 2025-06-30 | 2025-06-30 | 2025-06-30 | 2025-06-29 | GH:marchof/java-almanac.git |
| 138.3 MB | 3,670 | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/mat` | 2025-07-05 | 2025-07-05 | 2025-07-05 | 2025-06-30 | GH:eclipse-mat/mat.git |
| 102.4 MB | 4,607 | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/visualvm/visualvm` | 2025-07-05 | 2025-07-05 | 2025-07-05 | 2025-06-30 | GH:oracle/visualvm.git |
| 29.6 MB | 64 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-cloud/Turbine` | 2025-07-16 | 2025-07-16 | 2025-07-16 | 2015-07-10 | GH:Netflix/Turbine.git |
| 24.8 MB | 585 | `infrastructure_system_softwares/language_dev/fortran/app/first_app/build/dependencies/stdlib` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2025-08-10 | （无） |
| 20.2 MB | 1,366 | `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/M_CLI2` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2022-11-24 | （无） |
| 20.2 MB | 1,364 | `infrastructure_system_softwares/language_dev/fortran/fpm-search/build/dependencies/M_CLI2` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2022-11-15 | （无） |
| 19.7 MB | 5,744 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-in-action-version5/viewer_dev/thymeleaf` | 2025-03-11 | 2025-03-11 | 2025-03-11 | 2024-12-17 | GH:thymeleaf/thymeleaf.git |
| 15.3 MB | 452 | `infrastructure_system_softwares/language_dev/fortran/fpm-search/build/dependencies/M_strings` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2025-07-10 | （无） |
| 12.0 MB | 172 | `platforms_scene/multi_media_dev/renders_site_genetator/nextjs_dev/blog/blog-starter-app` | 2025-06-17 | 2025-06-17 | 2025-06-17 | 2025-06-17 | （无） |
| 7.7 MB | 130 | `infrastructure_system_softwares/language_dev/fortran/fpm-search/build/dependencies/json-fortran` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2025-08-25 | （无） |
| 7.7 MB | 429 | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/jitwatch` | 2025-07-05 | 2025-07-05 | 2025-07-05 | 2024-10-13 | GH:AdoptOpenJDK/jitwatch.git |
| 4.7 MB | 987 | `platforms_scene/multi_media_dev/text_process/pandoc_cabel/dist-newstyle/src/citeproc-2c8c66795cc244f7` | 2025-06-16 | 2025-06-16 | 2025-06-16 | 2025-06-03 | GH:jgm/citeproc.git |
| 4.3 MB | 893 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-in-action-version5/activemq-artemis-examples` | 2025-03-18 | 2025-03-18 | 2025-03-16 | 2025-03-12 | GH:apache/activemq-artemis-examples.git |
| 3.5 MB | 130 | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/dash-licenses` | 2025-07-05 | 2025-07-05 | 2025-07-05 | 2025-05-30 | git@github.com:eclipse-dash/dash-licenses.git |
| 2.9 MB | 189 | `platforms_scene/multi_media_dev/text_process/office_suites_dev/app/quazip` | 2025-08-19 | 2025-08-19 | 2025-08-19 | 2025-08-10 | GH:stachenov/quazip.git |
| 2.7 MB | 216 | `platforms_scene/multi_media_dev/img_dev/gegl/subprojects/babl` | 2025-08-21 | 2025-08-21 | 2025-08-21 | 2025-08-15 | https://gitlab.gnome.org/GNOME/babl.git |
| 2.1 MB | 258 | `platforms_scene/multi_media_dev/text_process/office_suites_dev/app/qtspell` | 2025-08-19 | 2025-08-19 | 2025-08-19 | 2025-07-17 | GH:manisandro/qtspell.git |
| 1.6 MB | 456 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-cli_dev/spring-cli` | 2025-06-23 | 2025-06-23 | 2025-06-23 | 2025-05-14 | GH:spring-attic/spring-cli.git |
| 1.2 MB | 216 | `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/toml-f` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2023-04-16 | （无） |
| 0.8 MB | 20 | `infrastructure_system_softwares/language_dev/java/3rdlib_app/picocli/picocli-demo` | 2025-03-17 | 2025-03-17 | 2026-10-11 | — | （无） |
| 0.3 MB | 20 | `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/fortran-regex` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2023-04-27 | （无） |
| 0.2 MB | 35 | `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/jonquil` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2023-06-21 | （无） |
| 0.1 MB | 174 | `infrastructure_system_softwares/language_dev/java/se_app/effective_java_example/effective-java-3e-source-code` | 2025-07-14 | 2025-07-14 | 2025-06-30 | 2019-09-11 | GH:jbloch/effective-java-3e-source-code.git |
| 0.1 MB | 24 | `infrastructure_system_softwares/language_dev/fortran/app/first_app/build/dependencies/test-drive` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2021-11-14 | （无） |
| 0.1 MB | 9 | `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/fortran-shlex` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2025-06-16 | （无） |
| 0.1 MB | 18 | `infrastructure_system_softwares/language_dev/java/se_app/core_tech_app/ServiceLoader` | 2025-07-14 | 2025-07-14 | 2026-10-11 | — | （无） |
| 0.1 MB | 42 | `infrastructure_system_softwares/language_dev/fortran/fpm-search/build/dependencies/fhash` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2021-11-13 | （无） |
| 0.1 MB | 130 | `infrastructure_system_softwares/language_dev/java/se_app/effective_java_example/effective-java-examples` | 2025-06-30 | 2025-06-30 | 2025-06-30 | 2015-11-10 | GH:marhan/effective-java-examples.git |
| 0.1 MB | 44 | `infrastructure_system_softwares/language_dev/lisp_fortran/portacle_lin/all/emacsd/portacle` | 2025-08-21 | 2020-01-08 | 2020-01-08 | 2019-02-20 | GH:portacle/emacsd.git |
| 0.1 MB | 17 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-cli_dev/ai-openai-helloworld` | 2025-07-30 | 2025-07-30 | 2025-07-30 | 2024-07-05 | GH:rd-1-2022/ai-openai-helloworld.git |
| 0.1 MB | 19 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/feign_demo/demo` | 2025-03-10 | 2025-03-10 | 2026-10-11 | — | （无） |
| 0.1 MB | 43 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-in-action-version5/json-starter` | 2025-03-27 | 2025-03-27 | 2026-10-11 | — | （无） |
| 0.0 MB | 21 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/feign_demo/feign-service` | 2025-03-12 | 2025-03-12 | 2026-10-11 | — | （无） |
| 0.0 MB | 19 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/feign_demo/user-service` | 2025-03-12 | 2025-03-12 | 2026-10-11 | — | （无） |
| 0.0 MB | 9 | `infrastructure_system_softwares/language_dev/java/se_app/threads_app/vt` | 2025-09-15 | 2025-09-15 | 2026-10-11 | — | （无） |
| 0.0 MB | 4 | `platforms_scene/version_control/git_server_hub/gogs_local/config` | 2025-03-21 | 2025-03-21 | 2025-03-21 | 2025-03-21 | http://localhost:3000/geeker/config.git |
| 0.0 MB | 4 | `platforms_scene/version_control/git_server_hub/gogs/data/tmp/local-repo/2` | 2025-03-21 | 2025-03-21 | 2025-03-21 | 2025-03-21 | /home/geeker/architecture/home/geeker/projs/git_server_hub/gogs_repo/geeker/config.git |
| 0.0 MB | 1 | `platforms_scene/version_control/git_apps/vc` | 2025-08-26 | 2025-08-26 | 2025-08-26 | 2025-08-26 | GH:zhouzxing/version_control.git |
| 0.0 MB | 5 | `platforms_scene/version_control/git_apps/branch_test` | 2025-03-31 | 2025-03-31 | 2025-03-31 | 2025-03-31 | （无） |

### 4.3 B 级：冷藏只读（看过但没改过）体积 Top 20

| 体积 | 文件数 | 路径 | 类型 | 最后查看 | 最后修改 |
|---:|---:|---|---|---|---|
| 7.38 GB | 47,608 | `industry_secne/ebussiness_dev/bailing` | git | 2026-10-10 | 2025-09-16 |
| 5.97 GB | 80,040 | `infrastructure_system_softwares/language_dev/java/jdk` | git | 2026-10-10 | 2025-06-30 |
| 5.54 GB | 7,938 | `algo_engine_bigdata/Math_Model` | git | 2026-10-10 | 2025-06-28 |
| 3.62 GB | 82,064 | `infrastructure_system_softwares/language_dev/c_plus/glibc` | git | 2026-10-10 | 2025-05-13 |
| 3.00 GB | 9,716 | `platforms_scene/multi_media_dev/voice_dev/obs-studio` | git | 2026-10-10 | 2025-08-27 |
| 2.38 GB | 27,470 | `platforms_scene/qt_dev/Qt/Tools` | dir | 2026-09-29 | 2025-08-18 |
| 1.96 GB | 99 | `infrastructure_system_softwares/language_dev/clang+llvm-12.0.1-x86_64-linux-gnu-ubuntu-/bin` | dir | 2026-09-17 | 2021-07-12 |
| 1.52 GB | 48,519 | `platforms_scene/web_dev/projs_low_code/Rocket.Chat` | git | 2026-10-10 | 2025-03-09 |
| 1.50 GB | 5,440 | `platforms_scene/social_chat_im_oa_dev/qTox_bak` | git | 2026-10-10 | 2025-03-22 |
| 1.48 GB | 3 | `algo_engine_bigdata/database_system/mysql` | dir | 2025-11-24 | 2025-01-16 |
| 1.34 GB | 43,695 | `infrastructure_system_softwares/kernel_dev/driver_dev/driver_ref/linux` | git | 2026-10-10 | 2025-01-13 |
| 1.30 GB | 11,731 | `industry_secne/ebussiness_dev/py-xiaozhi` | git | 2026-10-10 | 2025-09-16 |
| 1.26 GB | 2,614 | `platforms_scene/game_dev/xonotic/xonotic-0.8` | dir | 2026-10-08 | 2023-06-20 |
| 853.8 MB | 701 | `infrastructure_system_softwares/language_dev/clang+llvm-12.0.1-x86_64-linux-gnu-ubuntu-/lib` | dir | 2026-09-17 | 2021-07-12 |
| 811.6 MB | 9,692 | `platforms_scene/multi_media_dev/img_dev/gimp` | git | 2026-10-10 | 2025-08-21 |
| 776.1 MB | 2,918 | `platforms_scene/multi_media_dev/text_process/office_suites_dev/Zettlr` | git | 2026-10-10 | 2025-08-18 |
| 731.9 MB | 2,324 | `platforms_scene/multi_media_dev/text_process/marktext_dev/marktext` | git | 2026-10-10 | 2025-06-16 |
| 709.4 MB | 143,966 | `infrastructure_system_softwares/language_dev/compiler_linker_loader_runtimer_dev/gcc_dev/gcc` | git | 2026-10-10 | 2025-05-12 |
| 686.1 MB | 5,685 | `platforms_scene/social_chat_im_oa_dev/qTox` | git | 2026-10-10 | 2025-03-22 |
| 604.6 MB | 18,994 | `middle_wares_interfaces_connectors/log_monitor/loki` | git | 2026-10-11 | 2025-06-06 |

### 4.4 clone / 下载后从未打开过、也没改过的仓库

交叉校验条件：`max(atime)` 与 `max(mtime)` 都停在 clone（或 CMake 拉取）当天，且工作区干净、无未推送提交。

其中 **42 个（2.64 GB）是 CMake FetchContent / 构建期自动拉取的依赖**（`build/_deps/*-src`、`dist-newstyle/*`），归属活跃项目的构建目录，不建议单独删除（清构建目录即可）。

| 体积 | 文件数 | 仓库路径 | clone 时间 | 最后查看 | 远程 |
|---:|---:|---|---|---|---|
| 0.58 GB | 3,090 | `algo_engine_bigdata/ai/lab_app/houyi_ucas_homework` | 2026-10-09 | 2026-10-10 | GH:Helios-YQH/UCAS-homework |
| 0.48 GB | 2,317 | `platforms_scene/multi_media_dev/text_process/office_suites_dev/paperless_dev/paperless-ngx` | 2025-08-18 | 2025-08-18 | GH:paperless-ngx/paperless-ngx.git |
| 0.24 GB | 690 | `infrastructure_system_softwares/language_dev/java/se_app/core_tech_app/java-almanac` | 2025-06-30 | 2025-06-30 | GH:marchof/java-almanac.git |
| 0.03 GB | 1,265 | `theory_base_hardware_chips/security_dev/antSword` | 2026-10-09 | 2026-10-10 | GH:AntSwordProject/antSword |
| 0.03 GB | 64 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-cloud/Turbine` | 2025-07-16 | 2025-07-16 | GH:Netflix/Turbine.git |
| 0.02 GB | 45 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/gs-graphql-server` | 2026-01-22 | 2026-01-22 | GH:spring-guides/gs-graphql-server |
| 0.02 GB | 61 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/gs-rest-hateoas` | 2026-01-22 | 2026-01-22 | GH:spring-guides/gs-rest-hateoas |
| 0.02 GB | 5,744 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-in-action-version5/viewer_dev/thymeleaf` | 2025-03-11 | 2025-03-11 | GH:thymeleaf/thymeleaf.git |
| 0.01 GB | 172 | `platforms_scene/multi_media_dev/renders_site_genetator/nextjs_dev/blog/blog-starter-app` | 2025-06-17 | 2025-06-17 | （无） |
| 0.00 GB | 130 | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/dash-licenses` | 2025-07-05 | 2025-07-05 | git@github.com:eclipse-dash/dash-licenses.git |
| 0.00 GB | 189 | `platforms_scene/multi_media_dev/text_process/office_suites_dev/app/quazip` | 2025-08-19 | 2025-08-19 | GH:stachenov/quazip.git |
| 0.00 GB | 2 | `resumes` | 2026-09-25 | 2026-09-25 | GH:zhouzxing/resume.git |
| 0.00 GB | 456 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-cli_dev/spring-cli` | 2025-06-23 | 2025-06-23 | GH:spring-attic/spring-cli.git |
| 0.00 GB | 47 | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/gs-integration` | 2025-12-29 | 2025-12-30 | GH:spring-guides/gs-integration |
| 0.00 GB | 130 | `infrastructure_system_softwares/language_dev/java/se_app/effective_java_example/effective-java-examples` | 2025-06-30 | 2025-06-30 | GH:marhan/effective-java-examples.git |
| 0.00 GB | 4 | `platforms_scene/version_control/git_server_hub/gogs_local/config` | 2025-03-21 | 2025-03-21 | http://localhost:3000/geeker/config.git |
| 0.00 GB | 3 | `infrastructure_system_softwares/language_dev/python/fastapi_app_dev/just_do_it` | 2026-09-19 | 2026-09-19 | http://47.106.207.27:3000/yuanbao/just_do_it.git |
| 0.00 GB | 4 | `platforms_scene/version_control/git_server_hub/gogs/data/tmp/local-repo/2` | 2025-03-21 | 2025-03-21 | /home/geeker/architecture/home/geeker/projs/git_server_hub/gogs_repo/geeker/config.git |
| 0.00 GB | 1 | `infrastructure_system_softwares/language_dev/python/fastapi_app_dev/test_git` | 2026-09-27 | 2026-09-27 | http://47.106.207.27:3000/geeker/test_git |
| 0.00 GB | 1 | `platforms_scene/version_control/git_apps/vc` | 2025-08-26 | 2025-08-26 | GH:zhouzxing/version_control.git |
| 0.00 GB | 5 | `platforms_scene/version_control/git_apps/branch_test` | 2025-03-31 | 2025-03-31 | （无） |

### 4.5 ⚠️ 删除前必须确认的仓库（死代码里带未推送/未提交内容）

| 体积 | 仓库路径 | 未推送提交 | 未跟踪文件 | 已跟踪改动 | stash |
|---:|---|---:|---:|---:|---:|
| 703.8 MB | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/visualvm/visualvm/visualvm/build/nb/netbeans` | 0 | 2 | 44 | 0 |
| 138.3 MB | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/mat` | 0 | 0 | 1 | 0 |
| 102.4 MB | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/visualvm/visualvm` | 0 | 1 | 0 | 0 |
| 7.7 MB | `infrastructure_system_softwares/language_dev/java/se_app/memoryAnalyzer/jitwatch` | 0 | 1 | 0 | 0 |
| 2.7 MB | `platforms_scene/multi_media_dev/img_dev/gegl/subprojects/babl` | 0 | 1 | 0 | 0 |
| 2.1 MB | `platforms_scene/multi_media_dev/text_process/office_suites_dev/app/qtspell` | 0 | 0 | 1 | 0 |
| 0.8 MB | `infrastructure_system_softwares/language_dev/java/3rdlib_app/picocli/picocli-demo` | 0 | 5 | 5 | 0 |
| 0.1 MB | `infrastructure_system_softwares/language_dev/java/se_app/core_tech_app/ServiceLoader` | 0 | 4 | 8 | 0 |
| 0.1 MB | `infrastructure_system_softwares/language_dev/lisp_fortran/portacle_lin/all/emacsd/portacle` | 0 | 21 | 0 | 0 |
| 0.1 MB | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-cli_dev/ai-openai-helloworld` | 0 | 0 | 1 | 0 |
| 0.1 MB | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/feign_demo/demo` | 0 | 0 | 11 | 0 |
| 0.1 MB | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring-in-action-version5/json-starter` | 0 | 8 | 9 | 0 |
| 0.0 MB | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/feign_demo/feign-service` | 0 | 4 | 9 | 0 |
| 0.0 MB | `infrastructure_system_softwares/language_dev/java/spring_mesh/spring_boot_clouds_apps/feign_demo/user-service` | 0 | 2 | 9 | 0 |
| 0.0 MB | `infrastructure_system_softwares/language_dev/java/se_app/threads_app/vt` | 0 | 0 | 6 | 0 |

## 五、git 信息汇总

- **git 仓库总数：652 个**（含嵌套子模块仓库；其中 652 个采集到完整 git 元信息）
- 当前路径 `/home/geeker/architecture/home/geeker/code_repo` **本身不是 git 仓库**，是由若干独立 clone 的仓库组成的“资料库/学习库”。

#### 5.1 提交活跃度（按 HEAD 提交年份，即上游时间）

| 年份 | 仓库数 |
|---|---:|
| 2002 | 1 |
| 2013 | 2 |
| 2014 | 1 |
| 2015 | 6 |
| 2016 | 4 |
| 2017 | 12 |
| 2018 | 13 |
| 2019 | 12 |
| 2020 | 20 |
| 2021 | 11 |
| 2022 | 21 |
| 2023 | 27 |
| 2024 | 38 |
| 2025 | 295 |
| 2026 | 173 |
| unknown | 16 |

- 近一年有提交的仓库：**220** 个；无提交：**432** 个（上游停更多为 2025 年及之前的归档项目）。

#### 5.2 本地操作活跃度（reflog，代表本地真实动过的时间）

| 年份 | 仓库数 |
|---|---:|
| 2014 | 1 |
| 2017 | 1 |
| 2020 | 2 |
| 2024 | 1 |
| 2025 | 340 |
| 2026 | 307 |

- 2026 年内本地动过（clone/pull/checkout/commit）：**307** 个。

#### 5.3 工作区状态

| 指标 | 数量 | 说明 |
|---|---:|---|
| 工作区有改动/未跟踪文件 | 176 | 含未跟踪的编译产物、本地实验代码 |
| 有未推送的本地提交 | 3 | 相对 upstream 领先，删除前需确认 |
| 无 remote（纯本地仓库） | 43 | 多为自己建的工程/练习项目 |
| detached HEAD | 61 | 检出到历史提交/子模块 |

**未推送提交最多的仓库（Top 15）**

| 仓库路径 | 未推送提交 | 最后本地操作 |
|---|---:|---|
| `industry_secne/ebussiness_dev/xiaozhi-esp32-server-java` | 2 | 2025-09-15 |
| `platforms_scene/version_control/git_apps/progit_demo` | 2 | 2025-04-01 |
| `platforms_scene/version_control/git_apps/version_control` | 1 | 2025-12-23 |

**无 remote 的纯本地仓库**

| 仓库路径 | 提交数 | 最后本地操作 |
|---|---:|---|
| `best_practice_perf/labs_ai_/agent_app/img_gene` | 1 | 2026-09-25 |
| `best_practice_perf/labs_ai_/agent_app/intro_self` | 4 | 2026-10-06 |
| `best_practice_perf/labs_ai_/agent_app/agent_dev_book_lab` | 0 | 2026-10-11 |
| `best_practice_perf/labs_ai_/agent_app/growth-story` | 1 | 2026-09-22 |
| `infrastructure_system_softwares/language_dev/fortran/app/first_app/build/dependencies/stdlib` | 1 | 2025-08-26 |
| `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/M_CLI2` | 1 | 2025-08-26 |
| `infrastructure_system_softwares/language_dev/fortran/fpm-search/build/dependencies/M_CLI2` | 1 | 2025-08-26 |
| `platforms_scene/multi_media_dev/renders_site_genetator/strapi_dev/strapi_projext` | 1 | 2025-06-17 |
| `infrastructure_system_softwares/language_dev/fortran/fpm-search/build/dependencies/M_strings` | 1 | 2025-08-26 |
| `platforms_scene/multi_media_dev/renders_site_genetator/nextjs_dev/blog/blog-starter-app` | 1 | 2025-06-17 |
| `infrastructure_system_softwares/language_dev/fortran/fpm-search/build/dependencies/json-fortran` | 1 | 2025-08-26 |
| `best_practice_perf/labs_ai_/agent_app/infor_ai_lab` | 12 | 2026-10-10 |
| `platforms_scene/multi_media_dev/renders_site_genetator/hugo_blog` | 0 | 2026-10-11 |
| `infrastructure_system_softwares/language_dev/fortran/app/first_app` | 0 | 2026-10-11 |
| `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/toml-f` | 1 | 2025-08-26 |
| `platforms_scene/game_dev/pacman/pacman` | 6 | 2026-04-02 |
| `platforms_scene/game_dev/pacman/pacman.java` | 6 | 2026-04-02 |
| `best_practice_perf/labs_ai_/agent_app/face_recognition` | 4 | 2026-10-06 |
| `infrastructure_system_softwares/language_dev/java/3rdlib_app/picocli/picocli-demo` | 0 | 2026-10-11 |
| `platforms_scene/multi_media_dev/renders_site_genetator/blog-starter-app` | 1 | 2025-06-17 |
| `infrastructure_system_softwares/language_dev/python/fastapi_app_dev/fastapi_tutor` | 8 | 2026-09-24 |
| `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/fortran-regex` | 1 | 2025-08-26 |
| `platforms_scene/multi_media_dev/renders_site_genetator/astro_dev/extinct-ellipse` | 1 | 2025-06-17 |
| `platforms_scene/web_dev/architecure_design/UniTestAuto` | 0 | 2026-10-11 |
| `infrastructure_system_softwares/language_dev/fortran/fpm/build/dependencies/jonquil` | 1 | 2025-08-26 |

#### 5.4 远程来源分布（Top 15 组织/站点）

| 来源 | 仓库数 |
|---|---:|
| （无 remote / 纯本地） | 43 |
| github.com/apache | 13 |
| github.com/Trinkle23897 | 10 |
| gitlab | 9 |
| github.com/libsdl-org | 8 |
| github.com/wkentaro | 7 |
| gitee.com | 7 |
| github.com/spring-guides | 7 |
| github.com/google | 6 |
| github.com/learning-go-book | 6 |
| github.com/zhouzxing | 5 |
| github.com/lavv17 | 5 |
| github.com/alibaba | 5 |
| github.com/kovidgoyal | 5 |
| github.com/google-deepmind | 4 |

## 六、处置建议

1. **先清 C 级非 git 大件**（收益最大、风险最低）：`driver_ref` 23.4 GB、`cuda_gpu_dev` 3.85 GB、Qt 安装包与 Tools 6 GB、MySQL 二进制 1.8 GB、HBuilderX 两份 2.6 GB、`voice_dev/build` 与 `cef_binary` 3.6 GB —— 这些都是可重新下载的安装包/构建产物，合计约 **40 GB+**，建议移到冷备盘或删除。
2. **C 级 git 仓库**：绝大多数是 clone 的第三方项目（visualvm/mat、spring 示例、fortran fpm 依赖、spring-cli demo 等），上游仍在，需要时可重新 clone；共约 1.8 GB，可整批删除或打包归档。
3. **clone 后从没打开过的仓库（4.4）**：共 63 个，4.09 GB，其中大部分是 2026-09 构建时自动拉取的 CMake 依赖；真正“自己 clone 了却没看过”的只有少数几个，建议列观察清单后再决定。
4. **B 冷藏只读**：只保留一份索引（路径清单 + remote 地址）即可，实体可归档到冷存储，需要时按 remote 重新 clone。
5. **删除前必做**：对第四节的“未推送/未提交”仓库先 `git status` / `git log @{u}..HEAD` 确认；对无 remote 的纯本地仓库（多为自己的练习工程）逐个人工确认后再处理。
6. 建议后续维护：给每个仓库补一份 `remote` 清单（已随 CSV 输出），以后按“是否重新可拉取”决定是否保留实体。


## 附：完整清单

明细见同目录 CSV：`dead_code_inventory_2026-10-11.csv`（字段：类别/类型/路径/体积/文件数/最后查看/最后修改/近一年被读/近一年被改/最后本地git操作/HEAD提交/分支/远程/未推送/未跟踪/改动/stash）。
