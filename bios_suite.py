import sys
import os
import re
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox

# ==========================================
# RUTAS DINÁMICAS (COMPATIBILIDAD PYINSTALLER)
# ==========================================
def resolver_ruta(ruta_relativa):
    """Obtiene la ruta absoluta de los motores, ya sea en modo desarrollo o compilado en el .exe"""
    try:
        # Cuando es un .exe, PyInstaller descomprime los motores en esta carpeta temporal secreta
        base_path = sys._MEIPASS
    except Exception:
        # Si lo corres desde tu editor, busca en la misma carpeta del script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, ruta_relativa)

RUTA_UEFIEXTRACT = resolver_ruta("UEFIExtract.exe")
RUTA_IFREXTRACTOR = resolver_ruta("UniversalIFRExtractor.exe")
CARPETA_MOTORES = os.path.dirname(RUTA_UEFIEXTRACT)

# MEMORIA GLOBAL PARA EL PAYLOAD Y LA GUÍA
variables_globales = [] 

# ==========================================
# REGLAS DE DIAGNÓSTICO PARA EL MODDING
# ==========================================
REGLAS_OPTIMIZACION = {
    "power limit": "MODIFICACIÓN: Habilitar (01) o subir el valor Hex para aumentar los Watts.",
    "tdp": "MODIFICACIÓN: Subir valor Hex al máximo térmico que soporte tu disipador.",
    "prochot": "MODIFICACIÓN: Cambiar a 00 (Disabled) para evitar asfixia térmica externa.",
    "c-state": "MODIFICACIÓN: Cambiar a 00 para máximo rendimiento.",
    "c state": "MODIFICACIÓN: Cambiar a 00 para máximo rendimiento.",
    "eist": "MODIFICACIÓN: Mantener en 01 (Enabled) para el Turbo Boost.",
    "speedstep": "MODIFICACIÓN: Mantener en 01 (Enabled) para el Turbo Boost.",
    "rc6": "MODIFICACIÓN: Cambiar a 00 (Disabled) para quitar latencia gráfica.",
    "standby": "MODIFICACIÓN: Cambiar a 00 para mantener componentes siempre alerta.",
    "dvmt": "MODIFICACIÓN: Subir valor para asignar más VRAM (Ej: 256MB o 512MB)."
}

# ==========================================
# EXPRESIONES REGULARES (TRADUCTOR UNIVERSAL)
# ==========================================
PATRON_RS = re.compile(r"(?:OneOf|Numeric|Checkbox)\s+Prompt:\s+\"([^\"]+)\".*?VarStoreId:\s+(0x[0-9a-fA-F]+).*?VarOffset:\s+(0x[0-9a-fA-F]+)", re.IGNORECASE)
PATRON_APTIO5 = re.compile(r"(?:One Of|Numeric|Checkbox):\s+(.+?),\s+VarStoreInfo.*?:\s+(0x[0-9a-fA-F]+),\s+VarStore:\s+(0x[0-9a-fA-F]+)", re.IGNORECASE)
PATRON_APTIO4 = re.compile(r"Setting:\s+(.+?),\s+Variable:\s+(0x[0-9a-fA-F]+)", re.IGNORECASE)

def imprimir(texto, tag="normal"):
    """Imprime resultados en la consola visual sin que el usuario pueda borrarlos."""
    txt_consola.configure(state='normal')
    txt_consola.insert(tk.END, texto, tag)
    txt_consola.configure(state='disabled')
    txt_consola.yview(tk.END)
    ventana.update()

def procesar_txt_ifr(ruta_txt):
    """Filtra el texto crudo y extrae las coordenadas de hardware."""
    resultados = []
    try:
        with open(ruta_txt, 'r', encoding='utf-8', errors='ignore') as archivo:
            for linea in archivo:
                match_rs = PATRON_RS.search(linea)
                match_aptio5 = PATRON_APTIO5.search(linea)
                match_aptio4 = PATRON_APTIO4.search(linea)

                if match_rs:
                    nombre, varstore, offset = match_rs.group(1).strip(), match_rs.group(2).upper(), match_rs.group(3).upper()
                elif match_aptio5:
                    nombre, offset, varstore = match_aptio5.group(1).strip(), match_aptio5.group(2).upper(), match_aptio5.group(3).upper()
                elif match_aptio4:
                    nombre, offset, varstore = match_aptio4.group(1).strip(), match_aptio4.group(2).upper(), "0X1"
                else:
                    continue

                for clave, recomendacion in REGLAS_OPTIMIZACION.items():
                    if clave in nombre.lower():
                        resultados.append({"nombre": nombre, "offset": offset, "varstore": varstore, "recomendacion": recomendacion})
                        break
    except Exception:
        pass
    return resultados

def iniciar_pipeline_automatizado():
    """Ejecuta el escaneo forense de la BIOS y guarda los Offsets en RAM."""
    global variables_globales
    variables_globales = [] # Limpiar memoria de escaneos anteriores

    if not os.path.exists(RUTA_UEFIEXTRACT) or not os.path.exists(RUTA_IFREXTRACTOR):
        messagebox.showerror("Error Crítico", f"No se encontraron los motores de extracción.\nPor favor, verifica que UEFIExtract.exe y UniversalIFRExtractor.exe estén junto al programa.")
        return

    ruta_bios = filedialog.askopenfilename(
        title="Selecciona la BIOS Original (.rom, .bin)", 
        filetypes=[("Archivos de BIOS", "*.bin;*.rom;*.fd;*.cap"), ("Todos", "*.*")]
    )
    if not ruta_bios: return

    txt_consola.configure(state='normal')
    txt_consola.delete('1.0', tk.END)
    txt_consola.configure(state='disabled')

    imprimir(f"📂 INICIANDO INGENIERÍA INVERSA: {os.path.basename(ruta_bios)}\n", "titulo")
    imprimir("="*75 + "\n", "normal")

    ruta_dump = ruta_bios + ".dump"

    try:
        imprimir("⚙️ [1/4] Desempaquetando estructura binaria...\n", "alerta")
        subprocess.run([RUTA_UEFIEXTRACT, ruta_bios, "all"], capture_output=True, creationflags=0x08000000)

        if not os.path.exists(ruta_dump):
            imprimir("[-] Error: UEFIExtract rechazó la cápsula.\n", "offset")
            return

        imprimir("🔍 [2/4] Buscando módulos maestros de hardware...\n", "alerta")
        candidatos = []
        for root, dirs, files in os.walk(ruta_dump):
            if "setup" in root.lower() and "pe32" in root.lower():
                for file in files:
                    if file.lower() == "body.bin":
                        candidatos.append(os.path.join(root, file))

        if not candidatos:
            imprimir("[-] Error: No se encontraron módulos Setup.\n", "offset")
            return

        imprimir(f"[*] Se detectaron {len(candidatos)} módulos. Iniciando Sandbox...\n", "normal")
        imprimir("🧠 [3/4] Forzando motor visual en entorno aislado...\n", "alerta")
        
        resultados_totales = []
        ruta_temp_bin = os.path.join(CARPETA_MOTORES, "temp_sandbox.bin")

        for i, candidato in enumerate(candidatos):
            try:
                shutil.copy(candidato, ruta_temp_bin)
                subprocess.run([RUTA_IFREXTRACTOR, "temp_sandbox.bin"], cwd=CARPETA_MOTORES, capture_output=True, creationflags=0x08000000)
                
                for archivo in os.listdir(CARPETA_MOTORES):
                    if "temp_sandbox" in archivo.lower() and archivo.lower().endswith(".txt"):
                        ruta_txt_generado = os.path.join(CARPETA_MOTORES, archivo)
                        resultados_totales.extend(procesar_txt_ifr(ruta_txt_generado))
                        os.remove(ruta_txt_generado)
                
                if os.path.exists(ruta_temp_bin):
                    os.remove(ruta_temp_bin)
            except Exception:
                pass

        if resultados_totales:
            # Filtrar duplicados exactos y guardar en RAM
            variables_globales = [dict(t) for t in {tuple(d.items()) for d in resultados_totales}]
            
            imprimir(f"\n[+] ÉXITO: Se encontraron {len(variables_globales)} opciones críticas.\n\n", "exito")
            
            varstores = set(res["varstore"] for res in variables_globales)
            
            for v_store in varstores:
                imprimir(f"📦 REPOSITORIO (VarStore ID): {v_store}\n", "titulo")
                imprimir("-" * 75 + "\n", "normal")
                for res in variables_globales:
                    if res["varstore"] == v_store:
                        imprimir(f"   ➤ VARIABLE: {res['nombre']}\n", "variable")
                        imprimir(f"      📍 OFFSET: {res['offset']}\n", "offset")
                        imprimir(f"      ⚙️ ACCIÓN: {res['recomendacion']}\n\n", "accion")
                        
            imprimir("\n💡 CONSEJO: Usa el Botón 2 (Inyección) o el Botón 3 (Modo Manual).\n", "exito")
        else:
            imprimir("\n[-] El escáner terminó, pero la placa base está bloqueada de fábrica.\n", "alerta")

    finally:
        imprimir("🧹 [4/4] Limpiando archivos temporales...\n", "normal")
        shutil.rmtree(ruta_dump, ignore_errors=True)
        imprimir("✅ Pipeline finalizado y asegurado.\n", "normal")


def generar_payload_usb():
    """Genera el archivo startup.nsh limpio (ASCII), muestra iconos en la GUI."""
    if not variables_globales:
        messagebox.showwarning("Advertencia", "No hay datos. Primero escanea una BIOS.")
        return

    ruta_guardado = filedialog.asksaveasfilename(
        defaultextension=".nsh", 
        initialfile="startup.nsh", 
        title="Guardar Script UEFI",
        filetypes=[("Script UEFI Shell", "*.nsh"), ("Todos", "*.*")]
    )
    if not ruta_guardado: return

    try:
        imprimir("\n" + "="*75 + "\n", "normal")
        imprimir("⚙️ COMPILANDO PAYLOAD DE INYECCIÓN (CLI)...\n", "titulo")

        with open(ruta_guardado, "w", encoding="utf-8") as f:
            f.write("echo -off\n")
            f.write("echo =========================================\n")
            f.write("echo   INICIANDO INYECCION DE HARDWARE (MOD)  \n")
            f.write("echo =========================================\n\n")

            for var in variables_globales:
                nombre = var["nombre"]
                offset = var["offset"]

                valor = "0xXX" 
                nombre_low = nombre.lower()
                icono = "📌"
                
                if "c state" in nombre_low or "c-state" in nombre_low or "rc6" in nombre_low or "prochot" in nombre_low:
                    valor, icono = "0x00", "⚡"
                elif "eist" in nombre_low or "speedstep" in nombre_low:
                    valor, icono = "0x01", "⚡"
                elif "power limit" in nombre_low or "tdp" in nombre_low:
                    valor, icono = "0x0F", "🔋"
                    if "enable" in nombre_low: valor = "0x01"
                elif "dvmt pre-allocated" in nombre_low:
                    valor, icono = "0x10", "🎮"
                elif "dvmt total" in nombre_low:
                    valor, icono = "0x03", "🎮"

                f.write(f"# ---> VARIABLE: {nombre}\n")
                f.write(f"# {var['recomendacion']}\n")
                f.write(f"setup_var {offset} {valor}\n\n")

                imprimir(f"   {icono} {nombre} -> {valor}\n", "variable")

            f.write("echo =========================================\n")
            f.write("echo  INYECCION FINALIZADA. REINICIA EL EQUIPO\n")
            f.write("echo =========================================\n")
            f.write("exit\n")
            
        imprimir("-" * 75 + "\n", "normal")
        imprimir(f"💾 PAYLOAD CREADO EXITOSAMENTE (100% COMPATIBLE CON UEFI).\n", "exito")
        imprimir(f"Ruta: {ruta_guardado}\n\n", "variable")
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo crear el archivo: {e}")


def generar_guia_ru_efi():
    """Calcula las coordenadas exactas de Fila y Columna para el editor RU.efi"""
    if not variables_globales:
        messagebox.showwarning("Advertencia", "No hay datos. Primero escanea la BIOS.")
        return

    imprimir("\n" + "="*75 + "\n", "normal")
    imprimir("🗺️ MODO NAVEGADOR GPS PARA RU.EFI (INYECCIÓN DIRECTA) 🗺️\n", "titulo")
    imprimir("Instrucciones: En la pantalla de RU.efi, presiona Alt+=, entra a 'Setup' y busca:\n\n", "normal")

    for var in variables_globales:
        nombre = var["nombre"]
        offset_hex = var["offset"] 

        try:
            # Matemáticas Forenses: Convertir Offset a Cuadrícula RU
            offset_int = int(offset_hex, 16)
            fila = format(offset_int & 0xFFF0, '04X')    # Extrae la fila
            columna = format(offset_int & 0x000F, '02X') # Extrae la columna

            valor = "XX" 
            nombre_low = nombre.lower()
            icono = "📌"
            
            if "c state" in nombre_low or "prochot" in nombre_low or "rc6" in nombre_low:
                valor, icono = "00", "⚡"
            elif "eist" in nombre_low or "speedstep" in nombre_low:
                valor, icono = "01", "⚡"
            elif "power limit" in nombre_low or "tdp" in nombre_low:
                valor, icono = "0F", "🔋"
                if "enable" in nombre_low: valor = "01"
            elif "dvmt pre-allocated" in nombre_low:
                valor, icono = "10", "🎮"
            elif "dvmt total" in nombre_low:
                valor, icono = "03", "🎮"

            imprimir(f"{icono} {nombre}:\n", "variable")
            imprimir(f"   ➤ Baja a la Fila: {fila} | Columna: {columna} | Escribe: {valor}\n\n", "exito")

        except Exception:
            pass

    imprimir("="*75 + "\n", "normal")
    imprimir("⚠️ Al terminar: Presiona Ctrl+W para grabar en el chip, apaga de golpe y desconecta la PC 10 seg.\n", "alerta")


# ==========================================
# CONFIGURACIÓN DE LA VENTANA GRÁFICA (GUI)
# ==========================================
ventana = tk.Tk()
ventana.title("BIOS Mod Suite - Analizador & Inyector UEFI")
ventana.geometry("1000x700")
ventana.configure(bg="#1e1e1e")

# Marco superior para acomodar los 3 botones en línea
marco_botones = tk.Frame(ventana, bg="#1e1e1e", pady=15)
marco_botones.pack(fill=tk.X, padx=10)

# BOTÓN 1: Escanear
btn_auto = tk.Button(
    marco_botones, 
    text="🔍 1. Escanear BIOS", 
    command=iniciar_pipeline_automatizado,
    font=("Segoe UI", 11, "bold"),
    bg="#007acc", fg="white",
    relief=tk.FLAT, padx=10, pady=5, cursor="hand2"
)
btn_auto.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

# BOTÓN 2: Exportar Payload
btn_exportar = tk.Button(
    marco_botones, 
    text="💾 2. Payload Shell", 
    command=generar_payload_usb,
    font=("Segoe UI", 11, "bold"),
    bg="#d7ba7d", fg="black",
    relief=tk.FLAT, padx=10, pady=5, cursor="hand2"
)
btn_exportar.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

# BOTÓN 3: Guía Manual RU.efi
btn_ru = tk.Button(
    marco_botones, 
    text="🗺️ 3. Navegador RU.efi", 
    command=generar_guia_ru_efi,
    font=("Segoe UI", 11, "bold"),
    bg="#800080", fg="white",
    relief=tk.FLAT, padx=10, pady=5, cursor="hand2"
)
btn_ru.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

txt_consola = scrolledtext.ScrolledText(ventana, wrap=tk.WORD, bg="#252526", fg="#d4d4d4", font=("Consolas", 10), padx=10, pady=10)
txt_consola.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

txt_consola.tag_config("titulo", foreground="#569cd6", font=("Consolas", 11, "bold"))
txt_consola.tag_config("alerta", foreground="#ce9178", font=("Consolas", 10, "bold"))
txt_consola.tag_config("exito", foreground="#4ec9b0", font=("Consolas", 11, "bold"))
txt_consola.tag_config("variable", foreground="#dcdcaa", font=("Consolas", 10, "bold"))
txt_consola.tag_config("offset", foreground="#f44747", font=("Consolas", 10, "bold"))
txt_consola.tag_config("accion", foreground="#9cdcfe")
txt_consola.tag_config("normal", foreground="#d4d4d4")

imprimir("=== SUITE DE INGENIERÍA INVERSA INICIALIZADA ===\n", "titulo")
imprimir("• Carga la BIOS de tu placa usando el Botón 1.\n", "normal")
imprimir("• Si la placa NO tiene protección: Usa el Botón 2 para crear el USB Auto-Inyectable (.nsh).\n", "normal")
imprimir("• Si la placa tiene BIOS Lock (Ej: J3355): Usa el Botón 3 para ver las coordenadas y editarlas en RU.efi.\n\n", "normal")

ventana.mainloop()