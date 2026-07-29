# XiaoAI TTS Bridge

**小爱 TTS 中间服务**是一个 Home Assistant 自定义集成，通过小米 MiNA API 将通知文本发送到小爱音箱播报。

## 功能

- 图形化配置小米账号
- 支持短信或邮件验证码
- 自动发现账号下的 MiNA 音箱
- 支持选择一个或多个音箱
- 为每台音箱创建独立的 Notify Entity
- 持久化登录 Token，不保存账号密码
- 支持重新认证和重新选择设备

已验证设备：`onemore.wifispeaker.sm4`

## 限制

当前使用小爱音箱默认的 MiNA TTS 音色，不支持指定音色、说话人、语速或音调。播报依赖小米云服务，不支持离线使用。

## 安装

1. 打开 HACS，进入“集成”。
2. 添加自定义存储库：

   ```text
   https://github.com/nymanyim/xiaoai-tts-bridge
   ```

3. 类别选择“集成”，下载 **XiaoAI TTS Bridge**。
4. 重启 Home Assistant。
5. 打开“设置 → 设备与服务 → 添加集成”。
6. 搜索 **XiaoAI TTS Bridge**，输入小米账号并选择音箱。

## 使用

在“开发者工具 → 操作”中调用：

```yaml
action: notify.send_message
target:
  entity_id: notify.xiao_ai_yin_xiang_hd
data:
  message: "测试小爱音箱文字播报"
```

实体 ID 以 Home Assistant 实际创建的 Notify Entity 为准。

## 升级说明

`0.2.0` 起内部标识调整为：

```text
Domain：xiaoai_tts_bridge
组件目录：custom_components/xiaoai_tts_bridge
```

从 `0.1.x` 升级后，请删除旧集成并重新添加 **XiaoAI TTS Bridge**。

## 致谢

底层小米账号认证、Token 管理和 MiNA API 由 [Yonsm/MiService](https://github.com/Yonsm/MiService) 提供，感谢原作者 [Yonsm](https://github.com/Yonsm)。

## 许可证

<a href="LICENSE">MIT</a>
