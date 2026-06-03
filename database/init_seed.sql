-- ============================================================
-- 种子数据 init_seed.sql  在 init_schema.sql 之后执行
-- 三角色 + 权限清单 + 角色权限关联
-- 超管账号由后端首次启动时按 .env 写入(密码需SM3哈希,不在SQL里)
-- ============================================================
SET NAMES utf8mb4;

-- ---- 角色 ----
INSERT INTO roles (role_code, role_name, description) VALUES
  ('SUPER_ADMIN',  '超级管理员',  '系统最高权限,可管理用户与角色分配'),
  ('LAB_ADMIN',    '实验室管理员', '管理设备与审批借用'),
  ('NORMAL_USER',  '普通用户',    '浏览设备/申请借用/查看本人记录');

-- ---- 权限清单 ----
INSERT INTO permissions (perm_code, perm_name, module) VALUES
  ('device:list',    '查看设备列表', 'device'),
  ('device:create',  '添加设备',     'device'),
  ('device:update',  '编辑设备',     'device'),
  ('device:delete',  '删除设备',     'device'),
  ('category:manage','管理设备分类', 'device'),
  ('borrow:apply',   '申请借用',     'borrow'),
  ('borrow:approve', '审批借用',     'borrow'),
  ('borrow:return',  '确认归还',     'borrow'),
  ('record:self',    '查看本人记录', 'record'),
  ('record:all',     '查看全部记录', 'record'),
  ('user:list',      '查看用户列表', 'user'),
  ('user:update',    '编辑用户',     'user'),
  ('user:assign',    '分配角色',     'user'),
  ('user:status',    '启用禁用账号', 'user'),
  ('log:view',       '查看操作日志', 'security'),
  ('security:view',  '安全监控面板', 'security'),
  ('stats:view',     '数据统计看板', 'stats'),
  ('role:manage',    '角色权限管理', 'system');

-- ---- 角色权限关联 ----
-- 超管:全部权限
INSERT INTO role_permissions (role_id, perm_id)
  SELECT (SELECT id FROM roles WHERE role_code='SUPER_ADMIN'), id FROM permissions;

-- 实验室管理员:设备管理 + 借用审批 + 全部记录 + 统计
INSERT INTO role_permissions (role_id, perm_id)
  SELECT (SELECT id FROM roles WHERE role_code='LAB_ADMIN'), id FROM permissions
  WHERE perm_code IN (
    'device:list','device:create','device:update','device:delete','category:manage',
    'borrow:approve','borrow:return','record:all','stats:view'
  );

-- 普通用户:看设备/申请借用/看本人记录
INSERT INTO role_permissions (role_id, perm_id)
  SELECT (SELECT id FROM roles WHERE role_code='NORMAL_USER'), id FROM permissions
  WHERE perm_code IN ('device:list','borrow:apply','record:self');
