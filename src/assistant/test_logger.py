import unittest
import logging
import os
from assistant.graph import init_logger, close_logger

class TestLoggerFunctions(unittest.TestCase):
    def setUp(self):
        self.log_file = "test_log.log"
        self.logger_name = "test_logger"
        
        # 確保測試開始前沒有舊的日誌檔案
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def tearDown(self):
        # 測試結束後清除日誌檔案
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_init_logger(self):
        global logger
        logger = init_logger(self.logger_name, self.log_file)
        
        # 檢查 logger 是否成功創建
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, self.logger_name)
        self.assertTrue(any(isinstance(h, logging.FileHandler) for h in logger.handlers))
        
        # 測試 logger 是否能成功寫入
        logger.info("Test message")
        with open(self.log_file, "r", encoding="utf-8") as f:
            log_content = f.read()
        
        self.assertIn("Test message", log_content)
        
    def test_close_logger(self):
        global logger
        logger = init_logger(self.logger_name, self.log_file)
        close_logger()
        
        # 檢查 logger 是否被清除
        self.assertFalse(logger.handlers)
        
if __name__ == "__main__":
    unittest.main()