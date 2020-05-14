import configparser
import mysql.connector as mysql

# loading database information from config file
config = configparser.ConfigParser()
config.read('config.ini')
host = config["DEFAULT"]["HOST"]
user = config["DEFAULT"]["DATABASE_USERNAME"]
password = config["DEFAULT"]["PASSWORD"]
dbname = config["DEFAULT"]["DATABASE_NAME"]

# connecting to the database using 'connect()' method
db = mysql.connect(
    host = host,
    user = user,
    passwd = password,
)

cursor = db.cursor()
cursor.execute("CREATE DATABASE alpaca_stocks")

db = mysql.connect(
    host = host,
    user = user,
    passwd = password,
    database = dbname
)
cursor = db.cursor()
cursor.execute("CREATE TABLE `trading_history` ( `id` INT(11) NOT NULL AUTO_INCREMENT, `stock_id` VARCHAR(255) DEFAULT NULL COMMENT 'stock_id', `symbol` VARCHAR(255) DEFAULT NULL COMMENT 'stock_name', `buy_price` FLOAT DEFAULT NULL COMMENT 'buy price', `sell_price` FLOAT DEFAULT NULL COMMENT 'sell_price', `buy_above_open_price` FLOAT DEFAULT NULL COMMENT 'buy % above open 3', `sell_above_open_price` FLOAT DEFAULT NULL COMMENT 'sell % above open 1', `buy_below_open_price` FLOAT DEFAULT NULL COMMENT 'buy % below the open 1.5', `sell_below_open_price` FLOAT DEFAULT NULL COMMENT 'sell % below the open 1.75', `buy_below_high_price` FLOAT DEFAULT NULL COMMENT 'buy % below the high 0.5', `sell_below_high_price` FLOAT DEFAULT NULL COMMENT 'sell % below the high price 0.35', `buy_above_low_price` FLOAT DEFAULT NULL COMMENT 'buy % above the low 1', `sell_above_low_price` FLOAT DEFAULT NULL COMMENT 'sell % above the high 0.25', `buy_below_previous_close_1` FLOAT DEFAULT NULL COMMENT 'buy % below previous close 1.5', `sell_below_previous_close_1` FLOAT DEFAULT NULL COMMENT 'sell % below previous close 0.75', `buy__below_previous_close_2` FLOAT DEFAULT NULL COMMENT 'buy % below previous 0.5', `sell_below_previous_close_2` FLOAT DEFAULT NULL COMMENT 'sell % below previous 0.5', `stock_num` INT(11)  DEFAULT NULL COMMENT 'stock number', `max_dollars` FLOAT DEFAULT NULL COMMENT 'max dollars', `start_time` DATETIME DEFAULT NULL COMMENT 'trade start time', `end_time` DATETIME DEFAULT NULL COMMENT 'trade end time', PRIMARY KEY (`id`) ) ENGINE=INNODB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8; ")
cursor.execute("CREATE TABLE `trading_number_per_day` (`symbol` varchar(60) NOT NULL, `max_num` int(11) DEFAULT NULL, `trade_num` varchar(11) DEFAULT NULL, `trade_time` date DEFAULT NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8;")