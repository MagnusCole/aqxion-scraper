import requests
import logging
import datetime as dt
from typing import Optional, List
from config import KEYWORDS

# Configuración de logging
log = logging.getLogger("alerts")

class AlertSystem:
    """Sistema de alertas para leads potenciales"""

    def __init__(self, telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{telegram_token}" if telegram_token else None

    def send_telegram_message(self, message: str) -> bool:
        """Enviar mensaje por Telegram"""
        if not self.base_url or not self.telegram_chat_id:
            log.warning("Telegram no configurado - mensaje no enviado")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            log.info(f"✅ Alerta Telegram enviada: {message[:50]}...")
            return True

        except Exception as e:
            log.error(f"❌ Error enviando alerta Telegram: {e}")
            return False

    def send_whatsapp_message(self, message: str, phone_number: Optional[str] = None) -> bool:
        """Enviar mensaje por WhatsApp (requiere configuración adicional)"""
        # Placeholder para WhatsApp - requeriría API de WhatsApp Business
        log.info(f"WhatsApp alert (not implemented): {message[:50]}...")
        return False

    def alert_high_value_lead(self, title: str, body: str, url: str, keyword: str, tag: str, score: int):
        """Enviar alerta para lead de alto valor"""
        if tag not in ['dolor', 'busqueda']:
            return

        # Solo alertar si es alta calidad
        if score < 80 and tag == 'dolor':
            return

        emoji = "💰" if tag == 'dolor' else "🔍"
        intent_type = "DOLOR" if tag == 'dolor' else "BÚSQUEDA PROVEEDOR"

        message = f"""{emoji} <b>NUEVO LEAD DE ALTO VALOR</b> {emoji}

🏷️ <b>Tipo:</b> {intent_type}
🔑 <b>Keyword:</b> {keyword.upper()}
📊 <b>Score:</b> {score}/150

📝 <b>Título:</b> {title[:100]}{'...' if len(title) > 100 else ''}

💡 <b>Snippet:</b> {body[:150] if body else 'Sin contenido adicional'}{'...' if body and len(body) > 150 else ''}

🔗 <b>URL:</b> {url}

⚡ <b>ACCIÓN RECOMENDADA:</b> Contactar inmediatamente - lead caliente!"""

        # Enviar por Telegram
        self.send_telegram_message(message)

        # Log para seguimiento
        log.warning(f"🚨 HIGH VALUE LEAD ALERT: {intent_type} | {keyword} | Score: {score}")

    def alert_daily_summary(self, actionable_dolores: int, provider_searches: int, total_leads: int, top_keywords: Optional[List] = None):
        """Enviar resumen diario de actividad"""
        if not self.base_url or not self.telegram_chat_id:
            return

        message = f"""📊 <b>RESUMEN DIARIO - AQXION SCRAPER</b> 📊

� <b>Fecha:</b> {dt.date.today().strftime('%Y-%m-%d')}

🔥 <b>Dolores Accionables:</b> {actionable_dolores}
🔍 <b>Búsquedas Proveedor:</b> {provider_searches}
📈 <b>Total Leads:</b> {total_leads}

💰 <b>Valor Potencial:</b> ${total_leads * 150:,} - ${total_leads * 500:,} (estimado)"""

        if top_keywords:
            message += "\n\n🏆 <b>Top Keywords del Día:</b>\n"
            for i, (keyword, count) in enumerate(top_keywords[:5], 1):
                message += f"{i}. {keyword} ({count} posts)\n"

        message += "\n\n⚡ <b>Próximos Pasos:</b>\n"
        message += "• Contactar leads de alta calidad\n"
        message += "• Crear contenido basado en dolores\n"
        message += "• Actualizar estrategias de marketing"

        self.send_telegram_message(message)

    def alert_system_status(self, status: str, details: str = ""):
        """Enviar alerta de estado del sistema"""
        if not self.base_url or not self.telegram_chat_id:
            return

        emoji_map = {
            "started": "🚀",
            "completed": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }

        emoji = emoji_map.get(status.lower(), "📢")
        message = f"""{emoji} <b>SISTEMA AQXION</b> {emoji}

<b>Estado:</b> {status.upper()}
<b>Detalles:</b> {details}
<b>Hora:</b> {dt.datetime.now().strftime('%H:%M:%S')}"""

        self.send_telegram_message(message)

# Instancia global del sistema de alertas
alert_system = AlertSystem()

def configure_alerts(telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
    """Configurar el sistema de alertas"""
    global alert_system
    alert_system = AlertSystem(telegram_token, telegram_chat_id)

    if telegram_token and telegram_chat_id:
        log.info("✅ Sistema de alertas configurado con Telegram")
        # Enviar alerta de configuración exitosa
        alert_system.alert_system_status("configurado", "Sistema de alertas operativo")
    else:
        log.warning("⚠️ Sistema de alertas no configurado - usar variables de entorno TELEGRAM_TOKEN y TELEGRAM_CHAT_ID")

def auto_configure_alerts():
    """Configuración automática desde variables de entorno"""
    from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    configure_alerts(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

# Funciones de conveniencia
def alert_lead(title: str, body: str, url: str, keyword: str, tag: str, score: int):
    """Función de conveniencia para alertar leads"""
    alert_system.alert_high_value_lead(title, body, url, keyword, tag, score)

def alert_daily_summary(actionable_dolores: int, provider_searches: int, total_leads: int, top_keywords: Optional[List] = None):
    """Función de conveniencia para resumen diario"""
    alert_system.alert_daily_summary(actionable_dolores, provider_searches, total_leads, top_keywords)

def alert_system_status(status: str, details: str = ""):
    """Función de conveniencia para alertas de sistema"""
    alert_system.alert_system_status(status, details)
