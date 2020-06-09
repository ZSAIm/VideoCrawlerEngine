VideoCrawlerEngine(Developing)
===============

# 视频爬取引擎(开发中)

视频爬虫引擎是以自定义脚本为草图，生成请求器工作流，实现可控可视的流水线执行。
意在提高脚本的开发效率，让开发者专注于解决反爬。

## 架构草图
![架构草图](./doc/sketch.png)


## 雏形开发进度

### 脚本引擎(script/\*.py)
- [x] 文件注册``(./script/__init__.py)`` - def register(script_name, sha256_key)
- [x] 版本控制``(./script/__init__.py)`` - class Scripts(object)
- [x] 编译执行``(./script/__init__.py)`` - def compile_script(script_name, verify)
- [x] 抽象基类``(./script/base.py)`` - class ScriptBaseClass(object)
- [x] 脚本调试``(./script/base.py)`` - def ScriptBaseClass.test(url, rule)
- [ ] 脚本校验``(./script/__init__.py)`` - def validate_script(source_key, key)
- [ ] 整理优化

### 请求器(_request.py & request.py)
- [x] 基本结构``(./_request.py)``:
    - [x] 请求抽象类 - class Request(object)
    - [x] 请求进度对象 - class RequestProgress(object)
    - [x] 可选请求列表 - class Optional(object)
    - [x] 请求选项化 - class Option(object)
- [x] 简单请求构建器``(./_request.py)`` - def requester(request_name, initializer, sub_getter, base_cls, sketch_data)
- [x] 驱动请求器``(./request.py)`` - class StartScript(Request)
- [x] 脚本请求器``(./request.py)`` - class ScriptRequest(Request)
- [x] 下载请求器``(./request.py)`` - @requester('download', base_cls=(Request, URIs))
- [x] FFmpeg请求器``(./request.py)`` - class FFmpegRequest(Request)
- [x] 视频转换请求器``(./request.py)`` - @requester('convert')
- [x] 清理请求器``(./request.py)`` - @requester('cleanup')
- [ ] 进度信息收集``(./request.py)`` - ...
- [ ] 节点错误处理器``(./request.py)`` - @requester('error_handler')
- [ ] 整理优化

### 工作流引擎(workflow.py)
- [x] 基本结构``(./workflow.py)``:
    - [x] 工作流请求节点 - class RequestNode(Node)
    - [x] 工作流阶段节点 - class StageNodes(Node)
    - [x] 请求工作流对象 - class RequestWorkflow(object)
- [x] 分解请求工作链``(./workflow.py)`` - def factor_request(request, rule, desc_saver)
- [x] 工作流执行``(./workflow.py)`` - def run_branch(branch_flow); def run_workflow(workflow, semaphore)
- [ ] 工作流节点保存``(./workflow.py)``
- [ ] 整理优化

### 工作器(worker.py)
- [x] 基本结构``(./worker.py)``:
    - [x] 请求工作者池 - REGISTERED_WORKER
    - [x] 工作者抽象类 - class Worker(object)
    - [x] 无工作者 - class NullWorker(Worker)；
    - [x] 线程工作者 - class Workers(Worker, ThreadPoolExecutor)
    - [x] 协程工作者 - class AsyncWorkers(Workers)
- [ ] 工作者负载信息``(./worker.py)`` - payload
- [ ] 整理优化

### 调试器引擎(debugger.py & context.py)
- [x] 请求调试器``(./debugger.py)`` - class RequestDebugger(object) - dbg
- [x] 请求上下文``(./context.py)`` - class RequestDebugger(object) - dbg
    - [x] 根节点信息上下文 - class RootInfo(NodeContext)
    - [x] 工作流节点上下文 - class FlowNodeContext(NodeContext)
- [ ] 整理优化

### 配置系统(config.py)
- [x] 基础配置``(./config.py)`` - BASIC_CONFIG
- [x] 脚本配置``(./config.py)`` - SCRIPT_CONFIG
- [x] 工作器配置``(./config.py)`` - WORKER_CONFIG
- [ ] 整理优化

### Web & UI设计
- [ ] WebDriver.``(./webdriver.py)``
- [ ] Flask 搭建Web Server``(./app/*.py)``
- [ ] 定义交互API

### 开发文档
- [ ] 脚本开发文档
- [ ] 请求器开发文档

### 脚本开发
- [ ] 哔哩哔哩

## Requirements

- Python >= 3.6
- Nbdler >= 3.0.3
- PyJSCaller >= 0.2.0
- wxpython
- Flask


## 许可证

Apache-2.0

## 未来
- [ ] 脚本执行和web server实现进程隔离

## 关于
> 旧项目 iqiyi-parser 由于其架构局限性已放弃维护
