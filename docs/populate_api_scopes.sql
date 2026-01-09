-- ============================================================================
-- API Permission Scopes - Initial Catalog
-- ============================================================================
-- Este script popula el catálogo de scopes disponibles para API keys
-- Ejecutar DESPUÉS de crear el schema de base de datos
-- ============================================================================

-- Limpiar scopes existentes (solo en desarrollo/testing)
-- TRUNCATE TABLE api_permission_scopes RESTART IDENTITY CASCADE;

-- ============================================================================
-- DOCUMENTS SCOPES
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(1, 'documents:read', 'Read Documents', 'View document metadata and content', 'documents', true),
(2, 'documents:write', 'Write Documents', 'Create and update documents', 'documents', true),
(3, 'documents:delete', 'Delete Documents', 'Delete documents', 'documents', true),
(4, 'documents:all', 'All Document Operations', 'Full access to document operations', 'documents', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VERIFICATIONS SCOPES (Cédula Verification)
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(10, 'verifications:read', 'Read Verifications', 'View verification requests and results', 'verifications', true),
(11, 'verifications:create', 'Create Verifications', 'Submit new verification requests', 'verifications', true),
(12, 'verifications:update', 'Update Verifications', 'Update verification status or metadata', 'verifications', true),
(13, 'verifications:all', 'All Verification Operations', 'Full access to verification operations', 'verifications', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- OCR SCOPES
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(20, 'ocr:extract', 'OCR Extract', 'Extract text from images using OCR', 'ocr', true),
(21, 'ocr:batch', 'OCR Batch Processing', 'Process multiple images in batch', 'ocr', true),
(22, 'ocr:all', 'All OCR Operations', 'Full access to OCR operations', 'ocr', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- USERS SCOPES
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(30, 'users:read', 'Read Users', 'View user profiles and information', 'users', true),
(31, 'users:write', 'Write Users', 'Create and update user profiles', 'users', true),
(32, 'users:delete', 'Delete Users', 'Delete user accounts', 'users', true),
(33, 'users:all', 'All User Operations', 'Full access to user operations', 'users', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- API KEYS SCOPES (Meta-scopes para gestión de API keys)
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(40, 'apikeys:read', 'Read API Keys', 'View own API keys', 'apikeys', true),
(41, 'apikeys:create', 'Create API Keys', 'Create new API keys', 'apikeys', true),
(42, 'apikeys:revoke', 'Revoke API Keys', 'Revoke own API keys', 'apikeys', true),
(43, 'apikeys:all', 'All API Key Operations', 'Full access to API key management', 'apikeys', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SUBSCRIPTIONS SCOPES
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(50, 'subscriptions:read', 'Read Subscriptions', 'View subscription details', 'subscriptions', true),
(51, 'subscriptions:write', 'Write Subscriptions', 'Create and update subscriptions', 'subscriptions', true),
(52, 'subscriptions:cancel', 'Cancel Subscriptions', 'Cancel subscription plans', 'subscriptions', true),
(53, 'subscriptions:all', 'All Subscription Operations', 'Full access to subscription operations', 'subscriptions', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- INVOICES SCOPES
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(60, 'invoices:read', 'Read Invoices', 'View invoices and payment history', 'invoices', true),
(61, 'invoices:download', 'Download Invoices', 'Download invoice PDFs', 'invoices', true),
(62, 'invoices:all', 'All Invoice Operations', 'Full access to invoice operations', 'invoices', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- USAGE SCOPES (Analytics y métricas)
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(70, 'usage:read', 'Read Usage', 'View usage statistics and metrics', 'usage', true),
(71, 'usage:export', 'Export Usage', 'Export usage data in various formats', 'usage', true),
(72, 'usage:all', 'All Usage Operations', 'Full access to usage analytics', 'usage', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- ADMIN SCOPES (Super privilegios)
-- ============================================================================

INSERT INTO api_permission_scopes (id, code, name, description, category, is_active) VALUES
(100, 'admin:users', 'Admin Users', 'Manage all users (not just own)', 'admin', true),
(101, 'admin:apikeys', 'Admin API Keys', 'Manage all API keys (not just own)', 'admin', true),
(102, 'admin:scopes', 'Admin Scopes', 'Manage API permission scopes catalog', 'admin', true),
(103, 'admin:all', 'Admin All', 'Full administrative access to all resources', 'admin', true)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verificar que los scopes se insertaron correctamente
SELECT
    category,
    COUNT(*) as scope_count,
    STRING_AGG(code, ', ' ORDER BY id) as scopes
FROM api_permission_scopes
WHERE is_active = true
GROUP BY category
ORDER BY category;

-- Contar total de scopes activos
SELECT COUNT(*) as total_active_scopes
FROM api_permission_scopes
WHERE is_active = true;

-- ============================================================================
-- NOTAS
-- ============================================================================

-- 1. Scopes con ":all" son wildcards que dan acceso completo a esa categoría
-- 2. "admin:all" es el super wildcard que da acceso a TODO
-- 3. IDs están espaciados por 10 para permitir insertar scopes adicionales
-- 4. El flag "is_active" permite deshabilitar scopes sin borrarlos
-- 5. Al crear API keys, validar contra este catálogo
-- 6. Categorías actuales:
--    - documents: Gestión de documentos
--    - verifications: Verificación de cédulas
--    - ocr: Extracción de texto
--    - users: Gestión de usuarios
--    - apikeys: Gestión de API keys
--    - subscriptions: Suscripciones
--    - invoices: Facturas
--    - usage: Métricas de uso
--    - admin: Privilegios administrativos
