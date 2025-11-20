# ✅ CHECKLIST - Sistema OCR Dual

**Tu guía rápida paso a paso**

---

## 📌 PASO 1: Configurar Campos Tesseract (⏱️ 5 min)

```bash
python test_tesseract_selector.py
```

### **Hacer:**
- [ ] Abre tu formulario web en el navegador
- [ ] Ejecuta el script
- [ ] Click en "📸 Capturar Formulario Web"
- [ ] Dibuja rectángulo sobre el formulario web completo
- [ ] Click en "⭕ primer_nombre"
- [ ] Dibuja rectángulo sobre el campo de primer nombre
- [ ] Repite para: segundo_nombre, primer_apellido, segundo_apellido
- [ ] Click en "💾 Guardar Configuración"
- [ ] Copia el YAML del diálogo
- [ ] Pega en `config/settings.yaml` (sección `ocr.tesseract.field_regions`)

### **Resultado:**
✅ Campos de Tesseract configurados correctamente

---

## 📌 PASO 2: Integrar en Aplicación (⏱️ 10-15 min)

Lee y sigue: **`INTEGRACION_RAPIDA.md`**

### **Hacer:**
- [ ] Abrir `src/presentation/ui/main_window.py`
- [ ] Agregar botón OCR dual (busca `_create_control_section`)
- [ ] Agregar señal `ocr_dual_processing_requested`
- [ ] Abrir `src/presentation/controllers/main_controller.py`
- [ ] Conectar señal en `_connect_signals()`
- [ ] Agregar método `handle_ocr_dual_processing()`
- [ ] Habilitar botón en `_perform_capture()`

### **Resultado:**
✅ Botón "🚀 Procesamiento OCR Dual" en la aplicación

---

## 📌 PASO 3: Probar (⏱️ 5 min)

```bash
./run.bat
```

### **Hacer:**
- [ ] Aplicación inicia sin errores
- [ ] Capturar formulario manuscrito (F4)
- [ ] Click en "🚀 Procesamiento OCR Dual (NUEVO)"
- [ ] Panel de progreso aparece
- [ ] Sistema procesa renglones automáticamente
- [ ] Presionar ESC para pausar
- [ ] Presionar F9 para reanudar
- [ ] Ver estadísticas al finalizar

### **Resultado:**
✅ Sistema OCR dual funcionando correctamente

---

## 📌 OPCIONAL: Ajustar Configuración

Editar `config/settings.yaml`:

### **Si validación es muy estricta:**
```yaml
validation:
  min_similarity: 0.80  # Cambiar de 0.85 a 0.80
```

### **Si formulario web carga lento:**
```yaml
automation:
  page_load_timeout: 7  # Aumentar de 5 a 7
```

### **Si digitación de cédulas falla:**
```yaml
automation:
  typing_delay_ms: 100  # Aumentar de 50 a 100
```

---

## 🐛 TROUBLESHOOTING RÁPIDO

### **"Error: No module named..."**
```bash
pip install -r requirements.txt
```

### **"Tesseract no lee nada"**
- Verifica que configuraste regiones en Paso 1
- Ejecuta `test_tesseract_selector.py` de nuevo

### **"Selector se cierra"**
- Ya está corregido ✅
- Si persiste, reinicia la aplicación

### **"Validación falla siempre"**
- Reduce `min_similarity` a 0.80 en `settings.yaml`

---

## 📚 REFERENCIAS RÁPIDAS

**Para TI:**
- `INTEGRACION_RAPIDA.md` - Cómo integrar
- `RESUMEN_FINAL.md` - Estado del proyecto
- `test_tesseract_selector.py` - Configurar campos

**Para CLAUDE CODE:**
- `CONTEXTO_CONTINUACION.md` - Contexto completo
- `PROGRESO_OCR_DUAL.md` - Progreso detallado

---

## ✅ CHECKLIST COMPLETO

### **Configuración:**
- [ ] Tesseract configurado
- [ ] settings.yaml actualizado

### **Integración:**
- [ ] Botón agregado en main_window.py
- [ ] Señal conectada
- [ ] Handler implementado en main_controller.py

### **Pruebas:**
- [ ] Aplicación inicia
- [ ] Captura funciona
- [ ] OCR dual funciona
- [ ] Pausas ESC/F9 funcionan
- [ ] Estadísticas se muestran

---

## 🎯 TIEMPO TOTAL ESTIMADO

- Paso 1: 5 min
- Paso 2: 15 min
- Paso 3: 5 min

**Total: 25 minutos** ⏱️

---

## 💡 TIP FINAL

**Si algo no funciona:**
1. Lee el error completo
2. Busca en `CONTEXTO_CONTINUACION.md` sección "Bugs Conocidos"
3. Abre nueva sesión Claude Code y comparte el error específico

**¡Todo está documentado! No te preocupes si algo falla.** 🚀

---

**Estado actual:** 90% completo
**Siguiente paso:** Configurar campos Tesseract
**Tiempo para terminar:** ~25 minutos

¡Éxito! 🎉
