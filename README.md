# XiaoAI TTS Bridge

**小爱 TTS 中间服务**是一个 Home Assistant 自定义集成。它将 Home Assistant 的通知消息桥接到小米 MiNA 云端 TTS 接口，再由账号下选定的小爱音箱播报。

```text
Home Assistant notify.send_message
        ↓
XiaoAI TTS Bridge
        ↓
MiService / MiNA API
        ↓
小爱音箱默认 TTS 音色
```

本项目不是独立的语音合成引擎，也不是局域网离线 TTS 服务。

## 当前状态

- 集成版本：`0.1.1`
- 已完成真实环境登录、设备发现和文字播报测试
- 已验证设备：`onemore.wifispeaker.sm4`
- Home Assistant Domain：`xiaoai_tts`
- 底层依赖：`miservice==3.0.1`

其他 MiNA 音箱可能也能使用，但在加入已验证列表前，应以实际测试结果为准。

## 功能

- 通过 Home Assistant 图形界面配置
- 小米账号登录
- 支持短信或邮件验证码验证
- 自动读取账号下的 MiNA 音箱列表
- 自动获取和保存稳定的 `miotDID`，无需手工填写 DID
- 支持选择一个或多个音箱
- 每台音箱创建独立的 Notify Entity
- 使用 Home Assistant Config Entry 持久化 Token
- 不保存小米账号密码
- 支持账号重新认证
- 支持重新选择音箱
- 提供英文和简体中文界面

## 工作原理

配置时，集成从 MiNA 设备列表读取：

```text
miotDID  → 用于持久化识别设备
deviceID → 用于调用 MiNA TTS 接口
```

运行时会重新获取设备列表，并将保存的 `miotDID` 映射为当前 `deviceID`，最终调用：

```python
MiNAService.text_to_speech(deviceID, text)
```

## 音色说明

当前版本使用小爱音箱的**默认 MiNA TTS 音色**，不支持通过 MiNA 原生文字播报接口指定音色、说话人、语速或音调。

原因是 `miservice==3.0.1` 的 MiNA 文字播报接口只接受：

```python
text_to_speech(deviceID, text)
```

未来可以研究以下扩展路径：

```text
外部 TTS 引擎生成自定义音色音频
        ↓
生成音箱可访问的 HTTP/HTTPS 音频 URL
        ↓
通过 MiNA URL 播放接口交给音箱播放
```

这属于“外部 TTS 音频桥接”，不是修改小爱音箱的内置 TTS 音色。该功能当前尚未实现，且需要针对具体音箱型号验证 URL 播放兼容性。

## 通过 HACS 安装

1. 打开 HACS。
2. 进入“集成”。
3. 点击右上角菜单，选择“自定义存储库”。
4. 填入：

   ```text
   https://github.com/nymanyim/xiaoai-tts-bridge
   ```

5. 类别选择“集成”。
6. 添加后搜索并下载 **XiaoAI TTS Bridge**。
7. 重启 Home Assistant。
8. 打开“设置 → 设备与服务 → 添加集成”。
9. 搜索 **XiaoAI TTS Bridge**；中文界面中显示为**小爱 TTS 中间服务**。
10. 输入小米账号和密码，根据提示完成验证码验证，然后选择需要使用的音箱。

## 发送文字播报

在“开发者工具 → 操作”中调用：

```yaml
action: notify.send_message
target:
  entity_id: notify.xiao_ai_yin_xiang_hd
data:
  message: "测试小爱音箱文字播报"
```

`notify.xiao_ai_yin_xiang_hd` 是已验证环境中的实际实体 ID。不同设备名称会生成不同的实体 ID，请始终以 Home Assistant 实体页面显示的 ID 为准，不要直接照抄示例。

自动化示例：

```yaml
alias: 入户提醒
triggers:
  - trigger: state
    entity_id: binary_sensor.front_door
    to: "on"
actions:
  - action: notify.send_message
    target:
      entity_id: notify.xiao_ai_yin_xiang_hd
    data:
      message: "入户门已打开"
mode: single
```

## 更新与兼容性

项目显示名称已从 `XiaoAI TTS` 调整为 `XiaoAI TTS Bridge`。为保护已有安装，以下内部标识保持不变：

```text
Domain：xiaoai_tts
组件目录：custom_components/xiaoai_tts
```

升级后无需删除已有 Config Entry。若 HACS 或 Home Assistant 暂时显示旧名称，请更新集成并重启 Home Assistant，必要时刷新浏览器缓存。

## 安全与隐私

- 密码只在首次登录或重新认证时使用，不写入 Config Entry。
- 登录 Token 保存在 Home Assistant 的配置存储中。
- 请保护 Home Assistant 配置目录、备份文件和管理账号。
- 播报内容会经过小米 MiNA 云服务，本项目不是本地离线方案。
- 项目不隶属于、不受支持于小米、Home Assistant 或 MiService。
- 小米云端接口、账号风控或设备固件变化可能影响可用性。

## 故障排查

### 集成无法登录

- 确认小米账号和密码正确。
- 按配置向导完成短信或邮件验证码验证。
- 确认 Home Assistant 可以访问 `account.xiaomi.com` 和 `api2.mina.mi.com`。

### 找不到音箱

- 确认音箱属于当前登录的小米账号。
- 确认音箱能在米家或小爱音箱应用中正常使用。
- 重新配置集成并刷新设备列表。

### 调用成功但没有声音

1. 确认调用的是本集成创建的 `notify` 实体。
2. 确认实体 ID 正确；已验证环境使用：

   ```text
   notify.xiao_ai_yin_xiang_hd
   ```

3. 确认音箱在线、音量不为零且未处于不可播报状态。
4. 查看 Home Assistant 日志中的：

   ```text
   custom_components.xiaoai_tts
   miservice
   ```

### 开启调试日志

在 `configuration.yaml` 中临时添加：

```yaml
logger:
  default: info
  logs:
    custom_components.xiaoai_tts: debug
    miservice: debug
```

重启 Home Assistant 并复现问题。排查完成后请删除或降低调试日志级别，避免日志持续增长。

## 底层项目与致谢

本项目的 Home Assistant 集成、配置流程、设备映射和 Notify Entity 封装为独立实现；小米账号登录、Token 管理以及 MiNA API 能力由以下开源项目提供：

- **MiService**：<https://github.com/Yonsm/MiService>
- **原作者**：[Yonsm](https://github.com/Yonsm)
- **版权声明**：Copyright © 2021–2026 Yonsm
- **许可证**：MIT License
- **本项目固定依赖版本**：`miservice==3.0.1`

感谢 Yonsm 开发和维护 MiService。本项目没有 MiService，就无法完成小米账号认证、MiNA 设备发现及音箱 TTS 调用。

## 项目许可证

XiaoAI TTS Bridge 使用 [MIT License](LICENSE)：

```text
Copyright (c) 2026 nymanyim
```

MiService 作为独立依赖继续遵循其自身的 MIT License 和版权声明。
