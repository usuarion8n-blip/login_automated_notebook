import os
import json
import time
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def automated_playwright_login(email, password, auth_dir, session_file):
    headless_mode = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    with sync_playwright() as p:
        # Usamos launch_persistent_context para guardar los datos en .auth_profile
        context = p.chromium.launch_persistent_context(
            user_data_dir=auth_dir,
            headless=headless_mode, # En Windows False, en Docker True
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox'],
            user_agent=(
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            )
        )
        
        page = context.pages[0] if context.pages else context.new_page()

        try:
            page.goto('https://notebooklm.google.com', wait_until='networkidle', timeout=30000)

            # Si no redirigió a Google, buscar botón de login
            if 'accounts.google.com' not in page.url and 'notebooklm.google.com' not in page.url:
                for selector in [
                    'a:has-text("Sign in")', 'button:has-text("Sign in")',
                    'a:has-text("Get started")', 'button:has-text("Get started")',
                    'a[href*="accounts.google"]',
                ]:
                    try:
                        page.click(selector, timeout=3000)
                        break
                    except PlaywrightTimeout:
                        continue
                
                try:
                    page.wait_for_url('**/*accounts.google.com**', timeout=15000)
                except PlaywrightTimeout:
                    pass

            # Si ya estamos logueados y entró directo a notebooklm
            if 'notebooklm.google.com' in page.url and 'accounts.google.com' not in page.url:
                context.storage_state(path=session_file)
                context.close()
                return True

            # Llenar email
            email_input = page.locator('input[type="email"], #identifierId')
            email_input.first.wait_for(state='visible', timeout=10000)
            email_input.first.click()
            email_input.first.fill(email)

            # Click Siguiente (Email)
            next_btn = page.locator('#identifierNext button, #identifierNext')
            next_btn.first.click()

            # Llenar contraseña (si la pide)
            try:
                password_input = page.locator('input[name="Passwd"]')
                password_input.wait_for(state='visible', timeout=10000)
                password_input.click()
                password_input.fill(password)

                # Click Siguiente (Password)
                next_pw_btn = page.locator('#passwordNext button, #passwordNext')
                next_pw_btn.first.click()
            except PlaywrightTimeout:
                print("No se encontró campo de contraseña, saltando directo a esperar 2FA o redirección...")

            # ESPERAR 2FA Y REDIRECCIÓN A NOTEBOOKLM
            print("Esperando validación 2FA o redirección...")
            success_redirect = False
            for _ in range(120): # 120 segundos máximo
                if 'notebooklm.google.com' in page.url and 'accounts.google.com' not in page.url:
                    success_redirect = True
                    break
                page.wait_for_timeout(1000) # Espera 1 segundo activo

            if not success_redirect:
                raise Exception(f"Timeout de 120s. URL actual: {page.url}")
            
            page.wait_for_timeout(3000) # Dejar que cargue bien

            # Guardar el session.json manualmente!
            context.storage_state(path=session_file)
            print(f"Sesión guardada exitosamente en {session_file}")

            context.close()
            return True

        except Exception as e:
            context.close()
            raise e

@app.route('/login', methods=['POST', 'GET'])
def login():
    try:
        data = request.get_json(silent=True) or {}
        email = data.get('email') or os.getenv('EMAIL')
        password = data.get('password') or os.getenv('PASSWORD')

        if not email or not password:
            return jsonify({'error': 'Email y contraseña no configurados en .env ni enviados en la petición'}), 400

        base_dir = os.path.expanduser('~/.notebooklm')
        auth_dir = os.path.join(base_dir, '.auth_profile')
        session_file = os.path.join(base_dir, 'session.json')

        os.makedirs(base_dir, exist_ok=True)

        # Siempre ejecutamos el flujo de login para refrescar el session.json
        print("Iniciando automatización de login para refrescar sesión...")
        automated_playwright_login(email, password, auth_dir, session_file)

        # Retornar el session.json
        if os.path.exists(session_file):
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            return jsonify({
                'success': True,
                'session': session_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo generar el session.json'
            }), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
