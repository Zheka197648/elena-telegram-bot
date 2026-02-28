# В начале bot.py добавьте:
import logging
import sys

# Настройка логирования (видно в логах Koyeb)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# В конце файла, в функции main():
async def main():
    logger.info("🚀 Запуск бота...")
    logger.info(f"Bot token: {'***' + BOT_TOKEN[-5:] if BOT_TOKEN else 'NOT SET'}")
    logger.info(f" Elena chat ID: {ELENA_CHAT_ID}")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()
        logger.info("🛑 Бот остановлен")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())