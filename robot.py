import time
import re
from datetime import datetime, timedelta
from playwright.sync_api import Playwright, sync_playwright, expect

def solicitar_datos_configuracion():
    print("=" * 65)
    print(" 🛠️  CONFIGURACIÓN CON AVANCE AUTOMÁTICO DE FECHAS Y PAUSA DE REVISIÓN ")
    print("=" * 65)
    
    # 1. Capturar códigos de estudiantes
    print("\n1. Pega los códigos de los estudiantes (separados por espacios, comas o líneas):")
    entrada_codigos = input("> ")
    codigos = re.findall(r'\d+', entrada_codigos)
    while not codigos:
        print("❌ No se detectaron códigos numéricos válidos. Intenta de nuevo:")
        entrada_codigos = input("> ")
        codigos = re.findall(r'\d+', entrada_codigos)

    total_estudiantes = len(codigos)
    print(f"📌 Total de estudiantes detectados: {total_estudiantes}")

    # 2. Capturar Fecha de Inicio (Debe ser obligatoriamente Lunes)
    while True:
        print("\n2. Ingresa la FECHA DE INICIO del primer Lunes (Formato: DD/MM/AAAA, Ej: 28/09/2026):")
        fecha_input = input("> ").strip()
        
        try:
            dt_inicio = datetime.strptime(fecha_input, "%d/%m/%Y")
            
            # Validar que sea Lunes (weekday() == 0)
            if dt_inicio.weekday() != 0:
                print("❌ [BLOQUEO] La fecha de inicio debe ser obligatoriamente un Lunes. Inténtalo de nuevo.")
                continue
                
            # Validar que no sea una fecha futura a hoy
            hoy = datetime.now()
            if dt_inicio > hoy:
                print("⚠️ [ADVERTENCIA] La fecha de inicio es posterior al día de hoy. ¿Estás seguro? (S/N)")
                if input("> ").strip().lower() != 's':
                    continue
                    
            break
        except ValueError:
            print("❌ Formato de fecha inválido. Usa estrictamente el formato DD/MM/AAAA.")

    # 3. Capturar Motivo Principal (Combobox 4)
    print("\n3. Ingresa el código/opción numérica del MOTIVO (Ej: 10178):")
    motivo_opcion = input("> ").strip()

    # 4. Capturar Submotivo (Combobox 5)
    print("\n4. Ingresa el código/opción numérica del SUBMOTIVO (Ej: 10184):")
    submotivo_opcion = input("> ").strip()

    # 5. Capturar Motivo de Consulta (Texto Libre)
    print("\n5. Escribe el texto para el MOTIVO DE CONSULTA O REMISIÓN:")
    motivo_texto = input("> ").strip()
    while not motivo_texto:
        print("❌ El campo no puede estar vacío:")
        motivo_texto = input("> ").strip()

    print("\n" + "=" * 65)
    print(f"✅ ¡CONFIGURACIÓN EXITOSA! Se asignarán {total_estudiantes} estudiantes a partir del Lunes {dt_inicio.strftime('%d/%m/%Y')}")
    print("=" * 65 + "\n")
    
    return codigos, dt_inicio, motivo_opcion, submotivo_opcion, motivo_texto


def seleccionar_fecha(page, input_fecha, fecha_objetivo):
    input_fecha.click()
    time.sleep(0.4)

    meses = {
        "ene": 1, "jan": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "ago": 8, "aug": 8,
        "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dic": 12, "dec": 12,
    }
    mes_actual = page.locator('[data-test="month-toggle-overlay-0"]').first
    anio_actual = page.locator('[data-test="year-toggle-overlay-0"]').first
    boton_anterior = page.locator('[data-dp-element="action-prev"]').first
    boton_siguiente = page.locator('[data-dp-element="action-next"]').first

    for _ in range(24):
        mes_texto = mes_actual.text_content().strip().lower().replace(".", "")
        anio_texto = anio_actual.text_content().strip()
        mes_numero = meses.get(mes_texto[:4], meses.get(mes_texto[:3]))
        if mes_numero is None or not anio_texto.isdigit():
            raise RuntimeError(f"No se pudo leer el mes/año visible: {mes_texto} {anio_texto}")

        diferencia = (fecha_objetivo.year - int(anio_texto)) * 12 + fecha_objetivo.month - mes_numero
        if diferencia == 0:
            break
        (boton_anterior if diferencia < 0 else boton_siguiente).click()
        time.sleep(0.15)
    else:
        raise RuntimeError(f"No se pudo navegar hasta {fecha_objetivo.strftime('%m/%Y')}")

    id_fecha = fecha_objetivo.strftime("%Y-%m-%d")
    celda_fecha = page.locator(f'[id="{id_fecha}"]')
    celda_fecha.wait_for(state="visible", timeout=2000)
    if celda_fecha.get_attribute("aria-disabled") == "true":
        raise RuntimeError(f"La fecha {fecha_objetivo.strftime('%d/%m/%Y')} está deshabilitada")
    celda_fecha.click()
    time.sleep(0.5)


def run(playwright: Playwright) -> None:
    lista_codigos, fecha_base_lunes, cod_motivo, cod_submotivo, texto_motivo = solicitar_datos_configuracion()

    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    print("[Iniciando] Abriendo la plataforma Adviser...")
    page.goto("https://adviser.ucatolica.edu.co/Adviser/permanencia/login.php?error=2")
    
    # Login automático
    page.locator("#usuario").fill("aflopez38")
    page.locator("input[name=\"contra\"]").fill("AFLRaflr2908??")
    page.get_by_role("checkbox").check()
    page.get_by_role("button", name="Iniciar").click()
    page.wait_for_load_state("networkidle")
    
    # Navegación al buscador
    page.get_by_role("link", name="Seguimiento Individual | Buscar Estudiante (Intervenciones)").click()
    
    # Selección de Código de Estudiante en el menú desplegable principal
    print("[Configuración] Seleccionando la opción de Código de Estudiante...")
    menu_desplegable = page.get_by_role("combobox")
    menu_desplegable.click()  
    time.sleep(0.5)
    for _ in range(3):
        page.keyboard.press("ArrowDown")
        time.sleep(0.2)
    page.keyboard.press("Enter")  
    time.sleep(1.5)  
    
    print("\n=========================================================================")
    print("--> ¡LISTO! Búsqueda por CÓDIGO configurada en Adviser.")
    print("=========================================================================\n")
    hoy = datetime.now()

    for idx, codigo in enumerate(lista_codigos, start=0):
        semana_offset = idx // 9
        pos_en_semana = idx % 9
        
        lunes_actual = fecha_base_lunes + timedelta(weeks=semana_offset)
        
        if pos_en_semana < 6:
            fecha_asignada = lunes_actual
            hora_asignada = 11 if pos_en_semana < 3 else 12
        else:
            fecha_asignada = lunes_actual + timedelta(days=1)
            hora_asignada = 11

        if fecha_asignada > hoy:
            print(f"\n❌ [BLOQUEO DE SEGURIDAD] La fecha calculada ({fecha_asignada.strftime('%d/%m/%Y')}) supera la fecha actual del sistema.")
            print(f"⚠️ El estudiante {codigo} y los siguientes no se pueden procesar porque exceden el día de hoy.")
            break

        nombre_dia = "Lunes" if fecha_asignada.weekday() == 0 else "Martes"

        print(f"\n[{idx+1}/{len(lista_codigos)}] Procesando estudiante: {codigo}")
        print(f"📅 Fecha asignada: {nombre_dia} {fecha_asignada.strftime('%d/%m/%Y')} a las {hora_asignada}:00 AM")
        
        try:
            if page.url != "https://adviser.ucatolica.edu.co/Adviser/permanencia/buscarEstudiante_inter.php":
                page.goto("https://adviser.ucatolica.edu.co/Adviser/permanencia/buscarEstudiante_inter.php")
                page.wait_for_load_state("networkidle")

            # Buscar estudiante
            page.locator("#nombre").click()
            page.locator("#nombre").fill(codigo)
            page.get_by_role("button", name="Buscar Estudiante").click()
            
            # Abrir ficha
            page.get_by_role("button", name="Ficha se seguimiento del").wait_for(state="visible", timeout=6000)
            with page.expect_popup() as page1_info:
                page.get_by_role("button", name="Ficha se seguimiento del").click()
            page1 = page1_info.value
            page1.wait_for_load_state("networkidle")
            
            # Formulario de apoyo
            page1.get_by_role("button", name="Insertar Apoyo").click()
            page1.get_by_role("combobox").first.select_option("3")
            page1.get_by_role("combobox").nth(1).select_option("300")
            page1.get_by_role("combobox").nth(2).select_option("309")
            page1.get_by_role("combobox").nth(3).select_option("PRESENCIAL")
            
            # Selectores de Motivo y Submotivo
            page1.get_by_role("combobox").nth(4).select_option(cod_motivo)
            page1.get_by_role("combobox").nth(5).select_option(cod_submotivo)
            
            # --- SELECCIÓN DE FECHA ROBUSTA (CALENDARIO VUE) ---
            print(f"Estableciendo fecha: {fecha_asignada.strftime('%d/%m/%Y')}...")
            input_fecha = page1.locator("[data-test=\"dp-input\"]").first
            seleccionar_fecha(page1, input_fecha, fecha_asignada)
            
            # --- CONFIGURACIÓN DEL RELOJ VUE SEGURA ---
            print(f"Configurando reloj a las {hora_asignada}:00...")
            input_reloj = page1.locator("[data-test=\"dp-input\"]").nth(1)
            input_reloj.click()
            time.sleep(0.4)

            boton_periodo = page1.get_by_role("button", name="Switch AM/PM mode")
            if boton_periodo.is_visible() and boton_periodo.text_content().strip().upper() != "AM":
                boton_periodo.click()
                time.sleep(0.2)
            
            boton_display_hora = page1.locator("[data-test=\"hours-toggle-overlay-btn-0\"]")
            
            # Intentar ajustar con los botones de incremento de manera controlada (máximo 12 clics para evitar bucles)
            for _ in range(12):
                texto_hora_actual = boton_display_hora.text_content().strip()
                if int(texto_hora_actual) == hora_asignada:
                    break
                page1.locator("[data-test=\"hours-time-inc-btn-0\"]").click()
                time.sleep(0.05)

            # Minutos en 00 asegurados. El selector puede abrirse con cualquier minuto.
            boton_display_min = page1.locator("[data-test=\"minutes-toggle-overlay-btn-0\"]")
            for _ in range(60):
                texto_min_actual = boton_display_min.text_content().strip()
                if int(texto_min_actual) == 0:
                    break
                page1.locator("[data-test=\"minutes-time-dec-btn-0\"]").click()
                time.sleep(0.05)

            page1.keyboard.press("Escape")
            time.sleep(0.4)
            
            # Motivo de consulta (Texto libre)
            page1.get_by_role("textbox", name="MOTIVO CONSULTA O REMISIÓN:").click()
            page1.get_by_role("textbox", name="MOTIVO CONSULTA O REMISIÓN:").fill(texto_motivo)
            
            # Estado final ("NC")
            page1.locator("div:nth-child(11) > .value > .styled2-select > .style6 > select").select_option("NC")
            
            # =========================================================================
            # 🛑 PAUSA DE REVISIÓN HUMANA OBLIGATORIA
            # =========================================================================
            print("\n" + "!" * 70)
            print(f"🔍 FORMULARIO LLENADO PARA EL ESTUDIANTE: {codigo}")
            print(f"📅 Fecha asignada: {nombre_dia} {fecha_asignada.strftime('%d/%m/%Y')} a las {hora_asignada}:00 AM")
            print("👉 Revisa la ventana del navegador. Todo está listo para enviar.")
            print("⌨️  Presiona [ENTER] en esta terminal para CONFIRMAR el envío o [Ctrl+C] para cancelar.")
            print("!" * 70 + "\n")
            input()  
            
            # Enviar e insertar apoyo
            print("Enviando intervención... esperando respuesta del sistema.")
            page1.get_by_role("button", name="Insertar Apoyo").click()
            
            time.sleep(5)
            
            # Validar botón OK de confirmación
            try:
                boton_ok = page1.get_by_role("button", name="OK")
                boton_ok.wait_for(state="visible", timeout=5000)
                boton_ok.click()
                time.sleep(1.5)
                page1.close()
                print(f"✅ Estudiante {codigo} completado y enviado con éxito.")
            except Exception:
                print(f"⚠️ No se detectó el botón OK para el estudiante {codigo}. Cierra la pestaña manualmente si es necesario.")
                input("Presiona ENTER en la terminal para continuar...")
                
        except Exception as e:
            print(f"❌ Error crítico procesando el código {codigo}.")
            print(f"Aviso técnico: {e}")
            input("Presiona ENTER en la terminal para pasar al siguiente código...")

    print("\n🎉 ¡Proceso finalizado con éxito!")
    context.close()
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)