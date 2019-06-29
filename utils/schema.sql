BEGIN TRANSACTION;
CREATE TABLE "OrderReport" (
	`date`	TIMESTAMP,
	`orderId`	TEXT,
	`clOrdId`	TEXT,
	`proprietary`	TEXT,
	`execId`	TEXT,
	`accountId_id`	TEXT,
	`instrumentId_marketId`	TEXT,
	`instrumentId_symbol`	TEXT,
	`price`	REAL,
	`orderQty`	INTEGER,
	`ordType`	TEXT,
	`side`	TEXT,
	`timeInForce`	TEXT,
	`transactTime`	TEXT,
	`avgPx`	REAL,
	`lastPx`	REAL,
	`lastQty`	INTEGER,
	`cumQty`	INTEGER,
	`leavesQty`	INTEGER,
	`iceberg`	TEXT,
	`displayQty`	INTEGER,
	`status`	TEXT,
	`text`	TEXT,
	`origClordId`	TEXT,
	`wsClOrdId`	TEXT
);
CREATE TABLE "IRFX20" (
	`date`	TEXT,
	`Ticker`	TEXT,
	`OF_price`	REAL,
	`OF_size`	REAL,
	`LA_price`	REAL,
	`LA_size`	REAL,
	`BI_price`	REAL,
	`BI_size`	REAL,
	`LA_date`	TEXT,
	`OI_date`	INTEGER,
	`OI_price`	REAL,
	`OI_size`	INTEGER,
	`SE_date`	INTEGER,
	`SE_price`	REAL,
	`IV`	REAL,
	`TV`	INTEGER
);
CREATE INDEX "ix_OrderReport_date"ON "OrderReport" ("date")




;
CREATE INDEX `ix_MarketData_date` ON `MarketData` (`date` ASC)








;
COMMIT;
