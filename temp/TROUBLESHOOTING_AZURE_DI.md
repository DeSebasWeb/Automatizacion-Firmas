# Troubleshooting Azure Document Intelligence

## Problema: API no responde / Timeout Infinito

### Síntomas

- Endpoint `/e14/azure-di/senado` no responde después de 1-2 minutos
- Cliente recibe timeout o la conexión se cuelga
- Logs muestran requests GET repetitivos cada segundo:
  ```
  Request URL: 'https://...cognitiveservices.azure.com/.../analyzeResults/...'
  Response status: 200
  'retry-after': '1'
  ```

### Causa

Azure Document Intelligence puede quedar atascado en estado `running` cuando:
1. El modelo custom tiene problemas de configuración
2. El documento es demasiado complejo para el modelo
3. El servicio de Azure está experimentando problemas
4. El documento tiene páginas corruptas o ilegibles

El SDK de Azure por defecto hace polling **SIN TIMEOUT**, esperando indefinidamente.

### Solución

**✅ IMPLEMENTADO** - Timeout configurado en `azure_di_adapter.py`:

```python
timeout_seconds = self.config.get("azure_di.polling_timeout_seconds", 120)
result = poller.result(timeout=timeout_seconds)
```

### Configuración

En `config/settings.yaml`:

```yaml
azure_di:
  model_id: "e14-senado-v1"
  polling_timeout_seconds: 120  # Ajustar según necesidad
```

**Valores recomendados:**
- Documentos pequeños (1-3 páginas): `60` segundos
- Documentos medianos (4-7 páginas): `90` segundos
- Documentos grandes (8-11 páginas): `120` segundos
- Testing/Debug: `180` segundos

### Debugging

#### 1. Verificar logs de Azure DI

```bash
tail -f logs/app_$(date +%Y%m%d).log | grep azure
```

Buscar:
- `analyzing_e14_document` - Inicio del análisis
- `waiting_for_azure_analysis` - Polling iniciado
- `e14_document_analyzed` - Éxito
- `azure_di_api_error` - Error de Azure

#### 2. Verificar estado del servicio Azure

```bash
# En PowerShell o CMD
curl -X GET "https://<your-endpoint>.cognitiveservices.azure.com/documentintelligence/documentModels?api-version=2024-11-30" ^
  -H "Ocp-Apim-Subscription-Key: <your-key>"
```

Debe retornar lista de modelos disponibles.

#### 3. Test de timeout

Ejecutar script de prueba:

```bash
python utils/test_azure_di_timeout.py
```

El script:
- Carga un PDF de prueba
- Mide tiempo de procesamiento
- Verifica que el timeout funcione correctamente

#### 4. Revisar modelo custom

En Azure Portal:
1. Ir a tu recurso Document Intelligence
2. Document Intelligence Studio → Models
3. Verificar que `e14-senado-v1` esté en estado "Ready"
4. Revisar métricas de accuracy del modelo

### Solución Alternativa (Temporal)

Si el timeout persiste, usar endpoint sin parser adaptativo:

```bash
# Endpoint básico (sin parser, solo campos raw)
POST /e14/azure-di
```

Este endpoint es más rápido porque no ejecuta el parsing complejo.

### Prevención

1. **Monitorear tiempos de respuesta:**
   - Agregar métricas de latencia en logs
   - Alertas si processing > 90 segundos

2. **Validar PDFs antes de enviar:**
   - Verificar tamaño < 50MB
   - Verificar número de páginas <= 11
   - Verificar que no estén corruptos

3. **Implementar retry logic:**
   ```python
   max_retries = 3
   for attempt in range(max_retries):
       try:
           result = use_case.execute(pdf_bytes)
           if result:
               break
       except TimeoutError:
           if attempt == max_retries - 1:
               raise
           time.sleep(5)
   ```

## Problema: Parsing Incorrecto

### Síntomas

- Parser retorna datos pero están mal estructurados
- Faltan partidos o candidatos
- Votos mal asignados

### Debugging

1. **Revisar campos limpios:**
   ```bash
   cat temp/cleaned_fields.json | jq .
   ```

2. **Comparar con output parseado:**
   ```bash
   cat temp/e14_senado_parsed.json | jq .
   ```

3. **Ejecutar parser standalone:**
   ```bash
   python utils/test_e14_senado_parser.py
   ```

4. **Revisar logs de parsing:**
   ```bash
   grep "e14_senado_parser" logs/app_$(date +%Y%m%d).log
   ```

### Causa Común

- Azure DI no detectó todos los campos (modelo necesita reentrenamiento)
- Cambios en formato del formulario E-14
- Páginas mal escaneadas o borrosas

### Solución

1. **Verificar calidad del PDF:**
   - Resolución mínima: 300 DPI
   - Sin manchas ni borrones
   - Texto legible

2. **Reentrenar modelo Azure DI:**
   - Agregar más ejemplos de entrenamiento
   - Etiquetar campos faltantes
   - Re-deployar modelo

3. **Ajustar parser:**
   - Revisar regex patterns en `parsing_utils.py`
   - Agregar más patrones de detección de página

## Problema: Credenciales Inválidas

### Síntomas

```
azure_di_credentials_missing
azure_di_client_not_available
```

### Solución

1. Verificar `.env`:
   ```bash
   cat .env | grep AZURE_DI
   ```

2. Debe contener:
   ```
   AZURE_DI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_DI_KEY=your_subscription_key
   ```

3. Verificar conectividad:
   ```bash
   curl $AZURE_DI_ENDPOINT/documentintelligence/info?api-version=2024-11-30 \
     -H "Ocp-Apim-Subscription-Key: $AZURE_DI_KEY"
   ```

## Contacto

Para problemas no resueltos:
1. Revisar logs completos en `logs/`
2. Crear issue en repositorio con:
   - Logs relevantes
   - PDF de ejemplo (si es posible)
   - Configuración de `settings.yaml`
