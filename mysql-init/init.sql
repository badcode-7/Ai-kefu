-- 创建数据库用户并授权
CREATE USER IF NOT EXISTS 'deepseek'@'%' IDENTIFIED BY 'deepseek_password';
GRANT ALL PRIVILEGES ON deepseek_db.* TO 'deepseek'@'%';
FLUSH PRIVILEGES;