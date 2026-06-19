# 🛠️⚡ Bios Mod Suite - Analizador & Inyector UEFI

![Release](https://img.shields.io/badge/Release-v1.0.0-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

**Bios Mod Suite** es una herramienta automatizada de ingeniería inversa diseñada para auditar archivos de BIOS UEFI, extraer coordenadas de memoria físicas (Offsets) y generar *payloads* para inyectar modificaciones de hardware de bajo nivel. 

Especialmente útil para liberar límites térmicos (TDP), deshabilitar estrangulamiento térmico (PROCHOT) y aumentar la VRAM en placas base bloqueadas de fábrica (Ej: Arquitectura Intel Apollo Lake / Celeron J3355).

---

## ⚠️ Descargo de Responsabilidad (Disclaimer)
**PELIGRO:** Esta herramienta manipula memoria NVRAM y registros físicos (SMI/MMIO) del hardware. Ingresar valores incorrectos, modificar zonas críticas o aplicar un voltaje no soportado puede resultar en un **Brick irrecuperable** de la placa base. 
El autor no se hace responsable de daños al equipo, pérdida de garantía o pérdida de datos. **Úsalo bajo tu propio riesgo y responsabilidad.**

---

## 🚀 Características Principales
* **Motor Forense Integrado:** Desempaqueta y analiza archivos `.bin`/`.rom` automáticamente usando `UEFIExtract` y `UniversalIFRExtractor` en un entorno aislado.
* **Extracción Inteligente:** Localiza automáticamente variables críticas (Power Limits, C-States, DVMT Pre-Allocated, PROCHOT).
* **Generador de Payload:** Exporta scripts `.nsh` listos para ser ejecutados en una consola EFI Shell.
* **Navegador GPS para RU.efi:** Calculadora matemática que convierte los Offsets hexadecimales en coordenadas exactas (Fila y Columna) para evasión manual de *BIOS Lock*.

---

## 📖 Manual de Instrucciones

### Preparación del Entorno
1. Descarga la última versión de `bios_suite.exe` desde la pestaña **[Releases](../../releases)**.
2. Consigue un volcado (Dump) de la BIOS original de tu placa base en formato `.bin` o `.rom`.
3. Ejecuta el programa.

### Método 1: Inyección Automatizada (Para placas SIN protección)
Este método utiliza la consola de comandos de GRUB (`setup_var`). Es rápido, pero puede ser bloqueado por sistemas modernos.

1. Haz clic en **🔍 1. Escanear BIOS** y selecciona tu archivo `.bin`.
2. Una vez que la consola muestre los Offsets encontrados, haz clic en **💾 2. Payload Shell**.
3. Guarda el archivo como `startup.nsh`.
4. Formatea una memoria USB en **FAT32**.
5. Copia el archivo `startup.nsh` y tu ejecutable de shell (`bootx64.efi`) a la raíz del USB.
6. Arranca la PC desde el USB. El script se ejecutará automáticamente inyectando los valores.

---

### Método 2: Evasión de BIOS Lock con RU.efi (Para placas CON protección)
Si al intentar el Método 1 la consola te arroja el error `EFI_UNSUPPORTED`, significa que la placa base tiene protegido el acceso a los Runtime Services (Ej: Placas Aptio 5). Para saltar este *firewall*, usaremos acceso directo a memoria (MMIO) con el entorno visual **RU.efi**.

#### Paso A: Preparar el USB Camuflado
1. Formatea un USB en **FAT32**.
2. Crea una carpeta llamada `EFI`.
3. Dentro de `EFI`, crea una subcarpeta llamada `BOOT` (Ruta: `EFI\BOOT\`).
4. Descarga la herramienta **RU.efi**, pégala dentro de la carpeta `BOOT` y **cámbiale el nombre a `bootx64.efi`**. 
*(La raíz del USB debe estar totalmente vacía, sin archivos `startup.nsh`).*

#### Paso B: Obtener las Coordenadas
1. Abre **Bios Mod Suite**, escanea tu `.bin` (Botón 1).
2. Haz clic en **🗺️ 3. Navegador RU.efi**.
3. El programa calculará las coordenadas matemáticas. Tómale una foto a las instrucciones (Te dará una **Fila**, una **Columna** y un **Valor Hexadecimal** a inyectar).

#### Paso C: Inyección Física
1. Conecta el USB y arranca la computadora. Se abrirá la interfaz azul de RU.
2. Presiona las teclas **`Alt + =`** (o `Alt + +`) para abrir el menú de variables.
3. Con las flechas del teclado, baja hasta encontrar la carpeta **`Setup`** (o `SystemConfig`) y presiona **Enter**.
4. Verás una cuadrícula de números. Utiliza las teclas de dirección (Arriba/Abajo/Izquierda/Derecha) o la tecla Re Pág / Av Pág para navegar:
   * Busca la **Fila** (Ej: `0050`) en el eje vertical izquierdo.
   * Busca la **Columna** (Ej: `02`) en el eje horizontal superior.
5. Sitúate en la intersección exacta y **escribe el valor** que te dio el programa (Ej: `00` o `0F`).
6. Repite el proceso para todas las variables que desees modificar.
7. 💾 **CRÍTICO:** Presiona **`Ctrl + W`** para grabar los cambios físicamente en el chip NVRAM.
8. Presiona **`Alt + Q`** para salir o simplemente apaga el equipo.

¡Tu hardware ha sido modificado y los bloqueos han sido superados!

---

## 👨‍💻 Autor
Desarrollado por **Juan Carlos Rojas Bacilio** ([ProHacknet](https://github.com/ProHacknet))
Proyecto de auditoría de hardware e ingeniería inversa.
