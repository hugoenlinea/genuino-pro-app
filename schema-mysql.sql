-- schema-mysql.sql
SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fullname` text NOT NULL,
  `email` text NOT NULL,
  `password_hash` text NOT NULL,
  `role` text NOT NULL DEFAULT 'Vendedor',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `customers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_name` text NOT NULL,
  `nit_ci` text NOT NULL,
  `address` text,
  `contact_person` text,
  `contact_email` text,
  `contact_phone` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nit_ci` (`nit_ci`(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `app_settings` (
  `setting_key` varchar(255) NOT NULL,
  `setting_value` text,
  PRIMARY KEY (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `quotes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quote_number` text NOT NULL,
  `customer_id` int NOT NULL,
  `user_id` int NOT NULL,
  `total_amount` real NOT NULL,
  `status` text NOT NULL,
  `rejection_reason` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `quote_number` (`quote_number`(255)),
  KEY `customer_id` (`customer_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `quotes_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`),
  CONSTRAINT `quotes_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quote_id` int NOT NULL,
  `order_status` text NOT NULL,
  `last_update` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `quote_id` (`quote_id`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`quote_id`) REFERENCES `quotes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `catalog_types` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` text NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `catalog` (
  `id` int NOT NULL AUTO_INCREMENT,
  `type_id` int NOT NULL,
  `code` text NOT NULL,
  `description` text NOT NULL,
  `unit_price` real NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `type_id_code` (`type_id`,`code`(255)),
  KEY `type_id` (`type_id`),
  CONSTRAINT `catalog_ibfk_1` FOREIGN KEY (`type_id`) REFERENCES `catalog_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `quote_items` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quote_id` int NOT NULL,
  `type_id` int NOT NULL,
  `code` text,
  `description` text NOT NULL,
  `quantity` int NOT NULL,
  `unit_price` real NOT NULL,
  `subtotal` real NOT NULL,
  PRIMARY KEY (`id`),
  KEY `quote_id` (`quote_id`),
  KEY `type_id` (`type_id`),
  CONSTRAINT `quote_items_ibfk_1` FOREIGN KEY (`quote_id`) REFERENCES `quotes` (`id`),
  CONSTRAINT `quote_items_ibfk_2` FOREIGN KEY (`type_id`) REFERENCES `catalog_types` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET foreign_key_checks = 1;