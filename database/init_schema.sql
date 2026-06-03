-- ============================================================
-- 实验室设备管理系统 建表脚本  init_schema.sql
-- 引擎 InnoDB（支持事务，借用状态机需要）  字符集 utf8mb4
-- 共 9 张表，满足第三范式
-- ============================================================
SET NAMES utf8mb4;

-- ========== 第一组：RBAC 权限体系（5 张）==========

-- 用户表
CREATE TABLE users (
  id              BIGINT       PRIMARY KEY AUTO_INCREMENT,
  username        VARCHAR(20)  NOT NULL UNIQUE COMMENT '登录名 4-20位',
  password_hash   VARCHAR(255) NOT NULL        COMMENT '格式 盐$哈希(SM3)',
  real_name       VARCHAR(50)  NOT NULL,
  phone_enc       VARCHAR(255)                 COMMENT 'SM4加密后的手机号(hex)',
  email           VARCHAR(100) UNIQUE,
  status          TINYINT      NOT NULL DEFAULT 1 COMMENT '1正常 0禁用',
  fail_count      INT          NOT NULL DEFAULT 0 COMMENT '连续登录失败次数',
  lock_until      DATETIME                     COMMENT '锁定截止时间,NULL未锁',
  created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户';

-- 角色表
CREATE TABLE roles (
  id          BIGINT      PRIMARY KEY AUTO_INCREMENT,
  role_code   VARCHAR(50) NOT NULL UNIQUE COMMENT 'SUPER_ADMIN/LAB_ADMIN/NORMAL_USER',
  role_name   VARCHAR(50) NOT NULL,
  description VARCHAR(200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色';

-- 权限表
CREATE TABLE permissions (
  id          BIGINT      PRIMARY KEY AUTO_INCREMENT,
  perm_code   VARCHAR(50) NOT NULL UNIQUE COMMENT '如 device:create',
  perm_name   VARCHAR(50) NOT NULL        COMMENT '中文名,界面显示',
  module      VARCHAR(50) NOT NULL        COMMENT '所属模块,分组用'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='权限';

-- 用户-角色 关联（多对多）
CREATE TABLE user_roles (
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户角色关联';

-- 角色-权限 关联（多对多）
CREATE TABLE role_permissions (
  role_id BIGINT NOT NULL,
  perm_id BIGINT NOT NULL,
  PRIMARY KEY (role_id, perm_id),
  FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
  FOREIGN KEY (perm_id) REFERENCES permissions(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色权限关联';

-- ========== 第二组：设备管理（2 张）==========

CREATE TABLE device_categories (
  id          BIGINT      PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(200)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备分类';

CREATE TABLE devices (
  id            BIGINT       PRIMARY KEY AUTO_INCREMENT,
  device_no     VARCHAR(50)  NOT NULL UNIQUE COMMENT '如 LAB-ELE-001',
  name          VARCHAR(100) NOT NULL,
  model         VARCHAR(100)                 COMMENT '型号规格',
  category_id   BIGINT       NOT NULL,
  location      VARCHAR(100)                 COMMENT '存放位置',
  status        VARCHAR(20)  NOT NULL DEFAULT 'IDLE'
                COMMENT 'IDLE空闲/BORROWED借出/REPAIRING维修/SCRAPPED报废',
  purchase_date DATE,
  asset_value   DECIMAL(10,2),
  image_url     VARCHAR(255),
  remark        VARCHAR(255),
  is_deleted    TINYINT      NOT NULL DEFAULT 0 COMMENT '软删除 1已删',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES device_categories(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='设备';

-- ========== 第三组：借用管理（1 张，核心业务）==========

CREATE TABLE borrow_records (
  id                  BIGINT      PRIMARY KEY AUTO_INCREMENT,
  user_id             BIGINT      NOT NULL COMMENT '申请人',
  device_id           BIGINT      NOT NULL,
  apply_time          DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  apply_reason        VARCHAR(255),
  expected_return_date DATE       NOT NULL COMMENT '预计归还,逾期检测基础',
  status              VARCHAR(20) NOT NULL DEFAULT 'PENDING'
    COMMENT 'PENDING/APPROVED/REJECTED/BORROWED/RETURN_PENDING/RETURNED/OVERDUE',
  approver_id         BIGINT      COMMENT '审批人',
  approve_time        DATETIME,
  reject_reason       VARCHAR(255),
  actual_return_time  DATETIME    COMMENT '用户申请归还时间',
  return_confirm_time DATETIME    COMMENT '管理员确认归还时间',
  return_confirmer_id BIGINT,
  remark              VARCHAR(255),
  FOREIGN KEY (user_id)   REFERENCES users(id),
  FOREIGN KEY (device_id) REFERENCES devices(id),
  FOREIGN KEY (approver_id) REFERENCES users(id),
  FOREIGN KEY (return_confirmer_id) REFERENCES users(id),
  INDEX idx_status (status),
  INDEX idx_user (user_id),
  INDEX idx_device (device_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='借用记录';

-- ========== 第四组：安全审计（1 张，只追加写）==========

CREATE TABLE operation_logs (
  id          BIGINT      PRIMARY KEY AUTO_INCREMENT,
  operator_id BIGINT      COMMENT '操作者ID,可空(如登录失败时未知)',
  username    VARCHAR(50) COMMENT '冗余存储,免联表',
  action      VARCHAR(50) NOT NULL COMMENT 'LOGIN_SUCCESS/LOGIN_FAIL/DEVICE_CREATE...',
  target      VARCHAR(100) COMMENT '如 设备ID:15',
  detail      TEXT        COMMENT 'JSON,记录具体改动',
  ip          VARCHAR(50),
  user_agent  VARCHAR(255),
  created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_action (action),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志';
