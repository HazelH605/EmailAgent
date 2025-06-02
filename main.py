import time
import config
import utils
import graph

def main():
    # 加载配置
    config_data = config.load_config()

    # 验证配置
    if not config.validate_config(config_data):
        return

    # 设置日志
    logger = utils.setup_logging(config_data['logging']['dir'])
    logger.info("邮件处理Agent启动")

    # 创建LangGraph工作流
    workflow = graph.create_workflow()

    # 生成工作流可视化图
    try:
        graph_image = workflow.get_graph().draw_mermaid_png()
        with open("workflow_diagram.png", "wb") as f:
            f.write(graph_image)
        logger.info("工作流图已保存为 workflow_diagram.png")
    except Exception as e:
        logger.error(f"生成工作流图失败: {str(e)}")

    # 获取未读邮件
    imap, emails = utils.fetch_unread_emails(config_data, logger)

    if not imap:
        logger.error("无法连接邮箱，程序退出")
        return

    # 处理邮件数量限制
    max_emails = config_data['processing']['max_emails']
    if len(emails) > max_emails:
        logger.info(f"限制处理邮件数量为 {max_emails}/{len(emails)}")


    # 处理每封邮件
    for email_data in emails:
        logger.info(f"开始处理邮件: {email_data['subject']}")

        # 初始化状态
        initial_state = {
            "email_data": email_data,
            "classification": None,
            "process_result": None,
            "config": config_data,
            "logger": logger
        }

        try:
            # 执行工作流
            result = workflow.invoke(initial_state)

            # 标记邮件为已读
            utils.mark_email_as_read(imap, email_data['id'], logger)

            logger.info(f"邮件处理完成: {email_data['subject']}")

        except Exception as e:
            logger.error(f"处理邮件时出错: {str(e)}")

        # 短暂暂停，避免速率限制
        time.sleep(2)

    # 关闭IMAP连接
    utils.close_imap_connection(imap, logger)
    logger.info("邮件处理Agent结束运行")

if __name__ == '__main__':
    main()