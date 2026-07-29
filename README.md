# XiaoAI TTS

Home Assistant 自定义集成，通过小米 MiNA 云服务向小爱音箱发送文字播报。

当前目标设备包括已验证的 `onemore.wifispeaker.sm4`。集成会在配置过程中自动读取 MiNA 设备列表和 `miotDID`，无需手工填写 DID。

## 功能

- Home Assistant 图形化配置
- 小米账号登录及验证码交互
- 自动发现账号下的 MiNA 音箱
- 支持选择一个或多个音箱
- 每台音箱创建独立的 Notify Entity
- Token 持久化，不保存账号密码
- 支持重新认证和重新选择设备

## 通过 HACS 安装

1. 打开 HACS。
2. 进入“集成”。
3. 右上角菜单选择“自定义存储库”。
4. 填入：`https://github.com/nymanyim/xiaoai-tts`
5. 类别选择“集成”。
6. 下载 **XiaoAI TTS** 并重启 Home Assistant。
7. 打开“设置 → 设备与服务 → 添加集成”，搜索 **XiaoAI TTS**。
8. 输入小米账号和密码，按提示完成验证码验证，然后选择音箱。

## 发送播报

在“开发者工具 → 操作”中调用：

```yaml
action: notify.send_message
target:
  entity_id: notify.xiaoai_speaker
data:
  message: "测试小爱音箱文字播报"
```

实际实体 ID 以 Home Assistant 创建的 Notify Entity 为准。

## 安全说明

- 密码仅用于首次登录或重新认证，不写入 Config Entry。
- 小米登录 Token 保存在 Home Assistant 的配置存储中，请保护好 Home Assistant 配置目录和备份。
- 播报依赖小米 MiNA 云服务及 `miservice==3.0.1`，不是局域网离线方案。

## 故障排查

- 找不到设备：确认音箱与登录账号位于同一小米账号下，并能在米家或小爱音箱应用中正常使用。
- 登录失败：确认账号密码正确，并完成短信或邮件验证码验证。
- 播报失败：先确认 Home Assistant 可以访问小米云服务，再重新加载或重新认证该集成。

## License

MIT